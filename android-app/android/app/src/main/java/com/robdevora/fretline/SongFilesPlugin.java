package com.robdevora.fretline;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import androidx.core.content.FileProvider;
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
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * One folder per song on the phone: Downloads/Fretline/Songs/<song name>/ holding the song file and the tab / chord
 * files it was made from. The app writes into the folder when a song is saved or changed and removes the whole folder
 * when the song is deleted, so nothing is left behind taking up space.
 * Android 10+: MediaStore (no permission needed, the app can always change files it made itself).
 * Before that: the app's own Downloads folder.
 */
@CapacitorPlugin(name = "SongFiles")
public class SongFilesPlugin extends Plugin {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private static final String ROOT = "Fretline/Songs/";

    /** folder and file names: keep letters of any language, drop what a file system can't hold */
    static String seg(String s, String fallback) {
        if (s == null) s = "";
        s = s.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]", "_").trim();
        while (s.startsWith(".")) s = s.substring(1);
        if (s.length() > 80) s = s.substring(0, 80).trim();
        return s.isEmpty() ? fallback : s;
    }

    private String relPath(String dir) { return Environment.DIRECTORY_DOWNLOADS + "/" + ROOT + seg(dir, "Song") + "/"; }

    private File legacyDir(String dir) {
        File base = getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        return new File(new File(base, ROOT), seg(dir, "Song"));
    }

    /** shareFile({name, b64, mime}) → {}. v1.143: same as shareText but for a binary file (the lesson audio .wav), sent as base64. */
    @PluginMethod
    public void shareFile(PluginCall call) {
        final String name = seg(call.getString("name"), "fretline-audio.wav");
        final String b64 = call.getString("b64");
        final String mime = call.getString("mime") != null ? call.getString("mime") : "application/octet-stream";
        if (b64 == null) { call.reject("no data"); return; }
        worker.execute(() -> {
            try {
                File dir = new File(getContext().getCacheDir(), "shared");
                if (!dir.exists()) dir.mkdirs();
                File f = new File(dir, name);
                try (OutputStream os = new FileOutputStream(f)) { os.write(android.util.Base64.decode(b64, android.util.Base64.DEFAULT)); }
                Uri uri = FileProvider.getUriForFile(getContext(), getContext().getPackageName() + ".fileprovider", f);
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType(mime);
                send.putExtra(Intent.EXTRA_STREAM, uri);
                send.putExtra(Intent.EXTRA_SUBJECT, "Fretline lesson audio");
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                Intent chooser = Intent.createChooser(send, "Share audio");
                chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(chooser);
                call.resolve();
            } catch (Exception e) {
                call.reject("share failed: " + e.getMessage());
            }
        });
    }

    /** shareText({name, text}) → {}. v1.135: writes the text to a file in the app's cache and opens Android's share sheet with it
     *  as a .txt attachment (Messages, Gmail, Drive...). Used for the detection report. */
    @PluginMethod
    public void shareText(PluginCall call) {
        final String name = seg(call.getString("name"), "fretline-report.txt");
        final String text = call.getString("text");
        if (text == null) { call.reject("no text"); return; }
        worker.execute(() -> {
            try {
                File dir = new File(getContext().getCacheDir(), "shared");
                if (!dir.exists()) dir.mkdirs();
                File f = new File(dir, name);
                try (OutputStream os = new FileOutputStream(f)) { os.write(text.getBytes("UTF-8")); }
                Uri uri = FileProvider.getUriForFile(getContext(), getContext().getPackageName() + ".fileprovider", f);
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType("text/plain");
                send.putExtra(Intent.EXTRA_STREAM, uri);
                send.putExtra(Intent.EXTRA_SUBJECT, "Fretline detection report");
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                Intent chooser = Intent.createChooser(send, "Share report");
                chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(chooser);
                call.resolve();
            } catch (Exception e) {
                call.reject("share failed: " + e.getMessage());
            }
        });
    }

    /** write({dir, name, text | data (base64), mime}) → {path}. An existing file of that name is replaced. */
    @PluginMethod
    public void write(PluginCall call) {
        final String dir = seg(call.getString("dir"), "Song");
        final String name = seg(call.getString("name"), "file.bin");
        final String mime = call.getString("mime", "application/octet-stream");
        final String text = call.getString("text");
        final String data = call.getString("data");
        worker.execute(() -> {
            try {
                byte[] bytes = text != null ? text.getBytes("UTF-8") : Base64.decode(data == null ? "" : data, Base64.DEFAULT);
                String where;
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentResolver cr = getContext().getContentResolver();
                    removeFiles(cr, dir, name);
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, relPath(dir));
                    Uri uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    if (uri == null) throw new Exception("Downloads isn't available");
                    try (OutputStream out = cr.openOutputStream(uri)) { out.write(bytes); }
                    where = "Downloads/" + ROOT + dir + "/" + name;
                } else {
                    File d = legacyDir(dir);
                    if (!d.exists()) d.mkdirs();
                    File f = new File(d, name);
                    try (FileOutputStream out = new FileOutputStream(f)) { out.write(bytes); }
                    where = f.getAbsolutePath();
                }
                JSObject r = new JSObject(); r.put("path", where); call.resolve(r);
            } catch (Exception e) {
                call.reject("could not save: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            }
        });
    }

    /** removeDir({dir}) → {removed}: deletes every file in the song's folder, then the folder itself */
    @PluginMethod
    public void removeDir(PluginCall call) {
        final String dir = seg(call.getString("dir"), "Song");
        worker.execute(() -> {
            try {
                int n = 0;
                if (Build.VERSION.SDK_INT >= 29) {
                    n = removeFiles(getContext().getContentResolver(), dir, null);
                    try { // the empty folder, where the phone lets the app
                        File d = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), ROOT + dir);
                        if (d.isDirectory()) { String[] left = d.list(); if (left == null || left.length == 0) d.delete(); }
                    } catch (Exception ignored) { }
                } else {
                    File d = legacyDir(dir);
                    File[] fs = d.listFiles();
                    if (fs != null) for (File f : fs) if (f.delete()) n++;
                    d.delete();
                }
                JSObject r = new JSObject(); r.put("removed", n); call.resolve(r);
            } catch (Exception e) {
                call.reject("could not remove: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
            }
        });
    }

    /** deletes files this app made in the folder (all, or just `name`); returns how many went */
    private int removeFiles(ContentResolver cr, String dir, String name) {
        String sel = MediaStore.MediaColumns.RELATIVE_PATH + "=?" + (name != null ? " AND " + MediaStore.MediaColumns.DISPLAY_NAME + "=?" : "");
        String[] args = name != null ? new String[]{relPath(dir), name} : new String[]{relPath(dir)};
        try { return cr.delete(MediaStore.Downloads.EXTERNAL_CONTENT_URI, sel, args); }
        catch (Exception e) { return 0; }
    }

    @Override
    protected void handleOnDestroy() { worker.shutdown(); }
}
