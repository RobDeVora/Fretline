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
| `test_wrong_wait_grades.py` | v1.52 logic: a suspected wrong note is cancelled by a hit or a new pick within 250 ms, reported otherwise; Perfect/Good/Okay thresholds | `python3 test_wrong_wait_grades.py <repo dir>` |
| `test_mic_options.py` | v1.53 Microphone list with a fake plugin (new app with `listInputs`, old app without); choosing Bluetooth starts the native mic with `type:'bluetooth'`. Serve the repo first: `python3 -m http.server 8766 -d <repo>` | `python3 test_mic_options.py <repo dir>` |
| `test_singing_e2e.py` | v1.55 singing: library tune (Amazing Grace) → guide + words; chord sheet → made-up melody (one note per syllable); each Settings › Singing tick; `twinkle.mid` (lyric events) and `song.musicxml` (lyrics on notes) → melody + words lined up with the guitar part. Copy the two test files into the repo root and serve it on port 8768 first | `python3 test_singing_e2e.py` |
| `test_made_up_melody.py` | Shape of the made-up melody for two sheets: range, repeats, leaps, chord tones on downbeats | `python3 test_made_up_melody.py` (server on 8768) |
| `check_library_tunes.js` | Library tunes (`tunes.json` = what's in `library/index.json`): bar lengths, length vs chords, chord tones on downbeats | `node check_library_tunes.js <repo>/index.html <repo>/library/index.json` (run from this folder) |
| `test_import_no_extension.py` | v1.56: a MIDI file with no extension loads as MIDI (parts listed) instead of as text. Serve the repo on 8769 first | `python3 test_import_no_extension.py <some.mid>` |
| `test_song_parts.py` | v1.57: import a multi-part MIDI with no extension, all parts saved on one timeline, "Which part?" chooser, Lead + rhythm (lead bars + rhythm elsewhere), 🎸 part button. Serve the repo on 8769 first | `python3 test_song_parts.py <multi-part.mid>` |
| `test_combo_strum.py` | v1.58: Lead + rhythm with each strum pattern keeps every lead note and strums only the rhythm bars; screenshots to /tmp. Serve the repo on 8769 first | `python3 test_combo_strum.py <multi-part.mid>` |
| `test_fingering.js` | v1.59 fingering: common chord shapes (C G D A E Am Em Dm F Bm B7 G7 C7, power chords) and single-note lines (pentatonic box, first position, a position shift) | `node test_fingering.js <repo>/index.html` |
| `shot_finger_guide.py` | Screenshots of the finger guide strip, landscape/portrait, fretboard on/off, playing and not (to /tmp/mm/). Serve the repo on 8769 first | `python3 shot_finger_guide.py <multi-part.mid>` |
| `test_listen_nudge.py` | v1.61: the Sound − / + control shows during Listen until ✓ Done, then only when asked for from Settings › Line it up by ear. Serve the repo on 8769 first | `python3 test_listen_nudge.py` |
| `test_v162_settings_route_hand.py` | v1.62: per-output sound delay / headphones with a fake plugin route switch, Settings tabs, hand size while playing at the owner's app screen sizes (screenshots to /tmp/mm). Serve the repo on 8769 first | `python3 test_v162_settings_route_hand.py <multi-part.mid>` |
| `test_one_note_all_song.py` | v1.65/1.66: the owner's A minor pentatonic lesson with one note played throughout. v1.66 results: `PLAY=55` (G3) 1/34, `PLAY=74` (D5) 4/34 (= its 4 D5s), `PLAY=62` (D4) 4/34 (2 real + 2 false); played correctly (no PLAY) 33/34 | `PLAY=55 python3 test_one_note_all_song.py <repo>` |
| `test_strums.py` | v1.74 strums: `CHORDS='["D","A",...]'` is the chart (one strum per step), `PLAYC='"Em"'` (or a list) what's strummed; voicings in `VO` (D A Em G C Am). Owner's pattern at `GAP=0.4167`: correct 100/104; Em/D/A/G throughout → only their own strums (+1); C (not in the song) still passes on Em and A steps | `CHORDS="$(cat song.json)" PLAYC='"Em"' GAP=0.4167 python3 test_strums.py <repo>` |
| `test_window_steal.py` | v1.69: the boogie at its real step gap (`GAP=0.4286`, 70 BPM eighths) with a slow-highway early window (`RING=0.45` s). `SWAP=1` plays fret 4 where the chart says 2 and vice versa (the owner's 1.68 run). v1.68: 11 false hits; v1.69: 5 (all A+E/A+F# and B+F#/B+G# steps: sampled-note overtone leak, see v1.67). Correct playing 95/96, `PLAY2='[40,47]'` 36/96. `MAP='{"40,49":[49,52]}'` plays A4+D2 on the E0+A4 steps only (owner's real 1.68 run): v1.68 all 24 credited, v1.69 none. v1.71: the harness also feeds an 8192-sample analyser (`analyserL`); `LPT=` sets the low-overtone partner threshold (99 = measure only), `LP=` adds a low-pass filter to mimic a phone mic, `SEQ=` (JSON list of steps, each a list of [midi, string]) replaces the boogie, e.g. the A minor arpeggio with `GAP=0.536` (v1.73: 64/64; 1.72: 61), `LATE=` (s) delays the first step after each change (v1.72: 0.10-0.20 → 95-96/96; 1.71: 0.10 → 55). Report lines show `2nd x.xx` | `SWAP=1 GAP=0.4286 RING=0.45 python3 test_window_steal.py <repo>` |
| `test_double_stops.py` | v1.67: two-note steps from "Boogie shuffle in E" (all 96 steps). v1.67: correct 95/96. `PLAY2=[40,47]` (E2+B2 throughout, the owner's run): 36/96 = all 28 E+B steps + 8 B2+G#3 steps (the low E's 5th overtone, 412 Hz, passes for G#3's 2nd, 415 Hz). `PLAY2=[45,52]`: 8/64 exact. `PLAY2=[40,49]`: 30/64 (24 real + 6 A+E steps still pass: E3 = E2's octave and A2's 5th sits on C#3's 4th) | `PLAY2='[40,47]' python3 test_double_stops.py <repo>` |
| `chord_strings_static.py` | Per-string chord analysis on single snapshots of 9 open/barre chords, each string removed in turn | `python3 chord_strings_static.py <repo dir>` |

Last results (v1.49): sweeps 108/108 at normal and quiet volume, 0/108 wrong notes counted, chord test
no false flags. Two strings at a time is about the limit on a 2-core workspace (~3-4 min per string).

Known test-harness gotcha: `G.pops` keeps only the last 6 pop-ups, so counting pops by length misses some;
use the detection report (`G.diag`) instead.
