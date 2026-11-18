# Detection tests

Offline tests that run real guitar recordings through Fretline's own detection and scoring code
(`detectFrame` → `update` → `matchEvent`) in headless Chrome, using an `OfflineAudioContext` that is
suspended every 1/60 s so the app's per-frame code runs exactly as on a phone.

## Setup

```bash
pip install playwright            # Chrome is at /usr/bin/google-chrome in the cloud workspace
mkdir -p /tmp/samp && cd /tmp/samp && npm pack tonejs-instrument-guitar-acoustic-mp3@1.1.2 && tar xzf *.tgz
export SAMPLES=/tmp/samp/package/   # the acoustic guitar recordings the app's "★ Acoustic guitar" sound uses
```

The scripts route the app's sample downloads (jsdelivr/unpkg) to these local files.

## Scripts

| Script | What it checks | Run |
|---|---|---|
| `sweep_fretboard.py` | One string, frets 0-17, each note after a ringing note on the neighbouring string. Prints hits per fret, early credits, wrong-note pops, misses with the detection report line | `python3 sweep_fretboard.py <repo dir> <string 0-5> <volume 0.5 normal / 0.025 quiet>` |
| `sweep_wrong_notes.py` | Same, but every target is played a semitone flat; nothing should count | `python3 sweep_wrong_notes.py <repo dir> <string> 0.5` |
| `chords_dead_strings.py` | Strummed progression with a dead B, low E ringing on D, dead D in Am, dead G on a repeat C. Prints the ✓/✕/! per string | `python3 chords_dead_strings.py <repo dir>` |
| `song_report_sim.py` | A melody like the user's "Melody in A blues", prints the detection report (set `window.__gap`, `__gain`, `__noise` via an init script) | see the file |
| `test_native_mic.py` | The Android app's native-mic path with a fake `NativeMic` plugin (bursty 10 ms chunks of a 220 Hz tone): analyser gets the sound, pitch reads 220, no gaps; and that a failing app mic falls back to the web mic | `python3 test_native_mic.py <repo dir>` |
| `chord_strings_static.py` | Per-string chord analysis on single snapshots of 9 open/barre chords, each string removed in turn | `python3 chord_strings_static.py <repo dir>` |

Last results (v1.49): sweeps 108/108 at normal and quiet volume, 0/108 wrong notes counted, chord test
no false flags. Two strings at a time is about the limit on a 2-core workspace (~3-4 min per string).

Known test-harness gotcha: `G.pops` keeps only the last 6 pop-ups, so counting pops by length misses some;
use the detection report (`G.diag`) instead.
