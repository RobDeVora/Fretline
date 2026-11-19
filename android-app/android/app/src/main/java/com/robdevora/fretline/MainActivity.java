package com.robdevora.fretline;

import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.webkit.WebView;

import androidx.activity.OnBackPressedCallback;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.JSObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

public class MainActivity extends BridgeActivity {
    private static final int MAX_BYTES = 20 * 1024 * 1024;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(IncomingPlugin.class);
        registerPlugin(NativeMicPlugin.class);
        registerPlugin(NativeSeparatorPlugin.class);
        registerPlugin(SongFilesPlugin.class);
        super.onCreate(savedInstanceState);
        hideSystemBars();
        getWindow().getDecorView().post(this::hideSystemBars); // again once the window is attached
        handleIntent(getIntent());
        // Back button / back gesture: let the page close whatever is open (Settings, a song, a dialog...).
        // Only when it reports there's nothing left to close does the app go to the background.
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                WebView wv = getBridge() != null ? getBridge().getWebView() : null;
                if (wv == null) { moveTaskToBack(true); return; }
                wv.evaluateJavascript("(window.fretlineBack && window.fretlineBack()) ? 'yes' : 'no'", v -> {
                    if (!"\"yes\"".equals(v)) moveTaskToBack(true);
                });
            }
        });
    }

    /** Full screen: no status bar or navigation bar. Swiping in from the edge shows them for a moment. */
    private void hideSystemBars() {
        final android.view.View decor = getWindow().getDecorView();
        try {
            WindowInsetsControllerCompat c = WindowCompat.getInsetsController(getWindow(), decor);
            if (c != null) {
                c.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                c.hide(WindowInsetsCompat.Type.systemBars());
            }
        } catch (Exception ignored) { }
        try {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.view.WindowInsetsController pc = getWindow().getInsetsController();
                if (pc != null) {
                    pc.setSystemBarsBehavior(android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                    pc.hide(android.view.WindowInsets.Type.statusBars() | android.view.WindowInsets.Type.navigationBars());
                }
            } else {
                decor.setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | android.view.View.SYSTEM_UI_FLAG_FULLSCREEN | android.view.View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | android.view.View.SYSTEM_UI_FLAG_LAYOUT_STABLE | android.view.View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | android.view.View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
            }
        } catch (Exception ignored) { }
    }

    // put full screen back after a dialog, the keyboard, another app or the notification shade
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemBars();
    }

    @Override
    public void onResume() {
        super.onResume();
        hideSystemBars();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleIntent(intent);
    }

    /** "Open with Fretline" (VIEW) and "Share → Fretline" (SEND): read the file or text and pass it to the page. */
    private void handleIntent(Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        Uri uri = null;
        JSObject item = new JSObject();
        if (Intent.ACTION_VIEW.equals(action)) {
            uri = intent.getData();
        } else if (Intent.ACTION_SEND.equals(action)) {
            uri = intent.getParcelableExtra(Intent.EXTRA_STREAM);
            String text = intent.getStringExtra(Intent.EXTRA_TEXT);
            String subject = intent.getStringExtra(Intent.EXTRA_SUBJECT);
            if (text != null) item.put("text", text);
            if (subject != null) item.put("title", subject);
        } else {
            return;
        }
        if (uri != null) {
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buf = new byte[16384];
                int n, total = 0;
                while (in != null && (n = in.read(buf)) > 0) {
                    total += n;
                    if (total > MAX_BYTES) throw new Exception("That file is too large.");
                    out.write(buf, 0, n);
                }
                item.put("name", fileName(uri));
                item.put("data", Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP));
            } catch (Exception e) {
                item.put("error", e.getMessage() != null ? e.getMessage() : "Could not read the file.");
            }
        }
        // don't handle the same intent again if the activity is recreated (e.g. on rotation)
        setIntent(new Intent(Intent.ACTION_MAIN));
        IncomingPlugin.deliver(item);
    }

    private String fileName(Uri uri) {
        String name = null;
        if ("content".equals(uri.getScheme())) {
            try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                if (c != null && c.moveToFirst()) name = c.getString(0);
            } catch (Exception ignored) { }
        }
        if (name == null) name = uri.getLastPathSegment();
        return name != null ? name : "song";
    }
}
