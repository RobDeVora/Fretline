package com.robdevora.fretline;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Hands songs that were opened with, or shared to, Fretline over to the web app. */
@CapacitorPlugin(name = "Incoming")
public class IncomingPlugin extends Plugin {
    private static JSObject pending;
    private static IncomingPlugin instance;

    @Override
    public void load() {
        instance = this;
    }

    @PluginMethod
    public void getPending(PluginCall call) {
        JSObject r = new JSObject();
        synchronized (IncomingPlugin.class) {
            if (pending != null) { r.put("item", pending); pending = null; }
        }
        call.resolve(r);
    }

    static void deliver(JSObject item) {
        IncomingPlugin p = instance;
        if (p != null && p.hasListeners("incoming")) {
            p.notifyListeners("incoming", item);
        } else {
            synchronized (IncomingPlugin.class) { pending = item; }
        }
    }
}
