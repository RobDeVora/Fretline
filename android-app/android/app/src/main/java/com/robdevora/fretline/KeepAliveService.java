package com.robdevora.fretline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;

import androidx.core.app.NotificationCompat;

/**
 * Keeps Fretline alive while the Lab splits a song and the phone is on another app or the screen is off.
 * A foreground service (with its notification) stops Android from pausing or killing the app, and a wake lock keeps
 * the processor running. Started by the Lab when a run begins, stopped when it ends.
 */
public class KeepAliveService extends Service {
    static final String WORK_CHANNEL = "fretline_work";
    static final String DONE_CHANNEL = "fretline_done";
    static final int WORK_ID = 4101;
    static final int DONE_ID = 4102;
    private PowerManager.WakeLock wake;

    static void channels(Context c) {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel(WORK_CHANNEL, "Working on a song", NotificationManager.IMPORTANCE_LOW));
        nm.createNotificationChannel(new NotificationChannel(DONE_CHANNEL, "Song ready", NotificationManager.IMPORTANCE_DEFAULT));
    }

    static PendingIntent openApp(Context c) {
        Intent i = new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        return PendingIntent.getActivity(c, 0, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    static Notification working(Context c, String text) {
        return new NotificationCompat.Builder(c, WORK_CHANNEL)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("Fretline is working on your song")
            .setContentText(text)
            .setOngoing(true).setOnlyAlertOnce(true).setSilent(true)
            .setContentIntent(openApp(c)).build();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        channels(this);
        String text = intent != null && intent.getStringExtra("text") != null ? intent.getStringExtra("text") : "Starting…";
        Notification n = working(this, text);
        if (Build.VERSION.SDK_INT >= 29) startForeground(WORK_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        else startForeground(WORK_ID, n);
        if (wake == null) {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "fretline:lab");
            wake.acquire(3 * 60 * 60 * 1000L); // never longer than 3 hours
        }
        return START_NOT_STICKY;
    }

    @Override
    public void onDestroy() {
        if (wake != null && wake.isHeld()) wake.release();
        wake = null;
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
