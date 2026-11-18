package com.robdevora.fretline;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Collections;
import java.util.Iterator;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

/**
 * Splits a recording into stems with Demucs (htdemucs_6s, ONNX) using ONNX Runtime for Android on several cores.
 *
 * The page (lab/stems.html) does the audio decoding, normalisation, chunking and blending; this plugin only:
 *  - downloads the model once into the app's private files (survives "Clear cache", resumes after a dropped
 *    connection, never keeps a file smaller than expected),
 *  - loads it with N threads,
 *  - runs one 7.8 s chunk at a time: input "mix" [1,2,n] float32 → returns the guitar stem and the sum of the other
 *    five stems (the band without the guitar), each as base64 little-endian float32, channel 0 then channel 1.
 * Work runs on its own thread so the app stays responsive; progress arrives as "progress" events.
 */
@CapacitorPlugin(name = "NativeSeparator")
public class NativeSeparatorPlugin extends Plugin {
    private static final int GUITAR = 4; // stem order: drums, bass, other, vocals, guitar, piano

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private OrtEnvironment env;
    private OrtSession session;
    private String inName;
    private int threads = 0;

    private File modelFile(String name) {
        File dir = new File(getContext().getFilesDir(), "models");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, name);
    }

    /** {available, cores, modelBytes, loaded, threads} */
    @PluginMethod
    public void status(PluginCall call) {
        JSObject r = new JSObject();
        r.put("available", true);
        r.put("cores", Runtime.getRuntime().availableProcessors());
        String name = call.getString("name", "htdemucs_6s.onnx");
        File f = modelFile(name);
        r.put("modelBytes", f.exists() ? f.length() : 0);
        r.put("loaded", session != null);
        r.put("threads", threads);
        call.resolve(r);
    }

    /** prepareModel({url, name, expectBytes}) → {path, bytes, downloaded} */
    @PluginMethod
    public void prepareModel(PluginCall call) {
        final String url = call.getString("url");
        final String name = call.getString("name", "htdemucs_6s.onnx");
        final long expect = (long) (double) call.getDouble("expectBytes", 0.0);
        if (url == null) { call.reject("no model address"); return; }
        worker.execute(() -> {
            File done = modelFile(name), part = modelFile(name + ".part");
            try {
                if (done.exists() && done.length() >= expect * 0.97) {
                    JSObject r = new JSObject(); r.put("path", done.getAbsolutePath()); r.put("bytes", done.length()); r.put("downloaded", false);
                    call.resolve(r); return;
                }
                if (done.exists()) done.delete();
                Exception last = null;
                for (int attempt = 1; attempt <= 6; attempt++) {
                    try { download(url, part, expect); last = null; break; }
                    catch (Exception e) { last = e; progress("download", part.length(), expect, "connection dropped, try " + attempt); Thread.sleep(1500L * attempt); }
                }
                if (last != null) throw last;
                if (expect > 0 && part.length() < expect * 0.97) throw new Exception("model download incomplete: " + part.length() + " bytes");
                if (!part.renameTo(done)) throw new Exception("could not keep the model file");
                JSObject r = new JSObject(); r.put("path", done.getAbsolutePath()); r.put("bytes", done.length()); r.put("downloaded", true);
                call.resolve(r);
            } catch (Exception e) {
                call.reject(e.getMessage() != null ? e.getMessage() : e.toString());
            }
        });
    }

    /** Downloads into `part`, continuing from its current length (HTTP Range) when the server allows it. */
    private void download(String address, File part, long expect) throws Exception {
        long have = part.exists() ? part.length() : 0;
        HttpURLConnection c = (HttpURLConnection) new URL(address).openConnection();
        c.setInstanceFollowRedirects(true);
        c.setConnectTimeout(20000);
        c.setReadTimeout(30000);
        if (have > 0) c.setRequestProperty("Range", "bytes=" + have + "-");
        int code = c.getResponseCode();
        // a redirect to another host isn't always followed automatically: follow up to 5 by hand
        for (int i = 0; i < 5 && (code == 301 || code == 302 || code == 303 || code == 307 || code == 308); i++) {
            String loc = c.getHeaderField("Location");
            c.disconnect();
            c = (HttpURLConnection) new URL(new URL(address), loc).openConnection();
            c.setConnectTimeout(20000);
            c.setReadTimeout(30000);
            if (have > 0) c.setRequestProperty("Range", "bytes=" + have + "-");
            code = c.getResponseCode();
        }
        boolean append = have > 0 && code == 206;
        if (code != 200 && code != 206) throw new Exception("HTTP " + code);
        if (!append) have = 0;
        long len = -1;
        try { len = Long.parseLong(c.getHeaderField("Content-Length")); } catch (Exception ignored) { }
        long total = expect > 0 ? expect : have + Math.max(0, len);
        try (InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(part, append)) {
            byte[] buf = new byte[1 << 16];
            long got = have, lastSent = 0;
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
                got += n;
                if (got - lastSent > (2 << 20)) { lastSent = got; progress("download", got, total, null); }
            }
        } finally {
            c.disconnect();
        }
    }

    private void progress(String phase, long got, long total, String note) {
        JSObject e = new JSObject();
        e.put("phase", phase);
        e.put("got", got);
        e.put("total", total);
        if (note != null) e.put("note", note);
        notifyListeners("progress", e);
    }

    /** load({path, threads}) → {ms, threads, input, outputs} */
    @PluginMethod
    public void load(PluginCall call) {
        final String path = call.getString("path");
        final int want = call.getInt("threads", 0);
        worker.execute(() -> {
            try {
                long t0 = System.currentTimeMillis();
                closeSession();
                if (env == null) env = OrtEnvironment.getEnvironment();
                int cores = Runtime.getRuntime().availableProcessors();
                threads = want > 0 ? want : Math.max(1, Math.min(6, cores - 1));
                OrtSession.SessionOptions so = new OrtSession.SessionOptions();
                so.setIntraOpNumThreads(threads);
                so.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.EXTENDED_OPT);
                session = env.createSession(path, so);
                Iterator<String> it = session.getInputNames().iterator();
                inName = it.hasNext() ? it.next() : "mix";
                JSObject r = new JSObject();
                r.put("ms", System.currentTimeMillis() - t0);
                r.put("threads", threads);
                r.put("input", inName);
                StringBuilder outs = new StringBuilder();
                for (String o : session.getOutputNames()) { if (outs.length() > 0) outs.append(','); outs.append(o); }
                r.put("outputs", outs.toString());
                call.resolve(r);
            } catch (Throwable e) {
                closeSession();
                call.reject("could not load the model: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            }
        });
    }

    /** run({mix: base64 float32 [2*n] (channel 0 then 1), n}) → {guitar, band (both base64 [2*n]), ms} */
    @PluginMethod
    public void run(PluginCall call) {
        final String mixB64 = call.getString("mix");
        final int n = call.getInt("n", 0);
        if (session == null) { call.reject("the model isn't loaded"); return; }
        if (mixB64 == null || n <= 0) { call.reject("no audio"); return; }
        worker.execute(() -> {
            OnnxTensor input = null;
            try {
                long t0 = System.currentTimeMillis();
                byte[] raw = Base64.decode(mixB64, Base64.DEFAULT);
                FloatBuffer in = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer();
                float[] mix = new float[2 * n];
                in.get(mix, 0, Math.min(mix.length, in.remaining()));
                input = OnnxTensor.createTensor(env, FloatBuffer.wrap(mix), new long[]{1, 2, n});
                float[] guitar = new float[2 * n], band = new float[2 * n];
                try (OrtSession.Result res = session.run(Collections.singletonMap(inName, input))) {
                    OnnxValue v = res.get(0);
                    FloatBuffer out = ((OnnxTensor) v).getFloatBuffer(); // [1, 6, 2, n]
                    float[] all = new float[out.remaining()];
                    out.get(all);
                    int stems = all.length / (2 * n);
                    for (int k = 0; k < stems; k++) {
                        int base = k * 2 * n;
                        if (k == GUITAR) System.arraycopy(all, base, guitar, 0, 2 * n);
                        else for (int i = 0; i < 2 * n; i++) band[i] += all[base + i];
                    }
                }
                JSObject r = new JSObject();
                r.put("guitar", encode(guitar));
                r.put("band", encode(band));
                r.put("ms", System.currentTimeMillis() - t0);
                call.resolve(r);
            } catch (Throwable e) {
                call.reject("separation failed: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            } finally {
                if (input != null) input.close();
            }
        });
    }

    private static String encode(float[] a) {
        ByteBuffer b = ByteBuffer.allocate(a.length * 4).order(ByteOrder.LITTLE_ENDIAN);
        b.asFloatBuffer().put(a);
        return Base64.encodeToString(b.array(), Base64.NO_WRAP);
    }

    @PluginMethod
    public void unload(PluginCall call) {
        worker.execute(() -> { closeSession(); call.resolve(); });
    }

    private void closeSession() {
        if (session != null) {
            try { session.close(); } catch (OrtException ignored) { }
            session = null;
        }
    }

    /* ---- saving a file to the phone's Downloads folder (web download links do nothing inside the app) ----
       saveChunk({name, data: base64, first}) appends to a staging file in the cache; saveFinish({name, mime}) copies it
       into Downloads (MediaStore on Android 10+, the app's own Downloads folder before that) → {path} */
    @PluginMethod
    public void saveChunk(PluginCall call) {
        final String name = safeName(call.getString("name", "file.bin"));
        final String data = call.getString("data", "");
        final boolean first = Boolean.TRUE.equals(call.getBoolean("first", false));
        worker.execute(() -> {
            try (FileOutputStream out = new FileOutputStream(new File(getContext().getCacheDir(), "save-" + name), !first)) {
                out.write(Base64.decode(data, Base64.DEFAULT));
                call.resolve();
            } catch (Exception e) { call.reject("could not save: " + e.getMessage()); }
        });
    }

    @PluginMethod
    public void saveFinish(PluginCall call) {
        final String name = safeName(call.getString("name", "file.bin"));
        final String mime = call.getString("mime", "application/octet-stream");
        worker.execute(() -> {
            File tmp = new File(getContext().getCacheDir(), "save-" + name);
            try {
                String where;
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentResolver cr = getContext().getContentResolver();
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Fretline");
                    Uri uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    if (uri == null) throw new Exception("Downloads isn't available");
                    try (InputStream in = new FileInputStream(tmp); OutputStream out = cr.openOutputStream(uri)) { copy(in, out); }
                    where = "Downloads/Fretline/" + name;
                } else {
                    File dir = new File(getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "");
                    if (!dir.exists()) dir.mkdirs();
                    File dst = new File(dir, name);
                    try (InputStream in = new FileInputStream(tmp); OutputStream out = new FileOutputStream(dst)) { copy(in, out); }
                    where = dst.getAbsolutePath();
                }
                JSObject r = new JSObject(); r.put("path", where); call.resolve(r);
            } catch (Exception e) {
                call.reject("could not save: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            } finally { tmp.delete(); }
        });
    }

    private static void copy(InputStream in, OutputStream out) throws Exception {
        byte[] b = new byte[1 << 16]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
    }

    private static String safeName(String n) {
        String s = n.replaceAll("[^A-Za-z0-9._ ()-]", "_");
        return s.isEmpty() ? "file.bin" : s;
    }

    @Override
    protected void handleOnDestroy() {
        closeSession();
        worker.shutdown();
    }
}
