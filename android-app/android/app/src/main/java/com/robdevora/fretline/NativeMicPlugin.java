package com.robdevora.fretline;

import android.Manifest;
import android.content.Context;
import android.media.AudioDeviceInfo;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Build;
import android.os.Process;
import android.util.Base64;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Records from the phone's own (built-in) microphone with no call-style processing and streams the sound to the
 * page as "pcm" events (base64 of little-endian float32 samples, mono).
 *
 * Why: when the web page asks for the microphone, Android's WebView switches Bluetooth headphones into "call" mode
 * and listens through the headset's call microphone, which is far from the guitar and filters out anything that
 * isn't a voice. Recording here keeps the headphones in normal (music) mode and uses the phone's mic.
 */
@CapacitorPlugin(
    name = "NativeMic",
    permissions = { @Permission(strings = { Manifest.permission.RECORD_AUDIO }, alias = "mic") }
)
public class NativeMicPlugin extends Plugin {
    private static final int CHUNK = 480; // samples per event (10 ms at 48 kHz)

    private volatile boolean running = false;
    private volatile boolean pausedByApp = false;
    private Thread thread;
    private AudioRecord rec;
    private int rate = 48000;
    private String wantType = "builtin", wantName = null;
    private boolean commRoute = false; // we switched Bluetooth into headset (call) mode for its mic
    private JSObject info = new JSObject();

    @PluginMethod
    public void start(PluginCall call) {
        if (getPermissionState("mic") != PermissionState.GRANTED) {
            requestPermissionForAlias("mic", call, "micPermission");
            return;
        }
        doStart(call);
    }

    @PermissionCallback
    private void micPermission(PluginCall call) {
        if (getPermissionState("mic") == PermissionState.GRANTED) doStart(call);
        else call.reject("Microphone permission was not given.", "denied");
    }

    private synchronized void doStart(PluginCall call) {
        stopRecording();
        int want = call.getInt("sampleRate", 48000);
        wantType = call.getString("type", "builtin");
        wantName = call.getString("name", null);
        try {
            openRecorder(want);
        } catch (Exception e) {
            call.reject(e.getMessage() != null ? e.getMessage() : "Could not open the microphone.", "open");
            return;
        }
        beginThread();
        call.resolve(info);
    }

    /** The microphones the phone offers: [{type: builtin|bluetooth|wired|usb|other, name, address}] */
    @PluginMethod
    public void listInputs(PluginCall call) {
        AudioManager am = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
        JSArray a = new JSArray();
        for (AudioDeviceInfo d : am.getDevices(AudioManager.GET_DEVICES_INPUTS)) {
            String t = kind(d);
            if (t.equals("other")) continue;
            JSObject o = new JSObject();
            o.put("type", t);
            o.put("name", d.getProductName() != null ? d.getProductName().toString() : "");
            o.put("address", Build.VERSION.SDK_INT >= 28 ? d.getAddress() : "");
            a.put(o);
        }
        JSObject r = new JSObject();
        r.put("inputs", a);
        call.resolve(r);
    }

    private static String kind(AudioDeviceInfo d) {
        int t = d.getType();
        if (t == AudioDeviceInfo.TYPE_BUILTIN_MIC) return "builtin";
        if (t == AudioDeviceInfo.TYPE_BLUETOOTH_SCO || (Build.VERSION.SDK_INT >= 31 && t == AudioDeviceInfo.TYPE_BLE_HEADSET)) return "bluetooth";
        if (t == AudioDeviceInfo.TYPE_WIRED_HEADSET) return "wired";
        if (t == AudioDeviceInfo.TYPE_USB_DEVICE || t == AudioDeviceInfo.TYPE_USB_HEADSET) return "usb";
        return "other";
    }

    @PluginMethod
    public void stop(PluginCall call) {
        pausedByApp = false;
        stopRecording();
        call.resolve();
    }

    @PluginMethod
    public void status(PluginCall call) {
        JSObject r = new JSObject();
        r.put("running", running);
        r.put("info", info);
        call.resolve(r);
    }

    // don't keep the mic on while the app is in the background
    @Override
    protected void handleOnPause() {
        if (running) { pausedByApp = true; stopRecording(); }
    }

    @Override
    protected void handleOnResume() {
        if (pausedByApp) {
            pausedByApp = false;
            try { openRecorder(rate); beginThread(); } catch (Exception ignored) { }
        }
    }

    private void openRecorder(int want) throws Exception {
        AudioManager am = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);

        // the input to use: the chosen kind (and name, if it's still there), else the built-in mic
        AudioDeviceInfo builtin = null, chosen = null;
        for (AudioDeviceInfo d : am.getDevices(AudioManager.GET_DEVICES_INPUTS)) {
            String k = kind(d);
            if (builtin == null && k.equals("builtin")) builtin = d;
            if (k.equals(wantType)) {
                String n = d.getProductName() != null ? d.getProductName().toString() : "";
                if (chosen == null || (wantName != null && wantName.equals(n) && !wantName.equals(chosen.getProductName() != null ? chosen.getProductName().toString() : ""))) chosen = d;
            }
        }
        if (chosen == null) chosen = builtin;
        boolean bt = chosen != null && kind(chosen).equals("bluetooth");

        if (bt) {
            // a Bluetooth headset's mic only works in headset (call) mode
            am.setMode(AudioManager.MODE_IN_COMMUNICATION);
            boolean routed = false;
            if (Build.VERSION.SDK_INT >= 31) {
                for (AudioDeviceInfo d : am.getAvailableCommunicationDevices()) {
                    if (d.getType() == chosen.getType() || d.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_SCO
                        || d.getType() == AudioDeviceInfo.TYPE_BLE_HEADSET) { routed = am.setCommunicationDevice(d); if (routed) break; }
                }
            }
            if (!routed) { am.startBluetoothSco(); am.setBluetoothScoOn(true); }
            commRoute = true;
            try { Thread.sleep(400); } catch (InterruptedException ignored) { } // let the headset switch over
        } else {
            leaveCallMode(am);
        }

        boolean unprocessedOk = Build.VERSION.SDK_INT >= 24
            && "true".equals(am.getProperty(AudioManager.PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED));
        int[] sources = bt
            ? new int[] { MediaRecorder.AudioSource.VOICE_COMMUNICATION, MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC }
            : unprocessedOk
            ? new int[] { MediaRecorder.AudioSource.UNPROCESSED, MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC }
            : new int[] { MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC };
        int[] rates = want == 48000 ? new int[] { 48000, 44100 } : new int[] { want, 48000, 44100 };
        int[] encs = { AudioFormat.ENCODING_PCM_FLOAT, AudioFormat.ENCODING_PCM_16BIT };

        AudioRecord r = null;
        int usedSrc = -1, usedRate = 0, usedEnc = 0;
        outer:
        for (int src : sources) for (int sr : rates) for (int enc : encs) {
            int min = AudioRecord.getMinBufferSize(sr, AudioFormat.CHANNEL_IN_MONO, enc);
            if (min <= 0) continue;
            int bytesPer = enc == AudioFormat.ENCODING_PCM_FLOAT ? 4 : 2;
            int size = Math.max(min, CHUNK * bytesPer * 8);
            try {
                AudioRecord t = new AudioRecord(src, sr, AudioFormat.CHANNEL_IN_MONO, enc, size);
                if (t.getState() == AudioRecord.STATE_INITIALIZED) { r = t; usedSrc = src; usedRate = sr; usedEnc = enc; break outer; }
                t.release();
            } catch (Exception ignored) { }
        }
        if (r == null) throw new Exception("No usable microphone recorder.");
        if (chosen != null) r.setPreferredDevice(chosen);
        r.startRecording();
        if (r.getRecordingState() != AudioRecord.RECORDSTATE_RECORDING) { r.release(); throw new Exception("The microphone is busy."); }

        rec = r;
        rate = usedRate;
        JSObject i = new JSObject();
        i.put("sampleRate", usedRate);
        i.put("source", usedSrc == MediaRecorder.AudioSource.UNPROCESSED ? "unprocessed"
            : usedSrc == MediaRecorder.AudioSource.VOICE_RECOGNITION ? "voice recognition"
            : usedSrc == MediaRecorder.AudioSource.VOICE_COMMUNICATION ? "call mode" : "mic");
        i.put("encoding", usedEnc == AudioFormat.ENCODING_PCM_FLOAT ? "float" : "16-bit");
        AudioDeviceInfo routed = r.getRoutedDevice();
        AudioDeviceInfo shown = routed != null ? routed : chosen;
        i.put("device", shown != null ? describe(shown) : "unknown");
        i.put("builtin", shown != null && shown.getType() == AudioDeviceInfo.TYPE_BUILTIN_MIC);
        i.put("type", shown != null ? kind(shown) : "?");
        info = i;
    }

    private static String describe(AudioDeviceInfo d) {
        String type;
        switch (d.getType()) {
            case AudioDeviceInfo.TYPE_BUILTIN_MIC: type = "built-in mic"; break;
            case AudioDeviceInfo.TYPE_BLUETOOTH_SCO: type = "Bluetooth headset mic"; break;
            case 26 /* TYPE_BLE_HEADSET */: type = "Bluetooth headset mic"; break;
            case AudioDeviceInfo.TYPE_WIRED_HEADSET: type = "wired headset mic"; break;
            case AudioDeviceInfo.TYPE_USB_DEVICE: case AudioDeviceInfo.TYPE_USB_HEADSET: type = "USB mic"; break;
            default: type = "input type " + d.getType();
        }
        CharSequence n = d.getProductName();
        return n != null && n.length() > 0 ? type + " (" + n + ")" : type;
    }

    private void beginThread() {
        final AudioRecord r = rec;
        final boolean isFloat = r.getAudioFormat() == AudioFormat.ENCODING_PCM_FLOAT;
        running = true;
        thread = new Thread(() -> {
            Process.setThreadPriority(Process.THREAD_PRIORITY_URGENT_AUDIO);
            float[] f = new float[CHUNK];
            short[] s = isFloat ? null : new short[CHUNK];
            ByteBuffer bb = ByteBuffer.allocate(CHUNK * 4).order(ByteOrder.LITTLE_ENDIAN);
            while (running) {
                int n;
                if (isFloat) n = r.read(f, 0, CHUNK, AudioRecord.READ_BLOCKING);
                else {
                    n = r.read(s, 0, CHUNK);
                    for (int k = 0; k < n; k++) f[k] = s[k] / 32768f;
                }
                if (n <= 0) { if (n < 0) break; continue; }
                bb.clear();
                for (int k = 0; k < n; k++) bb.putFloat(f[k]);
                JSObject ev = new JSObject();
                ev.put("d", Base64.encodeToString(bb.array(), 0, n * 4, Base64.NO_WRAP));
                notifyListeners("pcm", ev);
            }
        }, "FretlineMic");
        thread.start();
    }

    /** Back to normal (music) mode: no headset call link, no communication route. */
    private void leaveCallMode(AudioManager am) {
        try {
            if (Build.VERSION.SDK_INT >= 31) am.clearCommunicationDevice();
            if (am.isBluetoothScoOn()) { am.stopBluetoothSco(); am.setBluetoothScoOn(false); }
            if (am.getMode() != AudioManager.MODE_NORMAL) am.setMode(AudioManager.MODE_NORMAL);
        } catch (Exception ignored) { }
        commRoute = false;
    }

    private synchronized void stopRecording() {
        running = false;
        Thread t = thread;
        thread = null;
        AudioRecord r = rec;
        rec = null;
        if (r != null) { try { r.stop(); } catch (Exception ignored) { } }
        if (t != null) { try { t.join(500); } catch (InterruptedException ignored) { } }
        if (r != null) r.release();
        if (commRoute) leaveCallMode((AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE));
    }
}
