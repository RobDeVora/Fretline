# Fretline: session handoff (18 Nov 2026, web v1.68, Android app from the v1.63 build)

Read this first in a new session. It covers how the project is set up, where things stand, how the owner works,
how detection works now, what's open, and a changelog of everything built in the last session (v1.51 to v1.68).

## The project

- **Repo:** `RobDeVora/Fretline` (public). The owner works on an Android phone (Samsung SM-S948U1, Bluetooth
  "Buds4 Pro" headphones) and tests everything there. Changes go **straight to `main`** (no branches or PRs).
  They send screenshots and **detection reports** (results card › 📋 Copy detection report), sometimes as attached
  .txt files.
- **Web app:** one file, `index.html` (~3,900 lines: CSS, a `<script id="core">` with pure logic also exported for
  Node, and a second `<script>` with UI, audio, detection and drawing). GitHub Pages:
  `https://robdevora.github.io/Fretline/`. `sw.js` is the network-first service worker.
- **Android app:** `android-app/`, a Capacitor 7 wrapper that **loads the live site**, so web changes reach it
  without a new APK. Native code in `android/app/src/main/java/com/robdevora/fretline/`:
  - `MainActivity.java`: share/open-with intents, back button → `window.fretlineBack()`, **full screen**
    (`hideSystemBars`: status and nav bars hidden, swipe from an edge shows them briefly; re-applied on
    focus/resume and after the decor view attaches).
  - `IncomingPlugin.java`: delivers shared/opened files to the page.
  - `NativeMicPlugin.java`: records the **phone's built-in mic** with AudioRecord (UNPROCESSED, else
    VOICE_RECOGNITION) and streams 10 ms float32 chunks to the page (`pcm` events). `listInputs()`,
    `start({type})` (built-in / bluetooth / wired / usb; Bluetooth uses call mode), `outputRoute()` and `route`
    events (where sound goes: speaker / bluetooth / wired / usb).
  - Any push touching `android-app/` triggers `.github/workflows/android.yml`, which builds `Fretline.apk` and
    publishes it to the `android-latest` release. The signing keystore is committed (owner knows; fine for
    sideloading). Settings › App says whether the installed APK is the latest build.

### Release routine (every change)
1. Edit `index.html` (and Java for native changes).
2. Bump `const APP_VERSION='1.xx'` in `index.html` **and** `const CACHE = 'fretline-vNN'` in `sw.js`.
3. Syntax check every script block:
   `node -e "const h=require('fs').readFileSync('index.html','utf8');for(const x of h.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)){try{new Function(x[1])}catch(e){console.log('ERR',e.message)}}"`
   Beware: an inline `//` comment inside a one-line statement comments out the rest of that line (this broke
   drawing once). Use `/* */` in single-line code.
4. Test in headless Chrome (Playwright, `/usr/bin/google-chrome`). See **Testing** below.
5. Commit and push to `main`. Pages deploys in ~1 min; check with `gh run list -R RobDeVora/Fretline -L 1`.
   For native changes, wait for the "Build Android app" run (`gh run watch`), then send the APK link:
   `https://github.com/RobDeVora/Fretline/releases/download/android-latest/Fretline.apk`.
6. The owner updates with **Settings › App › Check for updates** (compares the live `APP_VERSION`). A new APK has
   to be installed by hand. Tell them clearly when a change needs the APK.

## Where things stand (end of 18 Nov session)

**Confirmed working on the owner's phone:**
- Native built-in mic via the app (fixed notes going silent with Bluetooth headphones): 32/32 on the A blues melody.
- Full screen, per-output sound delay (report shows "output bluetooth (Robert's Buds4 Pro)"), 60 frames/s.
- Landscape layout: the hand stands on the bottom edge, the highway fills the screen, lyrics fit.
- **v1.68, two-note steps:** playing E0+A2 throughout "Boogie shuffle in E" scored 28/96. The pattern matches
  exactly 28 steps; 27 of them counted (only #0, the first, missed), and just one wrong step counted (#6, E+C#).
  All A and B steps (including B+G#) were correctly missed.

**Open / to watch:**
- **False hits on single notes (v1.65/1.66):** sim results are good, but sympathetic open strings can't be
  simulated. The owner hasn't sent a single-note "play one wrong note throughout" report since v1.66. Next time,
  ask for one (e.g. the A minor pentatonic lesson) to confirm.
- **First note of a song** is often missed or judged without context (no history yet). Seen in the sims and in
  the 1.68 report (#0).
- The first E+C# false hit (#6 in the 1.68 report) suggests the "tracker heard it recently" rule can carry over
  from a previous step. Fine for now; watch it.
- Double stops in sim: E2+C#3 played over A2+E3 steps still pass 6 (E3 = E2's octave). See v1.67 notes.
- **MP3 play-along idea:** discussed, not started (see the section below).
- Not done: same-pitch-different-string detection; a "Jam" style; immersive mode is done but notch/cutout mode is
  left at default.

**Owner's preferences and style:** plain, practical explanations; they like seeing screenshots of layout changes;
they want detection to be strict (wrong notes must not count) and report results honestly. They prefer
one-tap/one-time settings and maximum screen space for the highway and hand.

## How note detection works now

`detectFrame` (every animation frame, analyser fftSize 4096): level (RMS), YIN pitch on the last 2048 samples
(`det.midi` raw, `det.stableMidi` after 2 frames), pick onsets (level jump; energy burst above 2.5 kHz for re-picks),
room noise. `gate()` = min(sensitivity cutoff, max(4×room noise, 0.0012)).

`matchEvent(e,i,now)`:
- **Chords (3+ notes or a chord symbol):** `chordScore` over 3 frames; strums count on a pick onset. Per-string
  dead/muted check (`chordStrings`, `chordCheck`) after a strum is credited.
- **Single notes and two-note steps:**
  1. **Path 1:** the tracker's reading matches a note (`noteOk`; "any octave" is now **off by default**), freshly
     picked, confirmed by the targeted check, and (two-note steps) `partnerOk` for the other note.
  2. **Path 2:** targeted check (`targetInfo`: Goertzel on resolvable overtones vs. semitone neighbours) ≥ 0.63
     and the note's strength jumped 2.5× (or a quick re-pick), for 2 frames. Blocked when the tracker clearly
     hears a different, real note `mh` (stable, or raw `det.midi` at a pick):
     - the expected note's own unshared overtones are under 30% of `mh`'s strength (sympathetic open strings),
       unless `mh` is one of the last 3 expected notes (previous note ringing) or the expected note sits on
       `mh`'s overtones;
     - the expected note is `mh`'s 2nd..8th overtone and `mh` was just re-picked (its own unshared overtones
       jumped at least half as much; history `G.uHist` per heard note);
     - two-note steps: each note must stand out on its own against an `mh` that's in neither; then `partnerOk`.
  - `partnerOk(e, base)`: the other note counts if the tracker reported it in the last 500 ms
    (`G.heardRecent`), else if its overtones not shared with the base note stand out (all, or the lowest three)
    with ≥ 20% of the base note's strength.
- **Wrong notes** are reported after a 250 ms wait (`wrongSuspect` / `wrongSettle`) and dropped if the note is
  credited or a new pick arrives. **Timing grades** (Perfect ≤ 50 ms, Good ≤ 100, Okay) from the pick time.

## Features from earlier sessions (still current)

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

## Changelog of the last session (v1.51 to v1.68)

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

## v1.66: more false-hit fixes (path 2 of `matchEvent`)

Owner's next report (playing the lesson) still showed false hits at the end: G3 and D3 credited while D5 rang —
open G/D strings ringing in sympathy (D5 is their overtone). Also found in sim: the block only ran when the
tracker had settled, and the re-pick test reset per event. Now, in path 2, with the heard note `mh` (stable, or
the raw `det.midi` right at a pick) really there (score >= 0.6):
- strength of the expected note = its overtones that don't land on any of the heard note's (1.5%) — unless the
  heard note is one of the last 3 expected notes (previous note ringing on) or the expected note sits on the
  heard note's overtones (`up`); blocked if under 30% of the heard note's strength;
- `up` (expected = heard's 2nd..8th overtone): blocked if the heard note's own unshared overtones jumped at least
  half as much as the expected note (re-picked); history kept per heard note across events.
Sim: one-note runs G3 1/34, D5 4/34 (exact), D4 4/34 (2 false: first note of the song, one D5); correct 33/34;
fretboard sweeps A/G/e 18/18; wrong-note sweep 0; song sim 17/17. Sympathetic strings aren't in the sim (samples
are single notes), so the owner's phone is the real test for that case.

## v1.67: two-note steps need both notes

Owner played E0+A2 (E2+B2) through "Boogie shuffle in E" (all steps are two notes) and got 71/96: steps with 2
notes go through the single-note matcher (`isChordEv` is 3+ notes or a chord), whose `e.notes.some(...)` accepted
either note, and the low E is in every E step. Now `partnerOk(e, base)`: every other note must stand out on its own
overtones that don't land on the base note's — all of them, or the lowest three (A2's 2nd at 220 Hz is what tells)
— with at least 20% of the base note's strength. Used in path 1 (base = the note the tracker hears) and at the end
of path 2 (base = best-scoring note; checked after the strength history is updated, or rises are never seen).
Also in path 2: if the tracker clearly hears a note in neither, each note must stand out against it on its own.
Sim (`test_double_stops.py`): correct 63/64; owner's E2+B2 run 24/64 = exactly the E+B steps (old code 56/64).
Known leaks: E2+B2 played over B2+G#3 steps passes all 8 (E2's 5th overtone 412 Hz ~ G#3's 2nd 415 Hz; excluding
recently heard notes' overtones fixed 2 but cost 5 correct steps, not used). E2+C#3 played over A2+E3 steps still passes 6 (E3 = octave of E2; A2's 5th next to C#3's 4th);
requiring A2's lowest unshared overtone alone fixed 3 but cost 4 correct, so not used.

## v1.68: two-note steps, real guitar

On the owner's phone v1.67 scored 3/96 playing E0+A2 through the boogie: even the real E+B steps failed — the
overtone test for the second note (tuned on sampled notes) is too strict for a real guitar via the phone mic. But the
report showed the tracker flicking between both notes ("heard E2>B2>E2"). `partnerOk` now accepts the second note if
the tracker itself reported it in the last 500 ms (`G.heardRecent`, filled in `matchEvent`; time from `now`, not
performance.now(), so the sim's clock works); the overtone test stays as the fallback. Sim unchanged (its sampled
notes don't make the tracker flick): correct 95/96, E2+B2 36/96.
**Confirmed on the phone:** E0+A2 throughout → 28/96: 27 of the 28 real E+B steps, 1 false (#6 E+C#), all A/B
steps (incl. B+G#) correctly missed.

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
See `tools/detection-tests/README.md` (every test is listed with how to run it and its last results). Setup in a
fresh workspace: `mkdir -p /tmp/samp && cd /tmp/samp && npm pack tonejs-instrument-guitar-acoustic-mp3@1.1.2 &&
tar xzf *.tgz` for the samples; `pip install --break-system-packages mido` to build test MIDI files. Most UI tests
need the repo served locally (`python3 -m http.server 8769 -d <repo>`), because module/worklet loading fails from
file://. Key detection checks to rerun after any detection change: `song_report_sim.py` (17/17),
`sweep_fretboard.py <repo> <string> 0.5` (18/18), `sweep_wrong_notes.py <repo> <string> 0.5` (0 hits),
`test_one_note_all_song.py` (correct 33/34; `PLAY=55` 1/34), `test_double_stops.py` (correct 95/96;
`PLAY2='[40,47]'` 36/96).

Real guitar recordings (`tonejs-instrument-guitar-acoustic-mp3` via
`npm pack`) through the app's real per-frame code. Network in the workspace only allows package registries
(npm works; GitHub Pages / jsdelivr / gleitz soundfonts are blocked), so the band's soundfonts can't be fetched
there (tests used stand-in samples).
