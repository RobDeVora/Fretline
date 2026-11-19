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
| `sheet_tab.py` (env `RIFF=`) | v1.83: tab with uneven spacing lined up with the riff: 64/64; half tempo moves nothing; app opens it, ♩ 2× |
| `sheet_chords.py` (env `SHEET=`) | v1.83: chord sheet without lengths vs synthetic strums (`make_chords90.py` builds `/tmp/chordtest`); changes within 72 ms; strum mode; transposed / capo sheets |
| — | `sheet_tab.py` default audio `/tmp/stemtest/riff100_clean.wav` = riff100.wav through `ffmpeg -af "lowpass=f=1800,lowpass=f=1800"` |

| `make_solo90.py` + `sheet_merge.py` | v1.90 a tab (solo) + a chord sheet on one recording (`/tmp/solotest/solo90.wav`): solo window, note times, no chords inside the solo; env `FROMTO='0:09.8,0:15.5'`, `STRUMS=1` | `python3 make_solo90.py && python3 sheet_merge.py` |
| `real_merge.py` / `real_files.py` | v1.90-91 real song (TYSK guitar stem + tab MIDI, and the owner's chords MIDI): a text tab cut from the MIDI (`real_merge.py A B [win] [from to]`) or both files (`real_files.py [auto|tab|chords] [swap]`). Files in /tmp, not in the repo | see the files |

v1.84 MIDI sheets: `MIDI=/tmp/riff.mid python3 sheet_tab.py` and `MIDI=/tmp/chords.mid python3 sheet_chords.py`.
Make the files with `pip install mido`, then: riff.mid = 120 BPM, tracks Bass (prog 33) / Drums (ch 10) / Guitar
(prog 25) with the riff [40,40,52,40,45,45,47,50] as 8ths from beat 8 for 8 bars; chords.mid = 100 BPM, one track,
G C D Em G C one bar each (G=[43,47,50,55,59,67], C=[48,52,55,60,64], D=[50,57,62,66], Em=[40,47,52,55,59,64]).

v1.85 timing check: `RIFF=/tmp/stemtest/riff_even.wav MIDI=/tmp/riff.mid python3 sheet_tab.py` prints "timing vs the
evenly played riff" (median 3 ms, max 10 ms as placed). riff_even.wav: 44.1 kHz stereo, plucks at 1.0 s + k·0.3 s
(100 BPM 8ths, the riff ×8 bars), each pluck = harmonics 1-8 with amplitude h^-1.2, decay e^(-(3+0.9h)t), 2 ms
attack, 1.2 s long. (riff100.wav has a pre-attack 55 ms before on-beat picks: ±27 ms residuals there.)
