# Lab (split a song) tests

The workspace can't reach Hugging Face, so these run the Lab page with a stand-in ONNX model of the same shape
(`mix` [1,2,343980] → [1,6,2,343980], "guitar" = 0.3 × input) served with onnxruntime-web from a local "CDN".

Setup: `npm pack onnxruntime-web@1.31.1` and unpack to `/tmp/ortpkg/package`; build `dummy.onnx` (see the v1.77
section of HANDOFF.md) into `/tmp/ortpkg/package/dist/`; serve the repo on 8769; run `python3 cdnsrv.py` (port 8771).

| Test | What it checks |
|---|---|
| `mt.py <audio>` | cross-origin isolation via the service worker, multi-thread run, exact blending |
| `fakegpu.py <audio>` | a fake WebGPU session that resets on run 2 and returns NaN from run 4: rebuild + processor fallback, exact output |
| `dropsrv.py` | a server that drops the model download at 10 MB; `getModel` must resume to an identical file |
| `e2e.py` (v1.81: 64/64, 0 extras; real-guitar guide checks) | synthetic 100 BPM riff (`riff100.wav`, real guitar samples + clicks): split → Basic Pitch → tempo → song saved; main app builds it and plays the backing in sync. v1.78: 99.5 BPM, 64/64 riff notes on the right beat, 8 extras, sync error ≤ 6 ms |
| `native.py <audio> [fail]` | fake APK NativeSeparator: default "all cores", exact blending, fallback to the web runtime |
