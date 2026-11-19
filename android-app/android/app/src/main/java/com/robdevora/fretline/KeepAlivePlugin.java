package com.robdevora.fretline;

import android.Manifest;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/** start / update / stop the "working on your song" notification and keep-alive service; done() says it finished. */
@CapacitorPlugin(name = "KeepAlive", permissions = {
    @Permission(alias = "notifications", strings = { Manifest.permission.POST_NOTIFICATIONS })
})
public class KeepAlivePlugin extends Plugin {

    @PluginMethod
    public void start(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 33 && getPermissionState("notifications") != PermissionState.GRANTED) {
            requestPermissionForAlias("notifications", call, "afterPermission"); // the service runs either way
            return;
        }
        begin(call);
    }

    @PermissionCallback
    private void afterPermission(PluginCall call) { begin(call); }

    private void begin(PluginCall call) {
        try {
            Context c = getContext();
            Intent i = new Intent(c, KeepAliveService.class).putExtra("text", call.getString("text", "Starting…"));
            ContextCompat.startForegroundService(c, i);
            call.resolve();
        } catch (Exception e) {
            call.reject("could not start: " + (e.getMessage() != null ? e.getMessage() : e.toString()));
        }
    }

    @PluginMethod
    public void update(PluginCall call) {
        try {
            Context c = getContext();
            ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE))
                .notify(KeepAliveService.WORK_ID, KeepAliveService.working(c, call.getString("text", "")));
        } catch (Exception ignored) { }
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        try { getContext().stopService(new Intent(getContext(), KeepAliveService.class)); } catch (Exception ignored) { }
        call.resolve();
    }

    /** stops the service and leaves a "song ready" (or "stopped") notification that opens the app when tapped */
    @PluginMethod
    public void done(PluginCall call) {
        try {
            Context c = getContext();
            c.stopService(new Intent(c, KeepAliveService.class));
            KeepAliveService.channels(c);
            ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).notify(KeepAliveService.DONE_ID,
                new NotificationCompat.Builder(c, KeepAliveService.DONE_CHANNEL)
                    .setSmallIcon(android.R.drawable.stat_notify_sync_noanim)
                    .setContentTitle(call.getString("title", "Fretline"))
                    .setContentText(call.getString("text", ""))
                    .setAutoCancel(true).setContentIntent(KeepAliveService.openApp(c)).build());
        } catch (Exception ignored) { }
        call.resolve();
    }
}
