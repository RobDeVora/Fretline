# Fretline: session handoff (18 Nov 2026, v1.65 + APK from v1.63)

Read this first in a new session. It covers how the project is set up, what was built in the last session, the
problem still being worked on, and what to do next.

## The project

- **Repo:** `RobDeVora/Fretline` (public). Owner works on an Android phone; changes go **straight to `main`**
  (no branches/PRs). They test on the phone and send screenshots and detection reports.
- **Web app:** a single file, `index.html` (~3,250 lines: CSS, a `<script id="core">` with pure logic that's also
  exported for Node, and a second `<script>` with UI, audio, detection and drawing). Served by GitHub Pages at
  `https://robdevora.github.io/Fretline/`.
- **Service worker:** `sw.js`, network-first.
- **Android app:** `android-app/`, a Capacitor 7 wrapper that **loads the live site**, so web changes reach the app
  without a new APK. Native code: `MainActivity.java` (share/open-with intents, back button → `window.fretlineBack()`),
  `IncomingPlugin.java`. Any push touching `android-app/` triggers `.github/workflows/android.yml`, which builds and
  publishes `Fretline.apk` to the `android-latest` release. The signing keystore is committed (owner knows; fine
  for sideloading).

### Release routine (every change)
1. Edit `index.html`.
2. Bump `const APP_VERSION='1.xx'` in `index.html` **and** `const CACHE = 'fretline-vNN'` in `sw.js`.
3. Syntax check every script block, e.g.
   `node -e "const h=require('fs').readFileSync('index.html','utf8');for(const x of h.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)){try{new Function(x[1])}catch(e){console.log('ERR',e.message)}}"`
4. Test in headless Chrome (Playwright, `/usr/bin/google-chrome`); see `tools/detection-tests/`.
5. Commit with a descriptive message and push to `main`. Pages deploys in ~1 min.
6. The owner updates with **Settings › Check for updates** (compares the live `APP_VERSION`).

## What exists now (features added in the last session, roughly in order)

- Setting to hide the fretboard; remaining-time counter in the HUD; tip text kept clear of the HUD.
- Strumming: pattern locked to the bar grid (no overlapping strums); double-time MIDI detection (130+ BPM with a
  chord per bar → halved). Strums drawn as **chord fingering** (fret numbers on first strum of a chord, dots on
  repeats, ▼/▲ direction arrows); Settings › "Strums show" switches back to big D/U arrows.
- Hit zone: glowing line, notches, per-string target rings that light up; optional shaded timing band (off by
  default). Timing window: a note counts once its edge touches its ring; Settings › Timing window
  (Normal/Relaxed/Very relaxed).
- **Colours & theme** settings (6 dark themes, note palettes incl. colour-blind and custom, hit line colour, highway
  style, fretboard wood, live preview).
- **Check for updates** button; phone **back button** support (web history guard + native handler).
- **Backing band** (`buildBand`): drums (synth), bass and piano (General MIDI soundfonts, downloaded once), built
  from the song's chords/key and the player's role per bar (melody → piano comping; chords → piano melody;
  riffs → rock beat). Toggle "🥁 Band", volume in Settings.
- **Written solos** (`genSolo`): pentatonic box, call/answer phrasing, chord tones on strong beats, techniques.
  Blues → 12-bar. Solo style in Generate/Mix/quick-generate; course units "Your first solos" and "Solos across
  the neck"; Slides and Bends lessons.
- **Techniques:** notes can have `tech:'h'|'p'|'s'`, `bend:<semitones>`, `vib:true`. Drawn (arcs, slide lines, bend
  arrows, vibrato), scored (bend counts up to its target, legato needs no pick), played in Listen, parsed from tabs
  (`5h7`, `7p5`, `5/7`, `7b9`, `~`).
- Playback: notes stop at their written length (no 4.5 s ringing hum).
- **Detection** (see below), **dead-string / muted-string feedback for chords** (✓ ✕ ! per string, pop-ups,
  results tally), "you played here" marker (green/red ring on the string you most likely played), "Wrong string".
- Timing: **Sound delay** (output latency, Auto or set; tap test to measure it) so band/Listen/count-in are
  scheduled early; **Latency compensation** up to 600 ms; results show how late notes reached the app and offer
  "Set it to … ms".
- **I'm using headphones** setting (disables speaker allowances: ignoring picks near band hits, deafness after
  app sounds).
- **Detection report** on the results card (📋 Copy detection report): per note expected / heard / picks / note
  score / level vs cutoff, plus settings and (v1.50) the microphone in use.
- **Settings › Microphone** (v1.50): choose the input device; shows mic name and whether noise suppression,
  echo cancellation and auto volume are actually on.

## How note detection works now (single notes)

`detectFrame` (every animation frame, analyser fftSize 4096): level (RMS), YIN pitch on the last 2048 samples
(`det.stableMidi` after 2 frames), pick onsets from (a) level jump while climbing, re-armed once the note fades,
and (b) a burst of energy above 2.5 kHz (re-picks on a ringing string); pitch-change onsets; room noise
(5th percentile of level over ~30 s). `gate()` = min(sensitivity cutoff, max(4×room noise, 0.0012)).

`matchEvent` (single notes) counts a note when either:
1. the pitch tracker's reading matches **and** is freshly picked **and** is confirmed by the targeted check
   (exact ≥ 0.45; octave reading needs expected ≥ 0.55 or the octave note itself ≥ 0.7); "any octave" = ±1 octave;
2. **targeted check** (`targetInfo` → Goertzel on each resolvable overtone vs. the semitone neighbours, min of
   all-overtone and odd-overtone scores) ≥ 0.63 **and** the note's strength jumped 2.5× over the previous ~0.4 s
   (or it's a quick repeat of the same note with a fresh pick), for 2 frames, at ≥ half the cutoff.

Wrong-note sound: pitch reading wrong and expected note absent (< 0.5) 140 ms after a pick, or a fresh pick with
no sign of the expected note (< 0.3) after 220 ms. Ignores pitches of the last few notes (still ringing).

Chords/strums: strums count on a pick onset; chord events use `chordScore`. Per-string check (`chordStrings`,
`chordCheck`) runs 130-340 ms after the strum is credited.

## Current problem being worked on

The owner (Android phone, **Bluetooth headphones**, playing "Melody in A blues · 0:59 #292482" at 65 BPM in
Generate) gets ~69% with misses clustered on some notes. The latest detection report (v1.49) showed every miss as
**"heard nothing · picks 0/0 · level 0.1/1.2"** while hits had levels 2-97, and room noise 0.1, i.e. the mic signal
drops to near digital silence for whole notes. Timing readout also jumped 259 → 421 ms between runs with no change.

**Diagnosis:** call-style processing is gating the input. Most likely Android is recording from the **Bluetooth
headset's call microphone** (HFP/SCO: far from the guitar, voice-only noise suppression, variable latency), or the
phone applies noise suppression despite the constraints. Simulations can't reproduce this; everything passes there.

**v1.50 (just shipped) asks the owner to:**
1. Open Settings and report the blue "mic: …" line (device name + whether noise suppression etc. are on).
2. Choose the phone's own microphone in Settings › Microphone if listed, play the song again, send the report.
3. If only "Automatic" exists, do one run with Bluetooth disconnected (speaker, untick headphones, or wired) and
   compare reports. If the 0.1 levels disappear, the headset mic is the cause.
4. Hold off on "Set it to 420 ms" until the mic is sorted, then recalibrate (tap test for sound delay, then the
   results card's latency suggestion).

### Next steps depending on the answer
- **Headset mic confirmed and the phone mic can be chosen:** consider remembering/auto-preferring a built-in mic
  when a Bluetooth input is detected (label contains "Bluetooth"/"Headset"/"Hands-free"), with a one-time tip.
- **Web can't pick the phone mic:** the Android app could force it natively (e.g. in `MainActivity`, use
  `AudioManager.setCommunicationDevice` / avoid SCO, or `AudioRecord` with `MediaRecorder.AudioSource.UNPROCESSED`
  or `VOICE_RECOGNITION` routed to the built-in mic, streamed to the page via the plugin). This needs an APK
  rebuild and real-device testing.
- **Noise suppression shows ON despite constraints:** document it in the tip; the native route above also fixes it.
- Then recalibrate timing (sound delay tap test, then latency suggestion) and ask for a fresh report.

## v1.51: native built-in mic (Android app)

The owner's v1.50 report: mic "unnamed", noise suppression / echo cancel / auto volume all **off**, only
"Automatic" in the mic list, and misses still at level 0.1 (24/32). So the phone-side processing isn't the cause
and the web page can't pick the phone mic: the WebView switches the Bluetooth headphones into call mode (SCO) and
the headset's own voice filtering silences the guitar.

Fix: `NativeMicPlugin.java` (registered in `MainActivity`) records with `AudioRecord` from `TYPE_BUILTIN_MIC`
(source UNPROCESSED if supported, else VOICE_RECOGNITION, else MIC; float or 16-bit), takes the headphones out of
SCO/communication mode, and sends 10 ms base64 float32 chunks as `pcm` events. Stops on app pause, resumes after.
In `index.html`, `startNativeMic()` feeds them through an AudioWorklet queue (40 ms pre-buffer, 150 ms cap, counts
underruns as "gaps", linear resampling if rates differ) into the same analyser, so detection is unchanged. Used
when the app has the plugin and Settings › Microphone is "Phone's built-in microphone (recommended)" (`micId ''`);
"Let the phone choose (old way)" is `micId 'web'`. If the native mic fails, it falls back to getUserMedia and
the report says "(app mic failed: …)". Old APKs / browsers behave as before (old APK shows a download link in the
mic hint). Report line now shows e.g. `mic: built-in mic (…) via the app · unprocessed · float · 48000 Hz · gaps 0`.

**Needs:** the owner to install the new APK (android-latest release), play the A blues melody again and send the
report. Check the mic line says "via the app" and "built-in mic", gaps stay ~0, and the 0.1-level misses are
gone. Then recalibrate: with headphones in music mode (A2DP) the output delay changes, so redo the sound delay
tap test and then use the results card's latency suggestion. Not tested on a real device; Java not compiled
locally (no Android SDK in the workspace), so check the Actions build.

**Result (owner, Samsung SM-S948U1, new APK):** 32/32 (was 24/32). Mic line: `built-in mic (SM-S948U1) via
the app · voice recognition · float · 48000 Hz · gaps 2` (UNPROCESSED isn't offered on this phone). Room noise
0.7, no 0.1-level notes. Mic problem solved. Next: recalibrate timing (tap test, then latency suggestion; latency
was still 250 ms / sound delay 70 from the call-mode days). Worth watching: #6, #22, #29 counted with picks 0/0 at
levels 2-5 (quick repeats / soft notes); could be ringing from the previous note being credited.

After recalibrating (latency 150 ms, sound delay 190): 32/32 again, every note with a pick. Mic gaps 4.

## v1.52: timing grades and fewer false "Wrong note"s

- **Grades:** each hit is graded from its pick time minus latency compensation (`G.hitOff`, `timingGrade`):
  Perfect ≤ 50 ms, Good ≤ 100 ms, else "Okay · early/late" (all × the Timing window setting). Pop-up colours
  green / blue / amber; results card shows "Perfect n · Good n · Okay n" (`#rGrades`); report adds e.g.
  `· perfect +23 ms` per note. Without a detected pick it falls back to the credit time. Wait mode just says Good.
  The sim shows +67 ms raw detection delay, which the latency suggestion absorbs on the phone.
- **Wrong note wait:** the owner saw "Wrong note" on note #9 (A3 on G2 after C4 on B1) in two 32/32 runs: a
  fretting finger sounding the B string (C#4), heard as a pick. Wrong notes are now suspected (`wrongSuspect`)
  and only reported after 250 ms (`wrongSettle`) if the note wasn't credited and no new pick came; otherwise the
  report says `cancelled wrong:…`. If the note is missed while a wrong note is pending, the pop-up says "Wrong
  note"/"Wrong string" instead of "Miss". Wrong-note sweep (G string) flags exactly as before. The ghost-note sim
  couldn't reproduce the phone's false pick, so this needs the owner's next report to confirm.

## v1.53: choose Bluetooth headphones' mic (new APK)

Owner asked for a Bluetooth option alongside built-in and "old way". `NativeMicPlugin.listInputs()` returns
inputs by kind (builtin / bluetooth / wired / usb); `start({type})` records from that kind. For Bluetooth it
enters call mode (MODE_IN_COMMUNICATION + `setCommunicationDevice` on Android 12+, else `startBluetoothSco`), uses
the VOICE_COMMUNICATION source, and leaves call mode on stop/pause or when switching back. Settings values:
`''` built-in, `n:bluetooth`, `n:wired`, `n:usb` (shown only if present), `web` old way. The Bluetooth hint warns
it's call quality and will miss notes; if no headset is connected the built-in mic is used. With the v1.51 APK
(no `listInputs`) the Bluetooth option is shown disabled with "install the latest app". Not tested on a device.

## v1.54: lyrics on screen (🎤 Sing)

Owner's goal: generated vocals from chord-sheet/tab lyrics. Agreed first steps: lyrics on screen with a Sing toggle,
then a vocal guide (band plays the melody while they strum).
- `parseChordSheet` now also returns `ev.lyrics` = lines `[{t0, segs:[{t,d,text}]}]` (`lyricLines`): ChordPro
  `[G]words` and chords-above-words (text cut at the chord columns). Pickup words go with the line's first chord.
  Section labels / `{directives}` skipped; lyric lines without chords are dropped (their chords aren't repeated
  either); repeats (x2) get the words on the first pass. `buildSong` copies them to `song.lyrics` (re-parsed from
  `def.src`, so songs imported earlier get lyrics too).
- `drawLyrics`: karaoke strip between strings and fretboard (current line, part over the current chord in yellow,
  sung part dimmed; next line below). Short screens (landscape): one line laid over the bottom of the highway.
- `#singBtn` (shown only when the song has lyrics), `settings.sing` (default on).
- Not yet: lyrics from tabs, MIDI (.kar lyric events), MusicXML, Guitar Pro. Library chord songs have no lyrics.
- **Vocal guide needs a melody**, which chord sheets don't have. Asked the owner whether to (a) make up a melody from
  the chords and syllables, (b) add real tunes + words to the public-domain library songs, (c) read melody + lyrics
  from MIDI/MusicXML files that have them. Real sung words (vocal synthesis) isn't feasible in the browser now.

## v1.55: vocal guide and Settings › Singing

Owner chose all three melody sources as Settings ticks (no "ooh/aah" voice). Settings › Singing (above Colours):
`vocalGuide` on/off, `vocalVol`, `vocalLibrary` (real tunes in library songs), `vocalFiles` (melody + words from
MIDI/MusicXML), `vocalMadeUp` (made-up melody for chord sheets). 🎤 Sing stays the per-song switch.
- `songLyrics(S)` / `songVocal(S)` pick what to use. Priority: library tune > file melody > made-up.
- Library tunes: `tune:{pickup,notes}` in `library/index.json`, format in `parseTune` (note/beats/syllable, `_` tie,
  `//` new line). Done: Amazing Grace, Jingle Bells (chorus); checked with `check_library_tunes.js`. Saved copies
  pick the tune up in `getLibSong`. More tunes can be added the same way (only add ones known note-for-note).
- Files: `parseMidi` reads lyric (0x05) or karaoke text (0x01) events; `parseMusicXML` reads `<lyric>` (+syllabic).
  `vocalPart` picks the part whose notes start with the words (else a part named vocal/voice/melody); `monoLine`
  takes its top line. `importVocal` shifts it like the played part (`def.vocal`, `def.lyrics`). GP not done.
- `makeUpMelody`: syllables per chord (`syllableSpots`), 1 note per syllable, chord tone on each chord change,
  scale steps between, rising then falling per line, ends on root/3rd. Range ~F#4-E5.
- Playback: flute soundfont (`VOICE_FONT`, own `voxBus`), `voxTick` alongside `bandTick` (works with band off and in
  Listen), not in Wait mode. Real tunes shift only if the capo differs from the song's; made-up ones follow chord
  shapes + capo. With the guide on, the piano stops improvising its own melody (`S.noPianoTune`).
- Not tested on the phone yet. Owner asked about MP3 + chord sheet play-along (see below).

## v1.56: files recognised by their contents

Owner's "Marlboro_Man_Test" (a MIDI they made by merging a lead tab and chords) had no extension, so
`loadImportFile` treated it as a pasted chord sheet → "No chords found". `sniffExt` now checks the first bytes
(MThd → MIDI, %PDF, Guitar Pro headers, zip → .mxl or GP7, `<score-partwise` → MusicXML). Their file then shows
Rhythm Guitar (53 chords), Distortion guitar (24-note lead), Vocals (10 notes, used by the guide) and Bass. Note:
everything in it is in the first ~25 beats (~6 bars); its 3-minute length is only a late tempo marker, so their
merge probably exported just the opening. Parts play one at a time (no lead + rhythm in one part).
🎤 Sing now also shows for songs with a tune but no words (`hasLyrics`).

## v1.57: choose the part (or Lead + rhythm) when opening a song

Owner wants to play the lead, the chords, or both from one imported file.
- Import keeps every part (`allFileParts` → `def.parts=[{label,events,capo,strumAuto}]`, `def.partSel`), all on one
  timeline (`fileShift`: the file's first bar with anything playing; `eventsFromNotes`/`chordEventsFromSymbols`
  take a shared shift). The part picked in the import box uses its settings; others are read as written. Skipped
  if the chosen part is at double speed.
- Tapping such a song in the list shows "Which part?" (`pickPart`, via the message box); the player's 🎸 button
  switches. `usePart` swaps `def.events`/capo/strumAuto and saves the choice; per-song capo override is cleared.
- "Lead + rhythm" (`comboPair`/`comboEvents`): the busiest mostly-single-note part (not bass/vocals) is the lead,
  the busiest mostly-chord part the rhythm; each bar uses the lead if it has notes there, else the rhythm part.
- `parseMidi`: a short first time signature followed by the main one is a pickup bar; everything is moved later
  by (bpb - pickup) so bars line up (owner's file: 1/4 then 4/4). Affects Chordify-style 3/4-then-4/4 files too.
- Tested with the owner's file: Lead + rhythm = lead in bars 1-4, chords in 5-6.

## v1.58: fixes for parts

- Owner: Lead + rhythm with a strum pattern left the highway empty. `applyStrum` rebuilt the whole song from
  `chordSegments` (lead turned into guessed chords, rhythm bars dropped). Now lead events are tagged `ld` in
  `comboEvents`; patterns and simpler chords apply to the rhythm bars only and the lead is kept as written.
- v1.57 regression: parts on the shared timeline could start with long silence (the owner's Vocals part: 10 s).
  `trimLead` starts the played part at its first bar with notes (`def.trim`); `buildSong` moves file words/melody
  by the same amount. Stored `def.parts` stay on the shared timeline.
- Landscape: 🎸/🎤/🥁 show icons only on short screens (`.lbl` hidden at max-height 500px) and selects are capped,
  so the controls fit in two rows again.

## v1.59: finger colours, finger guide, readable notes

Owner asked for notes coloured by finger, a finger indicator at the bottom (its own setting, not tied to the
fretboard) that anticipates the following notes, and said notes move too fast to read the numbers.
- Fingering (`chordFingers`, `planFingers`, core script): chords lowest fret first, one finger per fret where it fits,
  low string first at the same fret, barre with the index for 5+ fretted notes. Single notes: Viterbi over hand
  positions (index finger's fret) for the whole song; moving costs 0.6+0.1/fret (less after 2+ beat gaps), pinky
  slightly penalised, first position preferred for frets 1-4. Sets `n.fg`, `e.fgs` (per string, chords/strums),
  `e.hand`. Re-planned whenever `G.song.events` changes (checked in `draw`).
- `FCOL` open grey, 1 blue, 2 green, 3 yellow, 4 red. Settings › Colours "Colour notes by" (`settings.noteBy`,
  default finger); `noteCol()` used for notes, strum fingering dots, chord labels, tech marks, fretboard dots (which
  show finger numbers when colouring by finger).
- `drawFingerGuide`: strip under the strings (above lyrics' row order: strings, lyrics, guide, fretboard): hand
  position, fingers 1-4 (lit with the strings they press, else the fret they hover), open strings, then the next 6
  fingers/chords with ↗/↘ position-change markers. `settings.fingerGuide` (Settings, under the fretboard tick).
  Full / slim / overlaid depending on room.
- Readability: the owner's screenshots showed quick notes overlapping and hiding each other's numbers. Spacing gets
  up to 1.6x more room for dense songs (`G._gapQ` = 15th-percentile gap), and one note size per song small enough
  for its quick passages. Canvas resolution capped at 2x (was 3x) to keep frames smooth; the detection report now
  has "frames N/s, slow X%, worst Y ms" to see if the phone drops frames. Zoom label: "Highway speed / note spacing".

## v1.60: a drawn hand, bigger numbers, Listen timing

- Owner: Listen notes sound before reaching the rings. Listen schedules each note `soundDelay` early (190 ms, set
  with Bluetooth headphones); through the speaker that's far too much. Added a "Sound − / +" control (`#lsTune`,
  ±10 ms, saved as the sound delay) that shows only while Listen plays. Idea not done: remember the delay per
  output (speaker / Bluetooth / wired) — the native plugin could report the output route.
- Numbers: larger (1.35× radius for one digit), heavier, with an outline. Owner still finds them hard to read in
  landscape where the strings are short; turning the fretboard off gives the strings much more room.
- Finger guide: `drawHand` draws the back of a fretting hand (thumb left, fingers 1-4 in `FCOL`, active fingers
  lit with a glow); beside it the position and a badge per finger used ("③ E3", "0 A open"), then the queue.
  Strip 76k tall (48+ slim); on short screens with the guide on, the fretboard shrinks (min 46 px) first.

## v1.61: one-time sound control, higher highway, bigger hand

- The Listen "Sound − / +" control shows only until ✓ Done (`settings.listenTuned`); Settings › Sound delay ›
  "👂 Line it up by ear" brings it back for the next Listen (`G.tuneAsked`).
- Highway starts higher: `laneTop` 46k with chord names (was 72k), 30k without (was 44k); chord names row moved up
  to `laneTop-20k`. The score panel sits on the right of the chord-name row.
- Finger guide strip up to 88k tall when the strings keep 26+ px each, so the hand is about twice the size in
  landscape with the fretboard off.
- Possible next step: hide Android's status bar during play (immersive mode) in the app for a little more height.

## v1.62 (needs the new APK for the last two)

- Hand still small on the owner's phone: their app screen is ~838x381 CSS with bars, canvas ~310 tall, and the
  strip only went full size if strings kept 26 px. Now the strip height is continuous: as tall as fits while each
  string keeps 21 px (`room-fbx-6*21`, between slim and 88k).
- Settings in tabs (`#sTabs`, `.stab`, `settingsTab()`, remembers `settings.sTab`): Mic & timing / Display /
  Sound / Singing / Colours (the old <details> is now a tab, id `sColors` kept, `.on` instead of `.open`) / App.
- APK: `MainActivity.hideSystemBars()` — immersive (status + nav bars hidden, swipe from an edge shows them for a
  moment), re-applied on focus/resume. Cutout mode left at default (content avoids the camera hole).
- APK: `NativeMicPlugin` reports the media output route (`outputRoute()`, `route` events via AudioDeviceCallback;
  Android 13+ uses getAudioDevicesForAttributes, older picks Bluetooth > wired > USB > speaker). The page keeps
  `settings.soundDelays[route]` and `settings.phonesBy[route]` (written in `saveSettings`), swaps them in
  `applyRoute`, shows a hint on change; speaker starts on "auto" until set. Report shows `output …`.

## v1.63

- Finger strip sits flush at the bottom when the fretboard is off (the 14 px bottom margin goes to the strip),
  with a 16k gap above so the hit line's bottom arrow and strum arrows never touch it. Queue on the badge line;
  chords in the queue show their name once per change (not "0" for the first string, not "C C C").
- Owner on web v1.62 still saw the status bar: probably the old APK. Settings › App now says whether the installed
  app is the latest build (`#appBuild`, checks `NativeMic.outputRoute`). `hideSystemBars` made sturdier: platform
  WindowInsetsController on 30+, legacy immersive flags below, re-run after the decor view attaches.

## v1.64: hand on the bottom edge (landscape)

Owner (full screen now working) wanted the hand's base on the very bottom of the screen and the highway filling
the rest, leaving room for lyrics. In landscape with the finger guide on and the fretboard off, `resizeCanvas` adds
`#player.guideBottom`: the button bar floats over the canvas bottom (absolute, padded left past the hand), so the
canvas runs to the screen edge. `G._Z` = button bar height + one text row; `drawGuideBottom` draws the hand in the
bottom-left corner (base on the edge) and one line above the buttons: position, finger badges, then the queue.
Lanes end 16k above the zone; lyrics sit just above the zone. Portrait keeps the strip layout; narrow screens put
chord names below the score panel (`laneTop` 66k when W<560). Lesson: an inline `//` comment in a one-line
statement commented out `let laneBot` and broke drawing — caught by screenshot test, use /* */ in single-line code.

## v1.65: false hits from overtones and sympathetic strings

Owner played only G3 (A10) through "A minor pentatonic, shape 3" and got 21/34. Simulated (`test_one_note_all_song.py`):
11/34. Causes: (1) "any octave" on, so G3 counted for G4; (2) path 2 of `matchEvent` (targeted check + strength
rise) credited notes that were G3's overtones (D5 = 3rd) or faint sympathetic ringing (E4), because every re-pick
makes everything rise. Fix in path 2: when the tracker hears a different note that's really there
(`targetInfo(m).score>=0.6`), block the expected note if it's under 30% of that note's strength, or if it's one of
its overtones (d = 12,19,24,28,31,34,36) AND the heard note was just re-picked — judged from the heard note's own
overtones that the expected one doesn't share (`G.uHist`, rise 1.8x). A phantom low note (tracker said D2 for A3)
has no unshared overtones so it doesn't block. Result: G3-only 1/34 strict (6/34 with any octave), correct
playing 33/34 (unchanged), fretboard sweeps A/G 18/18, wrong-note sweep 0 hits, song sim 17/17.
`anyOctave` now defaults off, switched off once for existing settings (`settings.octV2`).

## Idea: play along with an MP3

Owner asked whether an MP3 + chord sheet could be combined so they play the guitar part. Answer given: chords and
rhythm yes (play the MP3 as the backing, line the chord sheet up to it — a "tap along on first listen" step to
mark each chord change is the reliable way, auto beat-finding as a helper; then score strums against it). Melody/
solo parts need a tab or MIDI of that part; pulling the guitar notes out of a mixed recording isn't reliable.
Headphones needed (the mic would hear the MP3's guitar). Use the owner's own files only; nothing added to the
library. Not started — waiting for the go-ahead.

## Other open ideas mentioned but not done
- Same-pitch-different-string detection (timbre/inharmonicity), labelled beta.
- A "Jam" style: improvise over the band with the scale shown on the fretboard.

## Testing
See `tools/detection-tests/README.md`: real guitar recordings (`tonejs-instrument-guitar-acoustic-mp3` via
`npm pack`) through the app's real per-frame code. Network in the workspace only allows package registries
(npm works; GitHub Pages / jsdelivr / gleitz soundfonts are blocked), so the band's soundfonts can't be fetched
there (tests used stand-in samples).
