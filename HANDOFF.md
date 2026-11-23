# Fretline: session handoff (18 Nov 2026, evening · web v1.148 · Android APK last rebuilt at v1.80)

Read this first in a new session. It covers how the project is set up, where things stand, how the owner works,
how detection works now, what's open, and a changelog (newest first from v1.106 down to v1.69, then the older
v1.51–v1.68 log). **Start with "Where things stand" and "Picking up the conversation" below.**

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

## Where things stand (18 Nov 2026, evening)

**Versions:** web **v1.106** (sw cache `fretline-v94`). The APK was last rebuilt for v1.80, **v1.94 adds `SongFilesPlugin` and v1.95 `KeepAlivePlugin` + `KeepAliveService`, so it needs the NEW APK** (Capacitor plugins:
`IncomingPlugin`, `NativeMicPlugin`, `NativeSeparatorPlugin`, `SongFilesPlugin` = Demucs on all cores + save to Downloads; minSdk 24,
onnxruntime-android 1.22.0, arm64-v8a + armeabi-v7a only). Everything after v1.80 is web-only. The owner has the
v1.80 APK installed.

**What this session built (details in the changelog sections below):**
- v1.69–v1.76 detection work: highway speed in px/s, first chord after a switch, right-note playback in time,
  arpeggios over ringing strings, strums must be the right chord, string colours, a research comparison with
  Yousician / Gibson / Simply (`docs/RECOGNITION_RESEARCH.md`), tuning follower.
- **Lab** (`lab/stems.html`, linked from Settings › App): split an MP3 with Demucs htdemucs_6s (guitar + band
  without guitar), on device. In the APK it uses all cores natively (0.53–0.62× song length on the owner's phone;
  web runtime on one thread is 2.4×). Then it makes a highway song:
  - AI notes (Basic Pitch + cleanup, v1.81) **or** a tab / chord sheet / MIDI / MusicXML / Guitar Pro / PDF lined up
    with the recording (v1.83–v1.86: order-only alignment for text; files use their own timing, best of both).
  - Saved to My songs as `kind:'rec'`: backing = the band WAV, guide = the real guitar WAV (Listen plays the real
    guitar; Play with headphones + "play the right note" fades it in while you hit).
  - Tempo: auto, ½ / 2× buttons, type a BPM, tap tempo; ♩ button in My songs (v1.82). Notes keep their played
    timing (1/48 beat, v1.85).
- v1.86: MIDI tab exports with one channel per string are read as one part (also fixes the import screen).
- 21 Nov (no app change, analysis only): **vibrato is not checked anywhere.** `vib` is only drawn (wave on the highway) and played in the preview; no detection path reads it, so a vibrato step is credited like a plain note. Owner's Bends run (1411): pyin contours of the 8 long steps show no vibrato (wobble 7-13 cents p2p = steady; the larger numbers are the next note starting or an octave glitch). Steady held notes wobble up to about 20 cents p2p below 3 Hz, so a detector of >=30 cents p2p at 4-9 Hz over >=2 cycles would separate them. NOT built: generated Solo lessons put `vib` on every note >=1 beat, so a hard gate would fail many ordinary notes; proposal = non-blocking 'vibrato heard / not heard' line in the report and a small pop. Tool: `tools/detection-tests/vibrato_check.py`.
- 23 Nov (analysis only, no app change): **Fingerpicking Am/Em/C run 1237 (v1.148, 53/64).** Owner asked if good hits are missed because the previous note rings. Basic Pitch says 5 of the 11 MISS steps were really played (#5 A3, #13 G3, #14 B3, #37 A3, #46 B3; #56 unclear) and 6 were not (#8, #9, #40, #58, #60 bp<=0.26); 4 credited hits are doubtful (#24, #32, #57, #61). In all 5 false misses the tracker's 'heard' list is the previous note still ringing (C4, B3, G3, G3) plus an OCTAVE-BELOW reading of the target (A2 for A3, G2 for G3, B2 for B3, and D2 phantoms), with picks 0-1 of 3-5. So: ringing contributes but the sub-octave flip of yin while the old note sustains is the main failure. Levels were fine (40-76). Replay bench is NOT faithful on this run (agree 37/64, PAD 0/0.093/0.2/0.3 all 30-37; it credits 4 of the 5 real false misses and misses ~20 real hits; offset fit 325 ms vs 119 ms before; report gate 3.7 vs 'cutoff 7.1') -> do not tune against it until the replay matches (check noise-floor/gate learning and the tuning offset -5 cents in the injected run). Candidate fix once the bench matches: when the tracker reads exactly target-12 right after a fresh pick and the target's own harmonic score is >=0.45, treat it as the target (strictness risk: a real wrong-octave play).
- v1.148: **Bend misses now say how far you bent.** Owner's run 1223 (v1.147): 8/16, all 8 bend steps MISS 'not bent up'. Pyin on his audio: he did bend, but only +0.2..+0.33 semitone on the D4 steps (needs +2), ~+0.4 on the G4 half-bend (needs +1), C5 steps ~0. So the strict rule was right, not too harsh (the tracker rounds to the nearest semitone, so a bend needs to reach about the target minus half a semitone). Change: report only. `diagEnd` on a missed single-note bend step measures the highest 3-frame-median pitch above the note's first 0.3 s from `G.vibC` and writes `d.bt` -> ' · bent up 0.3 of 2 semitones needed'. Scoring unchanged. Open: 'not bent up' notes only appear when the plain note was held >250 ms; a tolerance (e.g. count >=80% of the way) was considered and NOT done because the owner wants strict. sw cache v138.
- v1.147: **Vibrato is now measured and reported (never scored).** Owner asked for 'vibrato heard / not heard' that doesn't touch scoring. `detectFrame` keeps the pitch contour in cents (`G.vibC`, only in lessons that have a single-note `vib` step); `diagEnd` queues each HIT vib step (`G.vibPend`, window = step start + latency + 0.35 s (0.65 s for bend steps) to the end of the note − 50 ms); `vibMeasure` drops frames >150 cents from the median (next note / octave slip), resamples to 50 Hz, detrends, Hann-windows and takes the strongest 3.5-9 Hz component (peak-to-peak cents); `vibTick` (from `update`, flushed in `finish`) writes `diag.vb` and a pop. Thresholds: >=12 cents 'vibrato N cents @x Hz' (green pop), 9-12 'slight vibrato', below 'no vibrato heard', too short/quiet 'not judged'. Report: ` · vibrato …` on each vib step + a header line 'Vibrato (report only…)'. Evidence: IDMT-SMT-Guitar V2 (Zenodo 7544110, pulled with `remotezip` range requests, dataset2 annotations label expressionStyle VI/NO): the app's own yin+vibMeasure on 68 labelled vibrato notes: 69% >=12 cents (median 20; the misses are mostly the 'slow-fast' exercise's weak/slow notes), plain notes 0/7 flagged (clean DI, <=3 cents; only 7 judged); owner's steady phone-mic notes 1-8 cents (one 20, probably the next note). Synthetic (test_vibrato.py): 30 cents p2p reads 27-28; steady reads 'no vibrato heard'. Only judged on HIT steps. Tools: `vibrato_idmt_run.js` (+ `vibrato_idmt_fns.js.txt` = yin/vibMeasure extracted from index.html), `vibrato_check.py`. Open: needs real vibrato recordings from the owner to confirm the 12-cent line on his mic; plain-note sample from IDMT is small; if it holds it could become a rule on Bends-lesson steps only. sw cache v137.
- v1.146: **Bend steps need a real bend.** Owner (21 Nov, Bends and vibrato run): 'just playing the note worked, I didn't have to bend the string' (his report showed 'heard D4' on a D4→E4 bend, 16/16). Cause: path 1/2 accept the fretted pitch as well as every pitch up to the bend (`targetInfo` tries k=0..bend, `noteOk` accepts a..a+bend). New gate at the top of the single-note part of `matchEvent`: a step with one note that has `bend` returns false until the pitch tracker has read the TOP of the bend (`det.midi===midi+capo+bend`, above the gate, onset inside this step's window) for 100 ms (`G.bdOK`, reset per step/song via `G.bdI`/`G.bdSong`); after that the normal paths decide. If the plain fretted note was heard and held >250 ms the diag note says 'not bent up to X'. Bend steps are also judged 0.6 s later than plain steps (`waX=wa+0.6*b`) because pushing the string up takes 0.3-0.5 s. Two-note steps with a bend are not gated (generated lessons never make them). Validated: `tools/detection-tests/test_bends.py REPORT` builds a synthetic recording from the owner's 1411 report step times: unbent = 0/8 bend steps credited, bent (half step then whole step) = 8/8; replay of the owner's real unbent audio: all 8 bend steps now MISS (they were HIT). Regression tests unchanged (95/96, 33/34, 95/96, 17/17, sweeps 18/18 on all six strings, wrong-notes 0/18). Not done: vibrato steps (`vib`) are still not checked (needs pitch wobble detection); a bend that stops short (e.g. 40 cents flat) reads as the lower semitone and misses. sw cache v136.
- v1.145: **First detection changes tested on the owner's own recordings (replay_run.py).** Replay bench fixed: the recorded file is aligned with the app's step clock (only the report's @N wall-time stamps drift), so the replay plays the file un-warped (`WARP=0` default) with `PAD=0.093` s; on the D major arpeggio run the replay now agrees with the real HIT/MISS on 153-157/160 steps and its grades match within ~15-30 ms. `LESSON=<id>` replays course lessons (i-pull, i-slide, i-bend checked: lesson rebuilt identically); BP referee (+-0.22 s, legato steps not judged) printed for real vs replay; debug hooks in matchEvent (inactive unless set): `window.__hitLog` (which path credited each step), `window.__trace=new Set([...])` (per-frame path-2 state + blocks, `TRACE=23,54` env in the replay tool), `window.__legLog`. Changes: (1) legato steps (h/p/s) no longer pass path 2 on 'legato' alone (needs `rose`); path 1 for legato needs `legNew` = the pitch tracker started a new note inside the window (margin 150 ms, slides 400 ms because the owner slides right after the pick) and after the last hit. Pull-offs run: 9 silent credits ('picks 0/0, heard nothing, okay -180 ms') and an E4 played by mistake two steps earlier crediting the E4 pull-off step are gone (replay legato credits 10 -> ~2); slides 32/32 and bends 16/16 unchanged. (2) `ringingPrevExact` (same midi in the last 3 steps) replaces pitch-class `ringingPrev` in the path-2 block: an A2 heard while A3 was two steps back no longer counts as 'ringing on' (fixed D3 false hits #32/#112: D3 credited from the A2's shared A4 overtone), and a note that IS the previous step ringing on no longer blocks (`block=!ringOn&&...`). (3) `bigRise`: fresh pick (<= 150 ms), not legato, score >= 0.45, T >= 8 absolute and >= 8x its level before -> credit (B3/G3 picked over a louder ringing open D3: #23, #43, #151 rescued, all BP-confirmed; without the absolute T >= 8 it added 5 false hits from near-silent baselines). D major replay: false hits 9 -> 7, false misses 6 -> 5 (BP referee), remaining false hits #28/#44/#48 (A2/D3 targets with the tracker hearing nothing or B2) and #84/#156/#159 (path 1). Synthetic suites unchanged: double stops 95/96, one-note 33/34, window steal 95/96, song sim 17/17, sweep_fretboard D/B 18/18, sweep_wrong_notes D/B 0/18. Also: BP doubt flags and the strict count skip legato steps (BP's onset is weak for them). Next ideas: #54/#118 (G3 rose only 2.3x over a sympathetic open-G level, then blocked by a D2 phantom) and the path-1 false hits. sw cache v135.
- 21 Nov (no app change, tools only): **first real audio (owner's v1.144 'Arpeggios in D major #158181' run + 'Strumming in A minor') analysed.** (a) The recording axis drifts against the step clock: Basic Pitch onsets of the step notes move from +15 ms at 3 s to +600 ms at 120 s (Theil-Sen fit 309 ms/min, offset 122 ms, 82 matches; the app's own v1.144 fit said 239 ms/min). The owner's picks stay in sync with the step clock the whole run (grades perfect/good), so it is the audio axis that is stretched (strum run: -62 ms/min, so the sign varies per run: probably the phone's input/output clocks (Bluetooth output)). (b) With correct alignment, BP-as-truth (onset >= 0.5 within +-150 ms): 102 of 115 hits confirmed; 13 hits not confirmed (#6,8,20,28,32,41,44,48,84,110,112,156,159; ~9 are real neighbour-note acceptances, e.g. #32 D3 credited while the player picked A3: 'heard C#4>C#3>A2', bp saw A3 .82; #41/#110 are just 220 ms late); 37 of 45 misses agree; 8 misses where BP heard the target: #23 B3, #54 G3, #118 G3, #151 B3 (target note present at 0.8-0.86 but the tracker keeps hearing the ringing open D3, 'heard D3 picks 1/0 note .79-.92': the block in path 2 (`block=tT<0.3*mi.T`, heard note ringing from 1-3 steps ago) is the suspect), #85 D3 (level 6.0 < gate 6.7: played softly), #17/#65/#113 ambiguous (bp .58-.6). (c) New tool tools/detection-tests/replay_run.py: warps the recorded wav back to wall time (BP drift fit), injects it as the page's getUserMedia stream started when the app starts its recording, replays the generated lesson (seed/key from the report title; diff 1 matched the owner's), settings from the report; PAD 0.243 s (setting latency 130 + start lag) makes the replay grades match the real run (median +45 ms). Replay agrees with the real HIT/MISS on 141/160 steps and reproduces the same error classes (false hits 6,28,32,41,44,48,84,110,112; false misses 17,23,54,85,118), so it can be used to test detection changes against the owner's recordings (use /tmp/truth.py-style BP truth: count false hits (hit and bp<0.5) and false misses (miss and bp>=0.6)). Run: `/tmp/withsrv.sh python3 /abs/path/replay_run.py AUDIO.wav REPORT.txt /tmp/out` (2.5 min). NOT yet tried: relaxing the path-2 block for a ringing note that is not an overtone relation of the target (would fix #23/#54/#118/#151 but must be checked against the false-hit side and the 95/96 + 33/34 suites).
- v1.144: **Basic Pitch overnight update (the owner left it to me; access to arxiv/github/osf/figshare/mendeley/unpkg/jsdelivr now works, kaggle/tfhub/storage.googleapis do not).** (1) Robust alignment: Theil-Sen straight line (clock drift + offset) through confident matches (bp >= 0.8, |offset| <= 450 ms, slope capped 20 ms/s), then local median of the residuals clamped to +-120 ms (replaces v1.140's unbounded local median that gave -397..610 ms in the E major run). Report/status shows 'clock drift X ms/min from N matches'. (2) 'Strict count' side by side with the normal score (NOT used for scoring): single-note hits that bp does not confirm (bp[0] < 0.5) are subtracted; shown in the results status and report header; marked 'alignment NOT trusted: ignore doubts' when fewer than 8 single-note hits, fewer than 6 matches, or > 35% of single-note hits would be dropped. (3) Larger GuitarSet check (30 clips, 9.9k queries; tools/detection-tests/guitarset_compare.py, 5 min): Fretline now (v1.139) recall 70.7% / semitone FA 4.9% / ring-through FA 27.1%; 'before v1.126' 82.2 / 9.0 / 85.4; Basic Pitch alone (non-causal) 81.0 / 2.7 / 21.6; sweeping Fretline's own threshold only moves along the same curve (scPick >= .55: 78.6 / 10.3 / 30.7; >= .7: 63.4 / 3.6 / 24.1), so v1.126's .63 is a sensible knee. CAUSAL Basic Pitch (2 s of audio ending 0.25 s after the note, the live-feasible version; sample of 1591 queries): bp >= 0.6 alone 87.6 / 3.8 / 14.4 vs Fretline on the same sample 81.9 / 7.5 / 28.9; 'bp >= .6 AND sc >= .5' 85.3 / 3.1 / 14.4; 'Fretline AND bp >= .6' 76.1 / 2.3 / 10.3. i.e. a live Basic Pitch confirmation would beat the current detector on every false-alarm axis. NOT built live yet: webgl BP took ~0.11 s per second of audio on the phone (14 s for 123 s) but webgl failed once and CPU is ~0.8x real time; crediting a hit 0.5-1 s late needs retroactive credit after the step window closed (the hit pipeline sets state in several places); plan = opt-in experimental setting, single-note steps only, skip BP if busy/CPU backend, default OFF. Needs the owner's audio+reports to validate alignment first. Datasets available on Zenodo for more tests: IDMT-SMT-Guitar 7544110 (1.3 GB zip), EGDB 12674910 (1 GB), GAPS 17152440 (7 MB), GOAT 17811453, ToqueFlamenco 804050 (13 MB), EGSet12 11406378 (110 MB). sw cache v134.
- v1.143: **Share lesson audio** (owner agreed to send recordings). Results card (needs Settings > Basic Pitch second opinion on, since that is what records) gets '🎧 Share lesson audio': `bpWavBlob()` builds a 16-bit mono 22.05 kHz .wav from `bpRec.chunks`; `shareAudioFile()` uses navigator.share(files) / new native `SongFilesPlugin.shareFile({name,b64,mime})` (Java, same FileProvider cache path as shareText; needs the new APK) / download. Report now has 'Audio of this run: N s ... (run HHMM)' and each row ' · @12.34s' = seconds into the audio where the step was expected (d.tw - bpRec.t0) so steps can be located in the file; file name fretline-audio-<lessonid>-<HHMM>.wav. Lab test_bp_shadow checks wav header/size, button, @ column. facts.js entry added. Proxy check this evening: reachable zenodo.org, huggingface.co, pypi.org, github.com/raw.githubusercontent.com (partly); NOT reachable: arxiv.org, kaggle, tfhub, storage.googleapis.com, cdn.jsdelivr.net (curl), unpkg, figshare, osf.io, ismir.net, semanticscholar. sw cache v133.
- v1.142: Basic Pitch alignment uses all steps (singles, chords, strums) and the report prints `bp@+NNms` = where bp heard the strongest target note relative to the expected moment (raw, before correction) so drift is visible. Evidence (reports v1.141): Arpeggios in E major 96/160, 'aligned -397..610 ms' (range too wide = alignment unreliable when most steps are wrong notes); all misses at upper-position steps (C#3 A4, G#3 D6, C#4 G6, E4 B5 etc.) where bp also names other pitches at 0.9+ = he really played other notes (or lagged one note); same pattern in D major arpeggio steps 36-48. Strumming in C major 147/160, aligned 0..0 (no single steps then): misses agree with bp (level ~1-15, bp .1); bp scores for repeated same-chord strums are low (.1-.3) even for hits because bp reports NEW onsets and the notes are already ringing: bp is not informative for repeated strums. #31 F MISS had bp .76/.86 on two strings (maybe wrongly missed). sw cache v132.
- v1.141: Basic Pitch second opinion now also covers strum steps (uses `snotes`; before, the owner's 'Strumming in A minor' 147/160 report said '0 steps'). Strum rows print one bp onset score per string; no doubt flag for strums. Strum report observations (v1.139): all 13 misses are mostly the first strum of each F bar (#8,#9,#24,#56,#72,#88,#120,#152: levels 6-29 vs hits 40-85) = chord change late, not a detector issue as far as known. sw cache v131.
- v1.140: **Basic Pitch alignment fix.** Owner's 2-min 'Arpeggios in D major' report (133/160, 14.3 s bp webgl) showed bp agreeing for ~35 steps then 'doubting' nearly every hit; 'bp also' kept naming the previous step's note at 0.9+ while hit timings stayed +-70 ms, i.e. the recording was drifting against the step clock (most likely dropped ScriptProcessor buffers -> recording shorter than wall time), NOT bad hits. Fixes: (1) `bpRec` fills dropped audio with silence using `ev.playbackTime` gaps (`bpRec.gap`, shown in bpInfo 'filled X s of dropped audio'); (2) bpAnalyse aligns each step by data: finds where bp heard the step's own pitch (>=0.6, +-0.6 s), shift = median of the offsets of steps within +-8 (>=3 found), bpInfo shows 'aligned a..b ms'. Doubt flags are still non-scoring. Lab test_bp_shadow ok (aligned 0..0 on short clip). Unverified on a real long run: next report should show 'filled'/'aligned' numbers and far fewer doubts. Earlier v1.138/1.139 doubt statistics from short runs remain valid. sw cache v130.
- v1.139: **pitch-tracker hits must come from a pick inside the step's window.** Evidence: owner's E minor pentatonic report (15/15, webgl bp worked 5.8 s/31 s): #14 D4 'okay -540 ms, picks 0/0' (bp 0.95) was credited by path 1 using a pick from before the window opened (`fresh` only checked pick>lastHitAt and <700 ms old); #13 D4 +108 ms 'heard nothing' bp 0.17 = false hit. Fix: `fresh=legato||(pick>G.lastHitAt&&now-pick<700&&(G._winAt==null||pick>=G._winAt-30))`. Tests unchanged (sim 17/17, double stops 95/96, one-note 33/34); GuitarSet compare identical before/after (69.3% recall now vs 83.9% 'no fresh pick' row, ring FA 30%). Bp data from 4 more reports (C major scale 32/32 all bp>=.94; G-C-D fingerpicking 59/64; Am-Em-C 59/64 and 46/64): misses and the 46/64 run's first 16 steps (level 1-4 vs cutoff 7.1) agree with bp (barely played); late hits (+100..+250 ms) with bp<0.5 recur (#9 G3 +111 bp .12, #24 A2 +253 wrong:absent, #57 A3 +152 wrong:D3 bp .28); runs of +53..+87 ms hits with bp .2-.4 and 'bp also' = neighbour step's note suggest bp alignment offset or genuinely late credit; unresolved. sw cache v129 (unchanged).
- v1.138: **Basic Pitch flags doubtful hits (owner's first full bp report: A minor pentatonic shape 2, 24/34, CPU backend after webgl failed, 22 s for 27 s of audio).** Findings: every MISS had bp < 0.33 (agrees); all 14 hits within +-100 ms had bp >= 0.89; 5 of the 10 hits outside +-100 ms had bp < 0.55 (#3 D4 +220 ms heard G3 bp 0.12; #18 D4 bp 0.52 with D#4 0.86; #21 D3 -130 ms bp 0.19 with B3 0.96 = he played B3; #27 E4 +204 ms bp 0.20; #28 A4 bp 0.45), i.e. ~5 of 24 credited hits were wrong notes (a semitone or other neighbour) accepted late. Detector features (note score .70-.87, picks, level) did not separate them from true late hits, only bp did. Also 'heard nothing' hits (#0,#4,#5) all bp>0.9 (tracker misses real notes, spectral score catches them). New: after analysis, single-note HITs with bp[0] < 0.5 get `d.doubt` (report: ' · BP DOUBTS THIS HIT') and the results card says 'It doubts N of your hits: steps #..., Your score is unchanged.' (`G.bpDoubt`). Score NOT changed yet. NEXT: more reports to confirm the pattern across lessons, then consider a live veto for late hits (needs the causal window and speed: CPU ~0.8x real time on the phone is too slow to run per step; maybe a smaller/faster model or WASM backend) or re-scoring after the run. sw cache v128.
- v1.137: **Results card fits a phone held sideways; Basic Pitch status on screen.** Owner: in landscape the bottom row of the results pop-up was cut off/unclickable (my added Most-missed + Share rows made it too tall). Card is now `.resCard` with `.resL` (title, stars, %, details) and `.resR` (missed bars, Basic Pitch status `#rBp`, report buttons) side by side under `@media (max-height:560px) and (orientation:landscape)`; the button row is sticky at the bottom; missed-bar buttons are compact (label 'Most missed bars (tap to practise):', 'Bar 2 x3'). `bpStatusUI()` shows 'Basic Pitch is listening... NN%. Wait for it to finish' / 'finished' / failure reason on the results card (owner saw no status before; it was only in the copied report). Checked at 780x360 and 390x780 in desktop Chrome. Owner said he 'shared the new report' but none arrived in chat (nothing attached): ask for it again after this version. sw cache v127.
- v1.136: **Basic Pitch shadow mode on the phone.** Owner's first report (A minor pentatonic, shape 1, 29/35, Samsung SM-S948U1): 'Basic Pitch ... failed: Failed to compile fragment shader' = the TF.js webgl backend does not work on the phone. `bpAnalyse` now tries webgl then cpu (`G.bpTried` shows what failed, header shows the backend used); header shows progress % while running. cpu in headless desktop: 17 s for 9 s of audio (phone will be slower: a 1-2 minute lesson may take minutes; consider a worker/wasm backend or analysing only part if too slow). Same report: Share fell back to the clipboard ('file sharing not available') because the phone still has the old APK or shareText failed; the report text itself arrived. Review of that report: 29/35; several HITs with picks 1/0 or 0/0 and 'heard' never showing the target (#16 D3 heard B2, #18 G3 heard E2, #21 A3 picks 0/0 -180 ms, #24 G3 heard E3 -180 ms): need the bp columns to tell real plays from ring. sw cache v126.
- v1.135: **Native share sheet for the report (Android app needs the new APK from CI).** SongFilesPlugin.java: new `shareText({name,text})` writes the report to cacheDir/shared and opens ACTION_SEND (text/plain, EXTRA_STREAM via the existing FileProvider `${applicationId}.fileprovider`, cache-path in file_paths.xml covers it). `shareReportFile` in the app calls `sfPlug().shareText` and returns 'shared'; on an old APK (method missing) or any failure it falls back to the v1.134 clipboard copy. Java only syntax-checked with javac (missing-symbol errors expected); first real test is on the phone after CI builds the APK. sw cache v125.
- v1.134: **Share report fix.** Owner: the share button said 'Shared / saved' but nothing was in the clipboard / arrived. Cause: the Android web view has no file share (navigator.canShare files false) and the download fallback fails silently, yet `shareReportFile` returned success. Now it returns 'shared' / 'downloaded' (browser only; skipped when `IS_APP`) / 'none', and on 'none' the button copies the report to the clipboard and says so (or shows a select-all text box if the clipboard is blocked). Button renamed 'Share report'. A real Android share needs a native method (SongFilesPlugin or a new plugin using an ACTION_SEND intent): not built. sw cache v124.
- v1.133: **Basic Pitch second opinion, shadow mode (owner approved the staged plan).** Settings checkbox 'Basic Pitch second opinion (test...)' (`settings.bpShadow`, id sBp, default OFF). In Play mode `update()` calls `bpRecStart()`: a ScriptProcessor tapped off `micSrc` records the mic box-resampled to 22.05 kHz in memory (`bpRec`); `diagEnd` now stores `d.tw` (wall time the step's target moment occurred). `finish()` calls `bpAnalyse()`: lazy-loads lab/basic-pitch/basic-pitch.bundle.js + model.json (TF.js, webgl then cpu), runs the whole recording (not the causal 2 s window the GuitarSet study assumed, so it is an upper bound) and fills `d.bp` (onset score per target note, window -0.2..+0.3 s around the step) and `d.bpx` (a loud non-target note >=0.5). `diagReport()` prints a header line (status/backend/time) and ' · bp 0.81/0.77 · bp also C4 0.62' per step. Never changes hit/miss. Runs on the main thread after the run (headless software GL: ~30 s for 9 s of audio; phone speed unknown, reported in the header). Test: tools/lab-tests/test_bp_shadow.py (uses a GuitarSet clip as the fake mic, so HIT/MISS there are meaningless). NEXT: owner plays several lessons with it on and sends reports; compare HIT/MISS vs bp columns (ring-through = picks 0/0 hits with low bp, wrong-note hits with 'bp also'); if good, fuse (logistic regression in guitarset_compare.py gave recall 89% / semitone 3.4% / ring 21% vs 83/8/30 for Fretline alone) with a causal 2 s window in a worker. sw cache v123.
- 20 Nov (no app change): **Basic Pitch evaluation on real guitar.** Network now allows zenodo.org, huggingface.co, cdn.jsdelivr.net. GuitarSet (Zenodo 3371780: annotation.zip + audio_mono-mic.zip) downloaded to /tmp/gs (not in repo). Basic Pitch ONNX model (basic_pitch/saved_models/icassp_2022/nmp.onnx, 230 KB, Apache-2.0) comes from `pip install --no-deps basic-pitch` + onnxruntime. Tools: tools/detection-tests/guitarset_bp_eval.py (BP alone) and guitarset_compare.py (Fretline detector in the page vs BP, same questions: annotated note onsets = positives; neighbouring semitone and still-ringing pitch = negatives; dumps /tmp/gs_rows.json). Results (note level, 24-36 clips): Fretline v1.126 recall ~72-83%, semitone accepted ~5-8%, ringing accepted ~28-30%; BP alone (full clip, onset>=0.5) 81/2.4/22; with a causal 2 s window ending 0.25 s after the note, Fretline features + BP score in a logistic regression (5-fold CV, th 0.6): recall 89%, semitone 3.4%, ringing 20.9% (better on all three). Caveats: per-note not per-step, clean studio mic, BP needs ~0.25 s extra latency + inference time; not run in the app. Plan: shadow mode first (BP runs in the background, its verdict printed in the detection report, never changes hits), ONNX in a Web Worker (the Lab ctc worker failed on the owner's phone, cause unknown), lazy-loaded and off by default; only then fuse. Harness note: 'before v1.126' row in guitarset_compare.py ignores the old 'rose' condition, so it overstates the old ring acceptance.
- v1.132: **UI pass (owner agreed to all six).** (1) Song screen: capo/tuning/simplify/strum selects moved into `#optPanel` behind `#optBtn` '⚙ Options' (dot via `.set` when any is non-default, updated in `updateButtons` + change listeners); ids unchanged so other code still works. (2) Bigger touch targets: top-bar buttons/selects min-height 40, speed -/+ 44x44, Play/Wait 40. (3) Lesson start card (`#intro`) is now a bottom card over a transparent overlay (highway visible), tip clamped to 2 lines, tap `#iTip` for the rest. (4) Hit pops append ' · early' / ' · late' when the timing is 60 ms or more off (`G.hitOff>0` = late). (5) Course list: overall progress bar, per-unit bars with a tick when finished, auto-scroll to the next lesson once per tier (`#nextLesson`); the Continue button already existed. (6) Left-handed mode (`settings.lefty`, id sLefty): `drawFretboard` mirrors the board (nut on the right; helpers `fx/cn/dir`), `drawHand` mirrors the hand with its numbers drawn unmirrored; highway untouched. facts.js entries for Options and Left-handed. Screenshots checked at 900x460 in a desktop browser only. Ideas not done: tidy the 'Band' button label on short screens, make the start card dismissible by tapping the highway. sw cache v122.
- v1.131: **Chord memory drill, slash chords, strummed progressions.** (1) New unit 'Chord memory' (c10c-1..5, lesson flag `recall:true`, passed to the def by `lessonDef`): `recallHide()` (G.def.recall and not peeking) makes the highway chord boxes show only the chord name + '?' while the step is pending (`st===0`); a hit step shows its frets in green; the finger guide / bottom guide / fretboard are skipped while hidden. Round `#peekBtn` (bottom right, shown by `peekUI()` when the lesson is a recall one) shows everything for 4 s (`G.peekUntil`) and counts `G.peeks` (reset in `resetRun`/`openSong`, printed on the results line). Detection is unchanged (events still carry their shapes). (2) Slash chords: SHAPES gained G/B, D/F#, C/G, C/E, Am/G, A/C#, E/G#, F/C; `chordShape` checks the exact name in SHAPES before splitting off the bass. Lessons c10b-7 (G D/F# Em C) and c10b-8 (C G/B Am Am/G F C/E F G). (3) Strummed lessons c10b-9 (50s, folk pattern), c10b-10 (Am G F E, steady eighths), c10b-11 (blues in A with muted backbeat). Test additions in test_chord_lessons.py (recall hide/peek, slash shapes). Not verified on the phone. sw cache v121.
- v1.130: **Chords section expanded (core course).** New unit 'More open chords' (after Chord changes): c6b-1 dominant 7ths (A7 D7 E7), c6b-2 G7/C7, c6b-3 sus2/sus4 on A/D, c6b-4 Dsus4/Esus4/Gsus4, c6b-5 major 7ths, c6b-6 minor 7ths, c6b-7 add9 (G Cadd9 Em7 Dsus2). New unit 'Chord progressions' (after Barre chords): c10b-1 12-bar blues in A, c10b-2 50s (C Am F G), c10b-3 Am G F E, c10b-4 G Em C D strummed, c10b-5 Bm/F#m barres, c10b-6 Bb/Eb barres. New `progL(chords,per,bpm,bars)` plays chords in the written order (chordsL shuffles for drills). c10-1 'C and F' retitled/tip rewritten for the easy F (v1.128). All shapes come from SHAPES. Test: tools/lab-tests/test_chord_lessons.py. Ideas not done: slash chords (G/B, D/F#), more strumming patterns per new progression, chord-name quiz. sw cache v120.
- v1.129: **Owner's four suggested improvements.** (1) Share: results screen has '↗ Share as .txt file' (`shareReportFile`: navigator.share with a File, else a download), next to Copy. (2) Slow-down offer: `slowCheck()` called on each miss; 4 misses in a row (`G.missRun`, reset on a hit/run) in Play mode at speed >70% and no loop -> floating `#slowOffer` 'Slow to 70%' (once a minute, auto-hides 9 s). (3) Most missed: `missedBars()`/`showMissed()` fill `#rMissed` on the results screen with the 3 bars missed most; tapping one resets the run, loops that bar + the next (`setLoop`), speed <= 80%, and starts Play. (4) Loop: `#loopBtn` in the player controls; `G.loop={a,b}` in beats; tap = 2 bars from the current bar, again 4, 8, off; `update()` wraps `seekTo(G.loop.a)` when the clock reaches b (stopVoices first); cleared in `openSong`. Loop practice counts hits/misses cumulatively (no per-lap score yet). Tests: tools/lab-tests/test_loop_missed.py (loop wrap, missed buttons, slow offer; Play start after 'practise' not exercised in the test because the mic is denied there). facts.js entries for all four. sw cache v119.
- v1.128: **Easier F by default.** Owner: use the easier form whenever a chord has a barre version, F the example. SHAPES: F xx3211 (was 133211), Fm xx3111, F7 xx1211 (all 4 top strings; F5 unchanged). `chordFingers`: new mini-barre rule (`mini`): at fret 1, 2+ notes share the lowest fret, it reaches the high e, every string from there up is fretted and something higher is fretted -> the index covers them (xx3211 = 0,0,3,2,1,1 fingers; A 2-2-2 and D 2-3-2 are not mini-barres). Other barre chords (B, F#, C#, G#, Bm, Cm, Gm...) have no easier standard form and are unchanged; E-shape fallback for unknown chords unchanged. standardShapes (v1.127) now converts to these. test_fingering.js still lists the old F (133211). sw cache v118.
- v1.127: **Standard chord shapes in songs.** Owner: a song (Marlboro Man, Lab tab) showed F as 5-6-5 on e/B/G with fingers 1-2-3 and hand 'Fret 3' (tab notes taken as written; the fingering planner gives one finger per note and parks the hand to minimise moves), wanted the traditional F at fret 1. New `standardShapes(events)` (UI block, before `buildSong`): in `buildSong`, for songs (not lessons/generated, `settings.stdShapes!==false`) any step of 3+ notes (no tech/bend/strum/lead) whose notes all fit one chord named by `estChord` is replaced by `chordEvent(name)` (the SHAPES library: F = 1-3-3-2-1-1). Same pitch classes, so listening/chord match unchanged. Skipped when already low on the neck (max fret <=4) or the chord is not clear. Settings checkbox 'Standard chord shapes in songs' (id sStd, default on; applies next time a song is opened), facts entry. Triad lessons (genTriads) deliberately untouched. Not yet checked on the phone. sw cache v117.
- v1.126: **Owner's 20 Nov requests + detection tightening.** (1) Settings: 'Show what I'm playing in the strike zone' (`settings.played`, id sPlayed, default on) turns off the dashed green/red ring. (2) 'Then' chips in the finger guide show the FRET number (finger colour kept) instead of the finger number. (3) Lab: background stall hypothesis = Chromium intensive timer throttling (setTimeout chains run once/min after ~5 min hidden), so `listen` now yields with a MessageChannel (`yieldNow`) instead of setTimeout; worker onerror now logs file:line. Unverified on the phone. (4) Detection: reports of 4 lessons showed HITs with 'picks 0/0' around -400..-530 ms on repeated identical steps (a ringing chord/note jumped in strength and was credited as the next step) and some level-below-gate hits. `matchEvent` path 2 (strength jump) now also needs a pick (`max(onsetAt,pitchOnsetAt)`) after `G.lastHitAt` and >= `G._winAt-30` unless legato (`pickedHere`). Sim 17/17, test_double_stops 95/96, one_note_all_song 33/34 (unchanged vs v1.125). Simulator song_report_sim.py: SKIP/SEQ env, supports 2-note events `[m,s,m2,s2]` (synthetic samples do not reproduce ring-through; real reports did). Not changed: semitone-neighbour acceptance seen in Fur Elise (needs more evidence). sw cache v116.
- v1.125: **Faster lyric timing + the 'Man' fix.** (1) The mix listen and the singing-alone listen now run side by side, each in its own Web Worker (new lab/ctcworker.js: ort + fbank.js + the model bytes passed in; one session per worker; falls back to the old one-after-the-other path in the page if a worker cannot start, logged 'side-by-side listen not possible here'). The main-thread session is created lazily only for that fallback. Desktop: both listens in 20.3 s, same as one listen before. The phone report showed 68.8 s for the two listens one after the other (the phone was also throttled: 'lined up' took 14.8 s vs 1.7 s). (2) `tidyEnds(sec)`: owner: in 'Marlboro Man' held 'Marlboro' then 'Man' straight away, the display never reached 'Man' before the next line ('Mountains') took over. The last word of a line is now kept >= 0.35 s before the next line starts (and after the word before); logged 'N line(s) had a last word too close to the next line'. Unverified on the phone. Report header 'page v1.125'. sw cache v115.
- v1.124 result (owner's phone, new APK): 'the model also listened to the singing alone' worked; the speech listen took 68.8 s (two passes) for 207.7 s of audio. 'Alone again…' moved from 2:27.8 to 2:10.5 and 'Mountains…' to 2:27.4 (no more squeezing). Weakest lines left: the last two 'Marlboro Man's (heard -9.5 / -10.2, at 2:59.1 and 3:10.0). Owner's verdict on the playback still to come.
- v1.124: **Speech model also hears the singing alone.** Owner's v1.123 report: every line shows 'singing 100%' at 2:07-2:28 (the owner says the lines ARE sung there, held notes, with instruments) but the model heard them badly (conf -5.1 and -7.9); so my 'unsung' guess was wrong and dropUnheard (needs singing<25%) correctly kept them. The 'Alone again' line is still squeezed at 2:27.8. Fix attempt: the model now also listens to the separated vocals and the two log-prob streams are averaged (`ctcLyrics(...,vox)`; `VOC16`, 16 kHz mono vocals: web path decimated from stem 3 in the chunk loop, native path via NEW `vocal16` field from NativeSeparatorPlugin.java: box-averaged mono 44.1k→16k per chunk; syntax-checked with javac only (missing-symbol errors expected, no syntax errors), CI builds the APK on this push, the phone needs that new APK). Without the new APK the Lab logs nothing about the voice and uses the mix only (r.vocal16 absent → VOC16 null). Report header now 'page v1.124'. Note: e2e.py riff check gives 8/64 in this workspace both before and after v1.116 (not a regression of mine; the documented 64/64 was an earlier setup). sw cache v114. NEXT if still squeezed: window the vocals-only listen, or boost: add VOC-based blank prior.
- v1.123: **Owner's v1.122 run: the 'Alone again' line still sat at 2:27.8, right next to 'Mountains…' at 2:28.5.** Per-line confidence from the speech model (ctcalign.js now returns `c`, the best log-prob of each word's pieces) shows the lines at 2:07-2:29 and the last 'Marlboro Man's are heard worst (-6.6 to -9.2 vs -1.2 to -5 for the rest). Reading: the owner's sheet repeats a chorus (the lines 'Just cussin'…' and 'Alone again…' after the 2nd 'missin' you') that the song does NOT sing (the model heard nothing 2:06-2:30, a solo), so forced alignment has nowhere true to put them. New `dropUnheard(sec,log)`: a line with confidence < -5.5, < 25% singing in its window (VOC loudness phrases) and >= 3 words is LEFT OUT of the lyrics; every line is now logged as 'start · heard <conf> · singing <%> · text', and removed ones as 'N line(s) left out because nobody sings them there'. The Lab report header shows 'page v1.123' so a stale cached page is visible (v1.122's fixSqueezed gave no log line in the report: either the old page was cached or it had no singing to use). Not run on the real vocal envelope here. sw cache v113.
- v1.122: **Owner's v1.121 Marlboro Man run: the speech model works on the phone (11.2 s for 207.7 s of audio, 37 lines timed word by word; times match the owner's ear: 'Ain't much changed' 0:54.2, 1:47.5).** One bad spot: 'Alone again like that damn Marlboro Man' (2nd time) came out at 2:27.8, 0.7 s before 'Mountains in the background' at 2:28.5 (the model heard nothing at ~2:08-2:28 and dumped the line at the end of the gap; the real line is sung ~2:10). New `fixSqueezed(sec)` in stems.html: a line of >=4 words squeezed below 0.28 s/word is moved onto the vocal-envelope phrases (VOC, `vocalPhrases`) found between the previous line's end and 0.6 s before the next line, spread by syllables; logs 'N line(s) the model could not hear were placed by the loudness of the singing'. Needs VOC (the singing envelope; phone: from the APK's `vocal`). Unit-checked in node only. sw cache v112.
- v1.121: **Lyrics timed by a speech model (Lab).** Owner's data showed the loudness method placing lines 3-8 s off (e.g. 'Ain't much changed' at 0:47.9, really ~0:54). GitHub release assets ARE reachable from this workspace (Hugging Face is not): downloaded sherpa-onnx's NeMo Conformer-CTC small (English, int8, 46 MB, Apache-2.0/CC-BY-4.0 NeMo) and proved it hears the words in the full mix (no vocal stem needed). New files: lab/ctc_en.int8.onnx (COMMITTED, 46 MB; served by Pages, not in the APK because the app loads the hosted web page), lab/ctc_tokens.txt (1025 pieces, blank=1024), lab/fbank.js (kaldi-style 80-bin log-mel in JS; matches kaldi_native_fbank to 7e-5), lab/ctcalign.js (greedy word-piece tokenising + CTC Viterbi forced alignment of the exact lyric text; per-word start/end, 40 ms frames). In stems.html `ctcLyrics()` (model cached in Cache Storage 'fretline-models'; 30 s chunks, per-chunk feature normalisation; onnxruntime-web wasm) is tried first in saveRecSong with the band+guitar mix; any failure falls back to the old `alignLyrics`. Test tools/lab-tests/test_ctc_lyrics.py (Marlboro Man mp3 at /tmp/mm.mp3): 20 s for 208 s of audio on the desktop; lines land at 13.5, 18.2, 25.0 … 'Ain't much changed' 54.2 (owner heard ~53-54), 'Too much pride' 60.9. LIMITS: the sheet must contain every sung line, repeats written out (a missing repeat makes the aligner use the wrong occurrence); English only; the model also needs a first-time 46 MB download on the phone (Settings › storage). Unverified on the phone (speed with single-thread wasm; chunk-edge effects). Also learned: Fretline's 'left' clock starts at bar 1 (recOffset 0.68 s) and the song is 115 bars = 193 s although the mp3 is 207.7 s. sw cache v111.
- v1.120: **Pause for Listen + drag the highway.** Play already paused/resumed in place; Listen was 'Stop' (reset to the start). Now Listen toggles ❚❚ Pause / ▶ Resume (also after the app was hidden, which pauses); ⟲ resets. `resumeFrom()` re-aims the Listen/effect/band indexes at the clock; `seekTo(beat)` sets the clock, marks earlier steps state 3 (skipped, not misses), clears results. Drag: pointer events on `#cv` (touch-action none): after 8 px sideways it pauses, moves the clock by dx/ppb0 (drag right = back), and resumes on release if it was playing (so it also works while paused). Test tools/lab-tests/test_pause_drag.py passes. Facts: 'Drag the highway' (id cv), Play/Listen entry reworded. sw cache v110. Unverified on the phone (finger drag, recorded-audio songs: recTick restarts the recording at the new clock).
- v1.119: **Lyric timing log (Lab).** Owner sent the Marlboro Man mp3 and says the lyrics fall behind, catch up, fall behind by different amounts (so NOT a constant lag: an alignment problem, not the playback clock; playback maps seconds→beats linearly with recOffset). Could not reproduce: the workspace has no real vocal stem and the mix envelope is not a vocal envelope; no lyric text. Tried 'groups between trusted anchors' (reset drift at pauses): worse on the synthetic test (median 1.1 s vs 0.02 s), so REVERTED; v1.117's global syllable→note-start DP stays. The Lab now logs, after timing lyrics, 'note starts found for N syllables' and each line's start time + first words, so the owner can report which line first goes wrong and I can see whether the note-start count is far from the syllable count (the likely cause on real singing: legato notes without dips, backing vocals). NEXT: use that report; ideas: weight note starts by loudness peaks, use the vocal's pitch changes as extra note starts, or Whisper word timestamps. sw cache v109.
- v1.118: **Flute vocal guide removed; lyrics nudge added.** Owner asked to remove the flute: Settings › Singing no longer has the vocal-guide switch/volume (facts entries removed), `voxActive()` is permanently false and the flute font is never loaded (the old code is left in place, unused). The three 'where the melody comes from' switches stay. Owner's re-test of v1.117: lyrics STILL fall behind the singing. Not reproduced (no real data here). New Settings › Singing slider 'Lyrics earlier / later' (-3..+3 s, `settings.lyrNudge`, applied in `songLyrics()`, same for every song) as a stop-gap and a way to measure the lag. Suspects for the lag if it grows over the song: the beat clock is linear (fixed bpm) while the recording's tempo wanders; or the vocal envelope vs audio offset. Ask the owner whether it is a constant lag (nudge fixes) or grows with time. sw cache v108.
- v1.117 (analysis, no code change): **why the real-stem score is stuck at F1 .38.** Error breakdown on TYSK (first 60 s, CLEAN): 328 notes found vs 209 truth; of the 225 wrong ones 126 are at a true onset but another pitch (the truth tab is a single-note melody, so extra notes the recording really contains - chords, bass, ringing strings - count as errors), 55 have no truth onset nearby, 25 are octave errors. Of the 106 misses, 70 have a different pitch at that onset, 29 nothing. Raising hiMidi to 84 changed nothing (F1 .381). RAW Basic Pitch recall is .59 and cleanup trades it for precision. Conclusion: the metric is partly unfair on a real mix (truth is incomplete), and further gains need a better model or a truth with ALL notes played, not more cut-off tuning. Do not re-tune cleanNotes on TYSK alone.
- v1.117: **Lyric sync follows the singing's note starts (Lab, `alignLyrics`).** Owner's Marlboro Man report: lyrics lagged from ~2:20 then caught up, word lengths ignored. Cause: the old version shared each line's time by syllable COUNT, so a held word or uneven delivery shifted everything until the next pause. Now `vocalOnsets` finds note starts (quick rises of the vocal loudness + phrase starts) and a dynamic programme matches every syllable, in order, to one onset (cost: distance from the expected index, skipped onset .3, skipped syllable 1.5, line starts prefer onsets after a pause); unmatched syllables are interpolated; word length = start to next word. Falls back to `alignLyricsOld` if too few onsets. NOTE: the first prior (time-based) drifted badly; the index-ratio prior (onsets/syllables) fixed it. New test tools/lab-tests/test_lyrics_sync.js (node; synthetic envelope with held words/pauses; `HARD=1` adds merged syllables, spurious bumps, miscounted syllables): median word error clean 2.3 s→0.02 s, HARD 2.2 s→0.17 s (old vs new). Unverified on real singing; needs owner retest of Marlboro Man (re-run the Lab with the lyric sheet). sw cache v107.
- v1.116: **Lab note-finding scored and tuned (no-sheet path only; `cleanNotes`).** New tools/lab-tests: `make_score_audio.py` (plays the Midland tab's Lead+Rhythm tracks with a plucked-string synth → /tmp/score_gtr.f32 + /tmp/score_truth.json), `score_transcribe.py` (RAW Basic Pitch vs CLEAN, hit/precision/recall/F1 at 50 ms, `DATA=tysk` for the real stem), `tune_clean.py` (coordinate search over the cleanNotes cut-offs, objective 0.6·F1 real + 0.4·F1 synth). Findings: Basic Pitch alone on the clean synth gets F1 .86; cleanNotes was throwing away strummed chords (max 2 notes per pick): F1 .53, recall .37. Tuned `P` in cleanNotes (now an overridable object `window.CN_OVR`, attack curve cached on the audio array): minDur .06, hiMidi 76, pickWin .09, maxPerPick 6, ampRatio .7 → synth F1 .83 (recall .75), real TYSK stem unchanged at F1 .38 (precision .35→.31, recall .42→.49). Real-world numbers are poor (F1 .38): Basic Pitch hears ringing strings; the real score is the thing to improve next. Caveats: only ONE real song (TYSK, Demucs stem) and a synth were used, so this may be over-fitted; synthetic audio is easier than a real recording. sw cache v106.
- v1.115: Facts only. Owner kept Add a song and the Lab separate (asked not to merge them) and wanted the difference explained: new Facts items "Add a song or the Lab: which one?" (Lab section), "MP3 and other recordings" (Add a song section); Lab "What it does" no longer says Settings › App (Lab is on Home since v1.113). Add a song cannot read audio; only the Lab can. sw cache v105.
- v1.114: **Lyrics in the Lab (line-level sync to the singing).** Owner asked to attach a lyrics sheet and whether the AI can sync it to the vocals. Lab: new "Add the lyrics (optional)" box (`#lyr`, `#lyrFile` .txt/.lrc/.cho). The split now also keeps a 10 ms loudness envelope of the **vocals stem** (web runtime: from the model output; native: the plugin returns a new `vocal` field, so **needs a rebuilt APK**; old APKs log "lyrics: not timed… needs the latest update"). `alignLyrics(text,env,bpm,b0)` in lab/stems.html: `vocalPhrases` thresholds the envelope (18% of the 95th percentile, merges gaps <0.25 s, drops <0.15 s) into singing segments; lines get singing time by syllable share (`sylCount`), then a DP pairs line starts with phrase starts (after ≥0.5 s pause) in singing time (unpaired cost 2 s, max 3 s); words share their line by syllables. Output: `def.recLyr` (seconds, so the tempo editor can retime) and `def.lyrics` (beats, shown by 🎤 Sing); `recRetime` (index) and `retimeEvents` (Lab) rebuild `lyrics` from `recLyr`. Limits (be honest with the owner): line level not true word level; harmonies/loud backing vocals blur it; no manual nudge yet. Possible next steps: a ± seconds nudge, or Whisper word timestamps (large download). Tested: synthetic envelopes (4 phrases/4 lines exact; 6 lines/4 phrases subdivided; silent → none), envelope accumulation across overlapping chunks (node sim). NOT tested on a real recording or the real model. sw cache v104.
- v1.113: **Home buttons tidied; Lab moved out of Settings.** Owner asked for the Lab to live on the home page and for the four buttons to sit flush. Header is now the name + `#btnSettings` (⚙ Settings) (+ Install when offered), and a new `#homeNav` grid of 4 equal buttons sits under it: 🎚 Tuner (`#btnTuner`), 🧪 Lab (`#btnLab`, goes to lab/stems.html), 🎓 Tutorials, 📖 Facts. The Lab link was removed from Settings › App (HANDOFF mentions of "linked from Settings › App" are out of date). Checked at 360 px. facts.js: `btnLab` added to the Lab "What it does" item. sw cache v103.
- v1.112: **My Songs cleanup.** (1) "Find more free music" is a collapsed `<details>`. (2) Filter chips (All, Recordings, Tabs, Chords, Files, Generated, Library; only kinds you have) + search box when >10 songs + sort select (Newest, A to Z, Recently played, Best score); chosen chip/sort remembered in localStorage `fretline:myView`. (3) ☆/★ pin to top (`fretline:pins`); last played time shown in each row's subtitle (`fretline:played`, set in openSong). (4) Delete: still two taps (✕ then Delete) but now soft: `delSongs(ids)` removes the song, shows an Undo bar (`#undoBar`, 8 s); recording audio cache files are only deleted when the bar expires (`flushUndo`). Select mode (`#mySelBtn`) ticks several rows and deletes them together. (5) Rows show tempo for recordings in the subtitle; the ♩ button moved to the song screen as `#tempoBtn` (only for recordings in My Songs; saving a new tempo reopens the song). Progress per song = best score at right (existing) + played time. facts.js updated (test_facts passes). Helpers live just above `renderList()` (`myView`, `myPins`, `myPlayed`, `agoText`). sw cache v102.
- v1.111: **Home header overflow fix.** Adding the 🎓 Tutorials button made the home header wider than a 360 px phone, so Settings was pushed off screen. `header` now wraps (`flex-wrap:wrap`, h1 `flex:1 1 90px`), so all buttons stay visible (second row on narrow phones). The tab row (Course…My Songs) already scrolled sideways; made touch scrolling explicit (`touch-action:pan-x`, hidden scrollbar). RULE: re-check the header at 360 px whenever a header button is added. sw cache v101.
- v1.110: **Free song library grown by 43 songs across genres** (309 → 352), each graded level 1-3 (easy to hard): Blues 6, Country & bluegrass 6 (+ a Travis-picking tab), Gospel & spirituals 6, Jazz & ragtime 6, Celtic & sea shanties 8, Latin & flamenco 5, Rock & metal original riffs 5 (tabs). Added in `library/index.json`; new Style options in `#libStyle`; library entries can now be `kind:'tab'` (getLibSong builds a tab def; green "T" icon). All are public domain (traditional or published before 1929) or original to Fretline; credit/licence shown per song. Owner is gathering Creative Commons links himself (e.g. Scott Buckley, CC-BY 4.0, cinematic orchestral, not guitar) for later; links to videos only need to be free to watch (we link out, never embed or host). Verified all 43 open in the player with events. Chord charts are simple progressions written from general knowledge, not checked against recordings: if the owner reports a wrong chord, fix it in index.json. sw cache v100.
- v1.109: **Back button fix.** Owner: back took them out of Fretline. Cause: `handleBack()` had no entry for the new Facts and Tutorials screens, and the Lab page (lab/stems.html) defined no `window.fretlineBack`, so the Android app (MainActivity: asks the page, moves to background if it returns false) left the app. Now facts→factsBack, tutorials→tutBack (the Tutorials detail goes to the list first), and the Lab returns to Fretline's main page, except while a split runs (KA_ON) when it returns false so back backgrounds the app and the work continues. RULE: every new screen must be added to the `backs` map in handleBack. sw cache v99.
- v1.108: **Tutorials: the full first set (10).** `tutorials.js` now has Bends, Hammer-ons, Pull-offs, Slides, Vibrato, Palm muting, Arpeggios, Scales, Barre chords, Strumming patterns (owner approved the tone after the Bends fixes). Each has what/how/show/mistakes/practice/note and optional `lessons:[ids]` (shown as buttons "Lessons that use it"; the reverse link from a lesson to its tutorial is NOT done yet). **Palm-mute mark added**: tab `0*` (an asterisk after the fret) sets `note.pm`; the highway draws a "PM" label, playback makes the note shorter (0.12 s), hint says to rest the picking hand by the bridge. **Parser gotcha**: tab lines with many `~` fail isTabLine (needs 70% of characters to be `-0-9|:`), so use at most one or two `~` per held note in tutorial tabs. Still no video links (none verified free). sw cache v98.
- v1.107: **🎓 Tutorials page (first tutorial: Bends).** Home button `#btnTut` → `#tutorials` screen (list → detail, `‹ Back` goes list then home). Content in new `tutorials.js` (`window.TUTORIALS`: id,title,sub,what,how[],show,mistakes[],practice def (kind 'tab', src tab text, bpm 50),note, optional `video{title,url,by,licence}` rendered only when present). Added to sw.js CORE (cache v95) and facts.js (`btnTut,tutBack,tutPlay`). **No video link yet**: none could be verified as CC/free (Justin Guitar's lessons are standard YouTube licence), so never add one unless licence is verified. Owner to check the Bends tone before the rest (hammer-ons, pull-offs, slides, vibrato, palm muting (needs a highway mark), arpeggios, scales, barre chords, strumming). Fixed after owner question: bend direction (thin/high strings push up toward the ceiling, thick/low strings pull down) and clarified that a bend stays on the same string. Also added the 'about as far as the neighbouring string' rule of thumb (owner suggestion), flagged as a guide only. Next: lessons link to their tutorial.
- v1.106: **📖 Facts page (first piece of the owner's tutorials + facts plan).** Home header button → `#facts` screen (search box + the content of `facts.js`, 16 sections / 107 items: basics, home, song screen, every Settings tab, Add a song, library, generator, tuner, Lab, Open with, glossary). The content lives in the new `facts.js` (cached by sw.js, loaded on first open); every item lists the DOM ids it explains. **Drift guard: `tools/lab-tests/test_facts.py` fails if any button/input/select in the app is not covered by an item, so when you add a control, add it to facts.js.** The "Please read" disclaimer (practice aid, no responsibility for injury/misuse, as-is, results can be wrong, user responsible for rights to songs) appears at the top of the Facts page ONLY (owner's choice; the test counts it outside facts.js = 0). Wording is not legal advice: the owner should have someone read it. Plan agreed with the owner for next: a Tutorials page (one entry per technique with explanation, how the highway shows it, common mistakes, one generated practice example the highway can play, bends/slides/h/p/vibrato are already drawn and sounded; palm-mute mark still to add; a link to a free (CC / owner-checked) video per entry rather than an embed, because embeds are not licence-free and need the internet; lessons link to their tutorial; first batch of ~6, owner checks the first one for tone).
- v1.105: **the versions are named for what a guitarist plays**, because "Tab only" showing chords made no sense to a player: **Rhythm + lead** (was Chords + lead), **Rhythm only** (was Chords only), **Full tab** (was Tab only: every guitar part as the tab writes it, strums included), **Lead only** (just the lead line; only when the tab has a rhythm and a lead guitar). The Lab writes the new names; index.html `VER_NAMES` maps the old stored labels of songs already saved, and the picker shows a one-line explanation per version (`VER_INFO` + step count); the .mid files in the song folder use the new names too. No data migration needed. Tests: test_versions (picker text), test_songmidi (file names) pass.
- v1.104: the owner found a Lab bug: **after choosing the mp3, choosing the first tab / chord sheet makes the mp3 disappear and it has to be re-chosen.** Could not reproduce on desktop (the JS never clears `#file`; test with set_input_files keeps it), so the likely cause is Android reloading the Lab page while the file picker is open (it frees memory), which empties every file input. Fix: each pick (`#file`, `#sheetFile`, `#sheet2File`) is stored in Cache `fretline-incoming` (`…/__fretline/labkeep/<slot>`, list in localStorage `fretline:labKeep`) and `restoreKept()` puts them back at page start (status line and the report say "restored after a page reload"); the copies are dropped after a finished run or when a sheet is cleared. A race between two quick picks overwriting the list was found by the test and fixed (cache write first, then read-modify-write of the list with no await). Test: `tools/lab-tests/test_keepfiles.py`. **If the owner still loses the mp3, the report line "files: restored after a page reload" will tell whether a reload was the cause; if it is absent and the file still vanishes, the cause is something else and I need their report.** Also answered: "Tab only" shows chord blocks because `eventsFromNotes` now joins 3+ different notes struck within 1/8 beat (a strum stored string by string) into one step and any step with 3+ notes is drawn as a chord block; it is a timing/shape rule, not music theory (the names come from the chord file or from `chordChart` for imports).
- v1.103: the owner tried Midland "Put The Hurt On Me" with the right files: better, but **Tab only had chords in it and long silent gaps while a guitar is clearly audible.** Cause: v1.102 picks the Lead Guitar part as "the tab", and the lead is silent for 26.8 s (beats 32-78) and more where only the Rhythm Guitar plays; it also holds 21 chord stabs. Fix (Lab, file tabs with 2+ guitar parts and file timing): `fileSheet(…, allGuitars)` merges every guitar part (`src`/`partIdx` are now returned so it can be re-read), `makeSheetSong` lines that combined sheet up too (`PA`) and uses it for **Tab only** ("every guitar in the tab"), and the old single part becomes a 4th version **Lead only** ("just the lead line"). Chords + lead and Chords only are unchanged. Tab only keeps strummed chords because the tab's rhythm guitar strums; Lead only is the nearly chord-free one. Test on the real Midland tab + chords MIDI files with a guitar track synthesised from the tab's own notes (no real audio here): Tab only 498 steps, longest silence 3.2 s (was 26.8 s for the lead alone); Chords + lead 214 steps (longest 4.7 s); Chords only 78; Lead only 199. `tools/lab-tests/midland_versions.py` (needs /tmp/midland_gtr.f32 etc.; the recipe to regenerate is in its header). Regressions unchanged (sheet_merge, real TYSK 142 steps, test_versions). **Not tried on the real Midland recording yet.**
- v1.102: **Midland "Put The Hurt On Me" (tab MIDI with Rhythm Guitar 2008 notes + Lead Guitar 346 + bass + vocals, 103 BPM; chords MIDI is 2 tracks of triads + bass at 103).** The owner first sent the chords file by mistake (confirmed from its contents), then the right tab. The tab-only song they had made showed 1617 single steps with six stacked notes per strum: the rhythm part stores each strum string by string 1/48 beat apart and `eventsFromNotes` only grouped notes on exactly the same beat. Fix (core, `eventsFromNotes`): notes ≤0.03 beat apart in a chain spanning ≤0.125 beat with 3+ different pitches become ONE chord step (rhythm part 1617 → 391 steps, all 4-6-note chords; TYSK tab 773 → 754, six clusters were real strums). It also applies to the import screen. Lab part pick: with 2+ guitar parts and no tab info, prefer the part labelled Lead/Solo (so the lead line is the tab and the chords come from the chord sheet); the dropdown still lets them pick Rhythm. Not run on the real Midland recording (no audio here); regressions unchanged (strums 95/96, sheet_tab/chords/merge, real TYSK merge: 9 lead stretches, 81 chords, tab steps 65 → 61).
- v1.101: **songs moved out of localStorage (5 MB) into IndexedDB (the phone's own storage, ~2 GB allowed on the owner's phone). Web-only, no new APK.** New shared file `songdb.js` (`SongDB.load/songs/save/add/update/ids`): one record per song (JSON text, `_built` stripped) + an `order` record; only changed songs are written, removed ones deleted; refuses to save before it has loaded (so a slow open can never wipe the list); falls back to localStorage if IndexedDB is unavailable. Old localStorage songs (and any written by an old cached Lab) are moved over once at load, then the localStorage key is removed. index.html: the UI `<script>` is now `<script type="text/plain" id="ui">` and a small bootstrap at the end waits for `SongDB.load()` and then injects it as a real script (10 s fallback); `store.get/set('songs')` go to SongDB; `core` script untouched, so the Lab's text extraction still works. The import save uses `store.set`; the `visibilitychange` guard compares `SongDB.ids()` with `mySongs` and reloads if another page changed the list. Lab: `saveRecSong`, both retime writers and `pickSongDir` (now async) use SongDB; failure to save shows the reason on screen. Settings › App › "Saved data" now shows MB used, the allowance and the biggest songs. Test: `tools/lab-tests/test_songdb.py` (migration, 11.5 MB of songs across reloads, delete, edit, Lab ↔ main sharing); the old `test_storage_full.py` is gone. All earlier regressions unchanged (strums 95/96, sheet_*, versions, songfiles, songmidi, openwith, keepalive).
  **Bug found and fixed on the way: my version-bump one-liner `open('sw.js','w').write(open('sw.js').read()...)` emptied sw.js (v1.95–v1.100 shipped an EMPTY service worker: no offline copy and no Lab cross-origin-isolation headers). sw.js restored from v1.94 (now cache `fretline-v89`, `songdb.js` added to its file list). Never bump files with that pattern; read into a variable first.**
- v1.100: the owner said new Lab songs were not showing in My songs or saving to the folder, and the Lab's "Open Fretline › My songs" link was gone (that card only shows after a save completes, so the save was failing before it). I could not reproduce it with the real TYSK files plus fake plugins (saves, folder files and card all fine), so the leading suspect is **localStorage being full (~5 MB in this WebView; a three-version song is ~155 KB)**. Fixes: `saveRecSong` logs the storage size, retries without `recRaw`, and when it still cannot save says so on screen (and shows the card) instead of failing silently; an always-visible "Open My songs" link at the top of the Lab; Settings › App shows "Saved data on this phone" (MB used, biggest songs, warning above 3.8 MB); the main page reloads on `pageshow` from bfcache and re-reads the song list when it becomes visible, so a stale list can never overwrite what the Lab saved. Real fix still to do if this is confirmed: move song data out of localStorage (IndexedDB). Test: `tools/lab-tests/test_storage_full.py`. **Waiting for the owner's Lab report / Settings storage line.**
- v1.99: the owner (on the app) found no APK link: the in-app link used to show only when `NativeMic.outputRoute` was missing, and "Check for updates" only checks the web version. Settings › App now always shows "Download the latest Fretline.apk" in the app, with a line saying whether SongFiles / KeepAlive plugins are present (= whether the installed build is new enough). APK asset confirmed live: android-latest/Fretline.apk, 35 MB.
- v1.98: **"Open with Fretline" goes to the Lab (audio part needs the new APK).** Manifest VIEW filter gained `audio/*` (mp3 etc.); `MainActivity.MAX_BYTES` 20→40 MB. index.html `Incoming` handler: audio / MIDI / Guitar Pro / MusicXML files are put in Cache `fretline-incoming` (list in localStorage `fretline:labIncoming`) and the app goes to `lab/stems.html`; other shared things (text, chordpro, pdf, links) still go to the import screen as before, and MIDI no longer goes to the import screen from outside the app (the import button still takes MIDI). lab/stems.html: `labReceive(file)` puts audio in `#file` (title filled, Split enabled), MIDI/GP/XML in the first free sheet box (then the second; if both are full the first), text sheets in the textarea; it also reads the stash on load and listens to `Incoming` while the Lab is open. Test: `tools/lab-tests/test_openwith.py` (fake Incoming plugin; needs /tmp/tysk.mid, /tmp/tysk_chords.mid). Untested on a phone.
- v1.97: the owner confirmed song folders work but each had only one .json and asked for the original files. Web-only (no new APK). `sfMidi`/`sfMidis` write a standard .mid per song, and one per version (Chords + lead / Chords only / Tab only) for songs with `parts`, into the song folder next to the .json (chord names as MIDI markers; bpm and time signature included; hash suffix `|m1` forces one rewrite of every existing song). Songs made in the Lab since v1.94 also hold the exact tab / chord files that were uploaded (those can't be recovered for older songs, hence the generated MIDI). Test: `tools/lab-tests/test_songmidi.py` (notes read back with `parseMidi` = 471/453/773 as in the song).
- v1.96: the owner said they found no Fretline folder after v1.95. Most likely their phone still has an older APK (no `SongFiles` plugin), so Settings › App now always shows a "Song folders on the phone" box in the app: with the plugin it shows the checkbox, the last saved path and any error; without it, it says the app is older and links the APK. Waiting for their report on which they see.
- v1.95: **the Lab keeps working when you leave the app (needs the new APK).** `KeepAliveService` is a foreground service (type dataSync, notification "Fretline is working on your song" showing the status line, partial wake lock capped at 3 h) and `KeepAlivePlugin` (`start/update/stop/done`; asks for the notification permission on Android 13+, the service runs even if refused). lab/stems.html: the Run handler is now `runLab()` wrapped by `$('go').onclick`, which calls `KA.start`, forwards `status()` (every 2.5 s) with `KA.update`, and in `finally` calls `KA.done` ("Your song is ready" / "Fretline Lab stopped"; ready = `window.__labDone` set). Hint text under the button appears only in the app. Manifest: FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, WAKE_LOCK, POST_NOTIFICATIONS + `<service>`. Limits: the owner must not swipe the app away; in a normal browser tab nothing changes (browsers pause hidden tabs); a hidden WebView throttles timers (the Lab only has two rare ones, the heavy work is native / compute loops). Untested on a phone (the Java builds in CI). Test: `tools/lab-tests/test_keepalive.py` (fake plugin).
- v1.94: **a folder per song on the phone (needs the new APK; the web build does nothing without it).** `SongFilesPlugin.java` (`write({dir,name,text|data,mime})`, `removeDir({dir})`) writes to Downloads/Fretline/Songs/<song>/ through MediaStore (Android 10+, no permission; the app's own Downloads folder before that). index.html: `sfRun` reconciles after every `store.set('songs')` (hooked) and 4 s after start: new/changed My songs → `<title>.fretline.json` (hash kept in `fretline:songFiles` {id:{dir,hash}}), songs that vanished → folder removed. Duplicate titles get "(2)". A failed write isn't marked done and is retried. Settings › App: "Keep each song in its own folder" (`settings.saveFiles`, default on) + "Save all songs now". Lab (`saveRecSong`): sets `def.dir` and drops the tab / chord files it was made from (original MIDI/GP/etc. as given, or pasted text as Tab.txt / Chords.txt) into the folder via `SRCFILES`/`saveSources`. Audio (band + guitar WAVs) is NOT saved there on purpose: it's big and stays in the app's cache, and is cleared on delete as before. Songs made before v1.94 get only the .fretline.json (their source files weren't kept). Limits: after an uninstall/reinstall the phone no longer lets the new install delete the old files (Android rule), and the plugin can't be compiled in this sandbox, so **the Java is untested until CI builds it and the owner tries it**. Test: `tools/lab-tests/test_songfiles.py` (fake plugin; writes, no-op rerun, changed song only, delete removes folder, failure retried, switch-off).
- v1.93: **three switchable versions of a song from a tab + chord sheet** (Lab). One saved song gets `parts` = [Chords + lead, Chords only, Tab only] (versions that come out identical are dropped). On the song screen the 🎸 button opens "Which version?"; `usePart` for `kind:'rec'` swaps `events`, `recEvT`, `capo`, `strumAuto` from the part. `comboPair` returns null for rec songs; `recRetime` retimes every part against the same anchor so ♩ tempo changes keep all versions on the real recording times. Test: `tools/lab-tests/test_versions.py` (needs /tmp/tysk_merge.json from real_files.py auto): picker lists 3, switching 146→90→773 steps, step-time error ≤9 ms after tempo changes to 70 and 140. Regressions unchanged (strums 95/96, chord matching, sheet_tab 64/64, sheet_chords, sheet_merge). **Not yet tried on the phone.**
- v1.92: **tuning dropdown on the song screen** (`#tuneSel`, next to the capo; same as Tuner › Tuning).
- v1.91: **Lab: files in the second box, Auto merge** (chords strummed, the tab where it plays a lead line); real
  song checked with the owner's TYSK tab MIDI + chords MIDI (see the v1.91 section).
- v1.90: **Lab: a tab and a chord sheet together** (solo + strummed parts, see the v1.90 section).
- v1.89: **Settings › Mic & timing › Chord matching** (Strict / Standard / Beginner) and a wrong-chord check in
  every mode (see the v1.89 section).
- v1.88: **chord blocks on the highway** for chords found in a song's notes (see the v1.88 section).
- v1.87: **guitar tunings** in the Tuner (11 presets, string-by-string "tighten / loosen N semitones / cents",
  ✓ per string); the whole app, imports and the Lab follow the tuning; songs remember theirs and offer to switch.

**Confirmed on the owner's phone this session:** native separator works (4.5× faster); real-guitar guide works
("works as described"); the full "Thought You Should Know" song + MIDI run (before the v1.86 fixes) showed the
problems fixed in v1.86. **Not yet confirmed on the phone:** v1.81 note cleanup, v1.83–v1.86 sheet alignment on a
real run, v1.87 tunings/Tuner with a real guitar.

**Owner's test song:** "Thought You Should Know" (Morgan Wallen). The owner sent the MP3 and a Songsterr-style MIDI
(`…Thought_You_Should_Know_Tab-12-15-2025.mid`: Lead Guitar on 6 channels = 6 strings, E♭ tuning, 140 BPM, guitar
from beat 47; plus vocals over 5 channels, bass over 3, drums). Not in the repo (commercial). Reproducing needs them
re-sent; the model is mirrored in the `lab-model` release (run the manual "Mirror Lab model" workflow if missing).
With them, the full song makes 773 steps, 140 BPM, E♭, median 3 ms from the MIDI's timing.

**Open / to watch:**
- Ask the owner to remake TYSK in the Lab (Whole song + the MIDI) on v1.87 and send the Lab report + a detection
  report; check the song is saved as E♭ and the notes match what's heard.
- Tunings with a real guitar: Tuner string detection when a string is far off (nearest target wins; tap to lock).
- Transcription (no sheet) still has extra notes on fingerpicked parts and some bass bleed.
- Lyrics from chord sheets are dropped in the Lab; chord shapes in open tunings are standard fingerings.
- Older open items: false hits from sympathetic strings (no fresh single-note report since v1.66); first note of a
  song often missed; see the v1.66–v1.68 notes.

**Owner's preferences and style:** plain, practical explanations; they like seeing screenshots of layout changes;
they want detection to be strict (wrong notes must not count) and report results honestly. They prefer
one-tap/one-time settings and maximum screen space for the highway and hand. Standing permission: "Take any
necessary steps … to fix any of these issues in the way you think is best, so long as you're able to check that it
doesn't cause interference with anything that does work correctly I don't need to approve it", and push straight
to `main`. They test on the phone and send Lab reports and detection reports (often as .txt attachments).

## Picking up the conversation

**Latest: v1.95 (Lab keeps running in the background with a notification; same new APK) and v1.94 (a folder per song on the phone; needs the new APK from the android-latest release, built by CI on this push) is pushed. v1.93 (three versions per song, 🎸 button) was confirmed working by the owner.** Before that: v1.93 was pushed; the owner needs to try the Lab on the phone with both files (Auto) and switch versions.**

**Earlier (18 Nov, ~22:00 Central): the owner ran TYSK on the phone with the tab MIDI + chords MIDI in the Lab (v1.91, native separator 0.55× song length, 9 lead stretches / 81 strummed chords, report matches my run) and said "it plays well, I like the ability to switch strumming pattern in song". They asked for changing the tuning in song: done in v1.92 (see below).**

Before that (~21:45): v1.91. The owner sent a chords MIDI for TYSK (`…Thought_You_Should_Know_chords.mid`:
Track 2 = chords, Track 3 = bass, 143 BPM in the file, unquantised, guitar from beat 47.57; not in the repo) and
switched to Opus. Built: files in the second box, tempo hint, tuning / capo fixes, Auto merge. Waiting for the owner to
make TYSK in the Lab with both files (Auto) and send the Lab report.

Before that (~21:30): the owner asked for a chord sheet AND a tab on one song (play the chords and the solo) — built in v1.90 (Lab).** Agreed rules: tab wins where both play (switch for chords), Lab first, My songs without a recording later. Waiting for the owner to try it on a real song.

Before that: **chords vs single notes — done in v1.88 + v1.89.** The owner asked for chords
drawn as blocks (repeats as a strum pattern) and for partial strums / a brushed extra string to count, as a
setting. v1.88 = the drawing, v1.89 = the Chord matching setting + scoring. Waiting for the owner to try it on the
phone (a song with chords, each mode) and send detection reports; the report line shows "chords beginner/standard"
when not Strict. Still open from this idea: whether to name chords only when a sheet gives them (today: the
existing label, or none).

Earlier, the same evening:

The last exchange (18 Nov, ~20:00 Central):
1. After v1.87 the owner asked whether the **"Lead + rhythm"** and **"chords only"** options were removed. Checked:
   both still exist.
   - **Lead + rhythm** is the part picker for songs imported from a file with several parts (MIDI / Guitar Pro /
     MusicXML): "Which part?" on opening, or the 🎸 button in the player (`partChoices`, `comboPair`,
     `comboEvents`, `usePart`; v1.57–v1.58). Offered only when one part is mostly chords and another mostly single
     notes; lead where it plays, rhythm in the other bars.
   - **Chords only** is the import screen's **Notes** option "Guitar chords (strummed, with capo suggestion)"
     (`#impNotes` = all / top / chords; `partEvents` → `chordChart`).
   - Told the owner: Lab recording songs have a single part, so neither option appears for them; and since v1.86,
     per-string MIDI exports import as one part per instrument instead of six string "parts" (already-saved songs
     keep their old parts until re-imported).
2. The owner said they **have ideas related to Lead + rhythm / chords only**. I asked what the ideas are. **They
   haven't answered yet: start the new chat by asking for those ideas** (likely: bringing parts / Lead + rhythm /
   chords-only to Lab recording songs, e.g. using the MIDI's other tracks or a chord version of the guitar).

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

## v1.92: change the tuning in the song screen

`<select id="tuneSel">` in the player's top bar (after the capo; names without the bracket part; highlighted when not
standard). `syncTuneSel()` (called from `syncCapo`) fills / selects it. On change: stop playing if playing, `applyTuning(id)`
(sets `settings.tuning`, clears `_built`), then `openSong(def)` so the song is rebuilt in the new tuning
(`retuneEvents` for songs built in another one, same pitches on new frets; tab / strum shapes use `chordEvent`'s
tuning shift), and a hint "Tuning: … retune in the Tuner". It restarts the song from the start (position not kept).
Tested: a G-string fret-2 note → E♭ fret 3; drop D and open G leave the G string; playing stops; layout checked in
landscape (portrait not checked).

## v1.91: Lab — files in the second box; Auto merge; checked on the real song

- Second box takes a file (`#sheet2File`, `#sheet2Part`, `SHEETFILE2`, `setSheetFile2`, `readSheetFileInfo`); read as
  the other kind than the first sheet (`readSecond`). Track auto-pick: most 3+-note onsets (the chords track).
  `fileSheet(core,sf,partIdx,asChords,tunIn)` / `readSheet(core,text,type,tunIn)` take the file / tuning.
- **Tuning:** chords from notes are named by the shapes in the tab's tuning (notes moved by `tuningShift()` before
  `chordChart`: F# heard in E♭ = a G shape); a chord sheet in box 1 is read again in the tab's tuning.
- **Capo:** one song = one capo: the chord half is renamed for the tab's capo (`d = capoChords − capoTab`).
- **Order:** a tab *file* is lined up first, whole, by its own timing (no window search); its tempo goes to the chords
  file as `sheet.bpmHint` (extra tempos in `fitFileTiming`: hint ×1, ½, 2 ±0.5%). TYSK chords file: 143 BPM in the
  file, real 140; ±1% couldn't reach it → fit 70.64 (match 0.143); with the hint 70 (= 140 halved by chordChart),
  match 0.202. Checked against the tab's notes: chords agree 78% as placed; moved ½ cycle 42–44%, whole cycles ≤ 76%.
- **Auto merge** (`mergeAuto`, default of "Where both play at once"): per chord span (same chord in a row), the tab
  is a lead line if busy (≥ 1.8× median notes/s over spans with notes) or mostly not the chord's notes (< 50% of
  ≥ 4); a tab with notes in < half the spans is a solo-only tab → used wherever it has notes; a lead line may start
  0.4 s before its chord (pickup). TYSK (tab MIDI box 1 + chords MIDI box 2, or swapped): 9 of 90 chords become tab
  (0:01–0:03, 1:25–1:27, 1:30–1:33, 1:37–1:38, 2:47–2:49, 2:54–2:57, 3:23–3:25), 81 strummed chords (G D Am7 C shapes,
  E♭ tuning), 146 steps. Synthetic: solo 16/16 within 17 ms.
- Tests: `tools/lab-tests/real_files.py [auto|tab|chords] [swap]` (needs /tmp/tysk_full_gtr.f32, /tmp/tysk.mid,
  /tmp/tysk_chords.mid served on 8771 with the ORT files; prints chord-vs-tab agreement with `chords`; dumps the song
  to /tmp/tysk_merge.json). `/tmp/tysk_full_song.json` (the old truth) is from before v1.86: ~37% of its steps differ
  from today's file timing, so don't use it as truth for those parts.
- Regressions: sheet_tab (MIDI) 64/64, sheet_chords unchanged, sheet_merge tab/chords/auto OK.
- Note: `chordChart` rebases a file's chords to start at beat 0 (offset is free in the fit, harmless).
- Open: a real song with a separate short solo tab (text) — the window search (v1.90) is still the weak part.

## v1.90: Lab — a tab and a chord sheet on one recording

Lab › "Use a tab or chord sheet" now has a second box, **"And the other one"** (`#sheet2`, text only): one tab and
one chord sheet, in either box (two of the same kind: the second is ignored, logged). Both are lined up with the
recording and merged; saved as one `kind:'rec'` song (credit "a tab and a chord sheet").
- `makeSheetSong`: chromaFrames + attackCurve once (`cache`); the chord sheet is lined up on the whole recording
  first; then the tab **inside a time window** (`alignSheet(sheet,g22,win,cache)` via `sliceFA`), because a solo-only
  tab fits the strums too (its first test put the notes in the opening G strums).
- Window: typed times `#tabFrom` / `#tabTo` (m:ss or seconds) win; otherwise `findTabWindow` tries the tab inside
  every run of 1–8 consecutive chords (start −0.5 s, end +0.2 s), scores each by `tabQ` (mean note-name match at
  each step's time), keeps the shortest window within 0.03 of the best; accepts ≥ 0.45, else falls back to the whole
  recording and says so in the report.
- `mergeTabChords`: tab wins (default): chord / strum steps inside a run of tab notes (< 1.5 s apart, +0.25 s) are
  dropped; chords win (`#mergeWin`): tab notes kept only outside the chord sheet's runs (< 6 s apart), i.e. mostly
  none. "Follow the recording's strums" works with it (the strums in the solo are dropped).
- `prepPlaced` = the strums-from-recording + transposition / capo code that was inline before (single-sheet path
  unchanged: sheet_chords.py changes within 50 ms, sheet_tab.py riff 64/64).
- Test: `tools/lab-tests/make_solo90.py` + `sheet_merge.py` (G 2 bars, C, a 2-bar single-note solo, D, Em at 90 BPM):
  window found 9.8–15.5 s (true solo 10.0–15.0), match 0.85; the 16 solo notes within 2–17 ms, no chord inside the
  solo, G/C/D/Em around it; both orders; `FROMTO='0:09.8,0:15.5'` for typed times, `STRUMS=1` for strum mode.
  The merged song opens in the main app: chord blocks / strum pattern, then single gems, then D, Em.
- **Real-song check (18 Nov, 21:30; `tools/lab-tests/real_merge.py`, TYSK guitar stem + its MIDI):** the made-up
  song works, the real one does NOT yet. Steps 300–347 of the MIDI pasted as a solo-only tab (true place 82.3–100.4 s),
  chord sheet = the MIDI's own chord chart (102 chords, lined up in 2.7 s, but at +4 semitones: capo 4 vs the tab's 0,
  "different keys" in the report). (1) Automatic window: picked 118.4–130.7 s (match 0.52, barely over the 0.45
  limit): wrong; fingerpicked arpeggios in one key fit everywhere. (2) Typed window 81.9–101.0 s (exact): 35 of 48
  steps placed, 33 of 35 within 50 ms of the true time; 13 steps dropped by the path. (3) Typed 81–102 s (±1 s slack):
  41 of 48 placed, only 28 of 41 within 50 ms, the first notes crammed at the window start. So order-only alignment of
  a text tab on a real fingerpicked recording is fragile (it was tuned on synthetic riffs and strums). Ideas: match the
  tab's chord sequence to the chord sheet's names to pick the window (symbolic, robust), keep the chord-sheet window
  edges instead of padding, put the pick-attack bonus / min-length K to work in short windows, use the chord
  sheet's key shift for the tab, allow a MIDI / GP file as the second sheet (file timing is exact).
- Not done: a file (MIDI / Guitar Pro) as the second sheet; the solo before the first chord / after the last is only
  tried as one window; real songs untested (the window search assumes the chord sheet lines up well — a solo with
  no chord change at its start gets a start pad of 0.5 s only).

## v1.89: Chord matching setting; wrong strummed chords no longer count

Settings › Mic & timing › **Chord matching**: Strict (default) / Standard / Beginner (`settings.chordMatch`,
`#sChordM`, `CMODE` next to `matchEvent`).
- Strums (`e.strum`): template fit (`chordFit`) ≥ 0.5 / 0.44 / 0.38, and no rival chord fitting better than the
  expected one minus 0.015 / 0.02 / 0.03, two frames.
- Chord steps (`isChordEv`): Strict unchanged (`chordScore` > 0.42, 3 frames). Standard / Beginner: at least 60%
  of the chord's notes heard, share of the sound inside the chord ≥ 0.5 / 0.33, and the rival check.
- **Rival check (`cmRivals`, `cmBest`)**: the song's chords plus all 24 major / minor triads, but a rival only
  counts if a note it has and the expected chord lacks is heard (≥ 25% of the loudest note in `strumChroma`): a
  partial G (G and B strings) isn't rejected as Em without an E. Applied in all three modes for strums (Strict keeps
  its old song-chord rivals too); for chord steps in Standard / Beginner.
- Why Strict changed too: the new test showed Strict accepted Am strummed for C or D (4/8) and Em for G (3/8).
  Now 0/8 and 1/8. Full strums and 3-string partials still 8/8.
- Test: `tools/detection-tests/test_chord_matching.py` (= test_strums.py plus env `MODE`, `PLAYV` per-step voicings,
  `ASNOTES=1` for chord steps instead of strums, `STDBG=1` to print fit numbers). Matrix over G C D Em ×2:
  FULL 8/8 in every mode; 3-string partial 8/8; 2-string partial Strict 2, Standard 3, Beginner 4 of 8; full +
  wrong open string: strums 8/8, chord steps Standard 6/8 (by design), Beginner 8/8; Am strummed throughout 0/8
  everywhere; Em/G/C swapped ≤1/8. Regressions: test_strums 95/96, test_window_steal 95/96 (unchanged);
  chords_dead_strings same hits, but C with a dead B and Am with a dead D now grade "Okay · late" (the rival check
  holds them a frame or two).

## v1.88: chords found in a song's notes draw as blocks (display only)

`chordView(ev)` (next to `isChordEv`) builds a cached per-song drawing view; the draw loop uses `CV[i]||ev[i]`.
Playing, scoring and saving still use the original events. A step with 3+ notes on different strings that is not
already a `strum` / `chord` event is a chord: drawn as a block across the strings it uses, with each string's
fret (or note name). The same chord (same strings and frets) repeated 3+ times in a row, each within 2 beats of
the last, becomes a strum pattern: first one with the full fingering, repeats as strokes with ▼ / ▲ (direction
guessed from the beat: off-beat = up). 2-note steps stay single gems. The chord name above comes from the existing
label. Checked: screenshots of a test song (singles, Am, C, G x6), strum regression test 95/96 unchanged.
Test script: not kept in the repo (rebuild: open a `kind:'file'` def with events via `openSong`, set `G.clock`,
call `draw`).

## v1.87: guitar tunings (Tuner) — app, imports and the Lab follow them

Owner asked for tuning options in the Tuner that say how to adjust each string as it's picked.
- **Core**: `TUNINGS` (std, eb half step down, dstd whole step down, dropd, dropdb, dropc, openg, opend, opene, dadgad,
  cstd), `setTuning(id)` rewrites `OPEN` / `STRING_LABELS` **in place** (so every string+fret→note path follows),
  `TUNING_ID`, `STD_OPEN`, `tuningShift()` (uniform shift or null), `tuningFromLows(lows)`, `TUNE_FLATS` (named so
  because the voice code already has `FLAT_NAMES`). `chordEvent` pcs: in a non-standard tuning, the shape's sound
  (uniform shift → name moved; drop/open → the shape's notes). Chord shapes stay standard fingerings.
- **Setting**: `settings.tuning`, applied at startup before any song is built (`setTuning(settings.tuning||'std')`);
  `applyTuning(id)` saves, drops every song's cached `_built`, refreshes the tuner and reopens a paused song.
- **Tuner**: tuning picker; string = nearest target (or tapped = locked); target note per string (flats for flat
  tunings), Hz vs target, "Tighten (tune up) / Loosen (tune down) N semitones (¢)" or cents, ✓ per string after
  0.5 s within 5¢. Raw pitch (not the tuning follower's corrected value).
- **Songs**: `def.tuning` = what the song is written for (MIDI per-string exports: each string's lowest note →
  `tuningFromLows` — TYSK → eb; Guitar Pro track tuning; text tabs "Tuning: half step down / Drop D …" in the Lab),
  `def.builtTuning` = the tuning its strings/frets were worked out in. `buildSong`: rec / file / library-file songs
  whose builtTuning ≠ current get `retuneEvents` (same pitches, strings/frets for the current tuning; chords rebuilt).
  Opening a song with `def.tuning` ≠ current asks "This song is in …" → Keep mine / Switch. Report: "tuning <id>".
- **Lab**: core set to the user's tuning (`userTuning()` from localStorage); a sheet is read in its own tuning when
  known (file part / text) and saved with tuning + builtTuning.
- Tests: tuner cases via a fake analyser (/tmp/tun.py pattern: drop D low E → "Loosen 2 semitones"; E♭ high E →
  "Loosen 1 semitone"; lock); TYSK MIDI song: tuning eb/eb, prompt, keep → standard frets, switch → E♭ frets;
  "Tuning: half step down" chord sheet vs a standard-pitch recording → capo 1. Boogie 95/96, fingering/lyrics node
  tests, Lab sheet tests unchanged.

## v1.86: MIDI tab exports read whole; files lined up by their own timing

Owner sent the full TYSK MP3, the Songsterr-style MIDI (Morgan_Wallen-Thought_You_Should_Know_Tab-12-15-2025.mid) and a
1.85 report (real guitar loaded, from a sheet; notes didn't match what was heard). Reproduced here end to end
(full song through the real model in headless Chrome, single thread: 703 s).
- **MIDI reader split one guitar into six parts**: tab programs export each string on its own channel (ch 0 = high e
  … ch 5 = low E; this file also splits vocals over 5 and bass over 3). `parseMidi` grouped by track:channel → the
  Lab took "part 1" = the D-string thumb notes only (252 of 773). Now channels of one track with the same program are
  one part (key track:p<program>, else track:c<channel>). Affects the app's import too (twinkle/riff/chords files
  unchanged). This file is in E♭ tuning (each string's lowest note a semitone under standard): Fretline has no
  alternate tunings, so notes show at the same pitch in standard tuning.
- **File timing**: the order-only path forced the MIDI onto the recording from 0 s, but the file's guitar starts at
  beat 47 (20 s) while the recording's starts at 0.3 s → notes seconds off. `fitFileTiming`: one offset + tempo for
  the whole file (file tempo, ½, 2× each ±1% in 0.25% steps, offsets every 50 ms, then ±0.3% / ±60 ms fine; scored
  by note-name match vs the average, per candidate transposition; precomputed per distinct note set). TYSK: 140 BPM,
  beat 0 at −19.84 s, 0.139 above average vs top-1% 0.051. Then the whole file is moved by the median gap to the
  nearest pick (chroma peaks ~0.1 s after a pick: −86 ms) and each note snapped to its pick if within 35 ms (TYSK: 422
  of 773; median 3 ms from the file's timing). Tempo/bars come from the file (bar 1 = the file's bar of its first
  note). Both ways are tried for files: the order-only result only wins if it also follows the file's rhythm
  (Theil-Sen line vs file beats, ≥80% within 0.1 s) and matches the chroma better (a file at another tempo than the
  recording: synthetic 120-BPM MIDI vs 100-BPM riff → order-only, 100% linear, 64/64). TYSK: order-only only 14%
  linear → file timing.
- Tests: /tmp/fitt.py-style check (guitar stem from the full run + the MIDI; not in the repo since the MP3/MIDI are
  the owner's); `RIFF=riff_even MIDI=riff.mid sheet_tab.py` 64/64; chords MIDI unchanged.

## v1.85: recording songs keep the played timing; report shows the recording's state

Owner: a full song made with a MIDI file sounds like "the timing of the notes is off" in Listen with the band.
(The song is on the phone; not seen here.) Two causes found in the code:
- **Grid snapping**: steps were snapped to 16ths (32nds < 90 BPM) of the detected tempo, up to ±half a slot
  (~50 ms at 140 BPM), worse when the detected tempo is slightly off (99.5 vs 100 on the test riff). Now
  `placeEvents`, `quantise` (Lab) and `recPlace`/`recRetime` (app) use 1/48 beat, like `eventsFromNotes` does anyway:
  steps stay where they were played; bar lines still follow the detected / chosen tempo. Clean synthetic riff
  (`riff_even.wav`: additive plucks, exactly 100 BPM, generator below): aligned median 2 ms / max 6 ms, as placed
  median 3 / max 10 ms. Existing songs: ♩ → Save (same tempo) re-places them (sheet songs and AI songs from 1.82 keep
  exact times; older AI songs only have beats).
- **Real guitar not loading** (a 4-min song is two ~42 MB WAVs, ~90 MB each decoded): a failure used to fall back
  silently to synthesized notes (played at the snapped times against the real band). Now a hint says so, and the
  detection report has "recording: backing N s, real guitar yes / FAILED <why> / none (older song), from a sheet /
  AI notes, offset".
- Test note: riff100.wav has a pre-attack ~55 ms before each on-beat pick (from how it was made), so its timing
  residuals are ±27 ms; use `RIFF=/tmp/stemtest/riff_even.wav` for timing checks (generator in the lab-tests README).

## v1.84: Lab sheets from MIDI, MusicXML, Guitar Pro and PDF files

Owner: "Why can't we use the midi file for the tabs or chords?" (v1.83 only took text.) Now the Lab's sheet file
button takes text/ChordPro, PDF (text pulled out into the box), MIDI, MusicXML (.xml/.musicxml/.mxl) and Guitar Pro.
- `loadCore` also lifts the app's file readers out of index.html's main script: the block from
  `function loadScript(srcs)` up to `const TAB_SITES` (loadScript, unzip, readMxl, readGuitarPro, readPdfText) plus
  `sniffExt`, run in the same private scope as the core. **Keep those functions contiguous there** (or update the
  markers in `loadCore`).
- File → `SHEETFILE {info,fmt,name}`; Track picker (default: a guitar track with tab, else any guitar, else first);
  "Use it as" Notes (`eventsFromNotes`, string/fret from the file when it has tab) or Chords (`chordChart`, its capo
  passed to the alignment); chord-symbol tracks use `chordEventsFromSymbols`. With a short clip ("first 30 s") only the
  start of the file is used (file tempo × 1.6 + a bar). The file's own timing/tempo is otherwise ignored: the
  alignment places every step from the recording.
- Tests: `MIDI=/tmp/riff.mid sheet_tab.py` (120 BPM file with bass + drums + 2 empty bars vs the 99.5 BPM riff:
  guitar track picked, 64/64); `MIDI=/tmp/chords.mid sheet_chords.py` (as chords: changes 0-72 ms; strums 66/64).
  MIDI test files are written with `mido` (snippet in tools/lab-tests/README.md). MusicXML / Guitar Pro use the same
  readers as the import screen (not separately tested in the Lab).

## v1.83: Lab: line a tab or chord sheet up with the recording

Owner: keep the Lab as it is, plus an option to attach a chord sheet or tab when splitting, aligned to the audio.
- **UI**: "Use a tab or chord sheet for the notes (optional)" (`#sheetBox`): paste or load a text file, type
  (detect/tab/chords), chords shown as "one strum per chord change" or "follow the recording's strums". With a sheet,
  the song comes from the sheet (Basic Pitch is skipped); without one, nothing changed.
- **Reading**: Fretline's own `parseTab` / `parseChordSheet` from `<script id="core">` of index.html, fetched and run
  in its own scope (`loadCore`), so the Lab reads sheets exactly like the import screen. Capo from the text.
- **Alignment** (`alignSheet` → `alignPath`): guitar-stem chroma (`chromaFrames`: 4096 FFT / 512 hop at 22.05 kHz;
  one value per semitone = strongest bin, so high harmonics don't outweigh fundamentals — first version read low E as
  B; notes ≥ E4 ×0.6, ≥ E5 ×0.35). Templates: the event's note names (single notes + 0.35 fifth + 0.15 third
  overtones; tabs + 0.3/0.12 of the two notes before, still ringing). Left-to-right path over [intro, events, outro];
  each event ≥ 3 frames (sub-states); cost 1 − cosine; silence costs events +0.15 (belongs to intro/outro).
  Picks: attack curve peaks, strongest within ±90 ms, credited to the frame at pick + 20 ms (chroma turns within
  0-35 ms). Tabs: moving on costs 0.6 − 1.0·pick, holding through a pick +1.2·pick (each tab step is a pick);
  chords: 0.3 − 0.5·pick, no hold penalty; skipping an event +6. Tried at the sheet's capo and the 3 best
  transpositions (overall note-name balance); cheapest wins. Starts snapped to the nearest pick (±0.12 s, never the
  same pick twice). Shift 1-7 → capo; more → chord names rewritten in the recording's key with `bestCapo`; tabs as
  written. Then `findBeats` tempo, bar 1 at the first step, steps on the grid (`placeEvents`, 32nds < 90 BPM),
  chords held to the next change; strum mode adds a strum on every strong pick (≥ 2.5×) inside each chord, direction
  by nearest 8th (down on the beat). Saved as `{kind:'rec', events, recEvT (s per step), …}`; `buildSong` uses
  `def.events`. ♩ tempo (`recRetime` → `recPlace`) and the Lab buttons (`retimeEvents`) re-place from `recEvT`.
- Tests (`tools/lab-tests/`): `sheet_tab.py` (riff with deliberately uneven tab spacing: 64/64 on the right beat
  clean, 63/64 with the file's clicks; half tempo moves nothing; main app opens it, real guitar in Listen, ♩ 2×
  moves nothing). `sheet_chords.py` (synthetic strummed G C D Em G C with uneven lengths after 2 s silence; sheet
  without lengths: changes within 0-72 ms; strum mode 66 strums for 64, directions right; `SHEET=` env: a sheet 2
  semitones high is rewritten to G C D Em; "Capo 2" F Bb C Dm keeps capo 2). e2e/native unchanged.
- Limits: the sheet must follow the recording (repeats written out or "x2" on chord lines); whole sections the
  recording skips cost 6 per skipped step, so long mismatches may misalign; lyrics from sheets are dropped.

## v1.82: set a recording song's tempo by hand

Owner asked to enter a BPM manually when it's known for sure.
- **My songs**: recording songs show "♩ <bpm>" beside ✕ → `#tempoEd` overlay: number box (2 decimals shown; an
  unchanged value keeps the exact stored tempo), ½ / 2×, "Tap the beat" (median of the last ≤16 tap intervals,
  resets after a 2.5 s pause), Save. `recRetime(def,bpm)`: notes keep their times in the recording and are re-placed
  on the new grid (32nds < 90 BPM, else 16ths); exact halving picks the old beat the notes lean on; otherwise bar 1
  stays put (then the first note is pulled into bar 1 by whole beats). Uses `def.recRaw` (exact times, saved by the
  Lab from 1.82) or rebuilds times from beats for older songs. Test: TYSK 139.75 → 69.875, 329/329 notes, 0 ms moved.
- **Lab**: "Or type the exact tempo" + Set tempo next to Half/Double (`retime(1,bpm)`), 30-300 BPM.

## v1.81: cleaner notes from recordings; half/double tempo in the Lab

Owner: the real-guitar guide works. But "Thought You Should Know" is 70 BPM with ~60-75 plucked notes in 30 s (per
Google), and we made 300+ notes at 140. Measured on the real guitar stem: ~100-130 clear picks (16ths at 70 BPM in
places; Google's count is a guess), so the transcription had ~2.5× too many notes and 1.6× too many steps.
- **`cleanNotes(notes,g22)`** in the Lab: spectral flux of the guitar stem (`attackCurve`, own radix-2 FFT, 1024/256
  at 22.05 kHz, running median over ±43 frames). Keep a note if the flux peak within ±50 ms is ≥ 2× the local median,
  it lasts ≥ 0.1 s (or is loud ≥ 0.5 with a strong attack ≥ 4), and above G5 only if amplitude ≥ 0.5; per pick
  (onsets within 60 ms) the loudest note plus at most one other of a different note name ≥ 0.8× as loud. TYSK clip:
  329 notes / 176 steps → 147 / 112. Synthetic riff: 64/64, extras 7 → 0.
- **Tempo**: the beat finder can't separate 70 from 140 on this song (raw autocorrelation 4.1 vs 5.8). After making
  a song the Lab shows "Use ½ / Use 2×" buttons (`retime`, `LAST`): no re-splitting; exact tempo (not rounded, since
  0.2% would drift 0.4 s over a song); for half it chooses which old beat becomes the new beat by where the notes
  lean; `quantise()` uses a 32nd grid under 90 BPM so halving moves no notes. Updates the saved song in place.

## v1.80: recordings use the real guitar as the guide; Lab downloads work in the app

Owner (v1.79): the native separator works on the phone, 0.53× song length (vs 2.4× on one thread in the WebView;
30 s clip in 21 s total). A song made from the 30 s "Thought You Should Know" clip "sounds very very sped up" while the
backing is fine; Lab download links did nothing in the app.
- **Diagnosis** (reproduced here with the real model, mirrored through the manual `Mirror Lab model` workflow into
  the `lab-model` release because Hugging Face is blocked in the workspace; same result as the phone, 329 vs 333
  notes, 139.75 BPM): the clock and backing are right (video's countdown is real time). The guitar stem is a
  fingerpicked 8th-note part, ~5.3 attacks/s; the transcription has 176 onsets, 118 on a real attack. Played back as
  short, even synthesized plucks it sounds frantic.
- **Fix:** the Lab now also saves the separated guitar (`<id>-gtr.wav`, `def.recGuitar`). In the app (`RECB.gbuf`,
  `RECB.gsrc`, `RECB.ggain`, `recGtrOn()`, `recGuide()`), the real guitar starts with the backing from the same
  position and rate; Listen plays it (no synthesized plucks); Play with headphones and "play the right note" fades it
  in while you hit and out after a miss (`G.fxOn`), instead of plucks. The recording loads even with the backing off
  (band gain 0 then). Deleting the song deletes both files. Older recordings (no `recGuitar`) behave as before.
- **Downloads in the app:** `NativeSeparator.saveChunk({name,data,first})` (3 MB base64 chunks to a cache file) +
  `saveFinish({name,mime})` → MediaStore `Downloads/Fretline/` (Android 10+). Lab links use it when present.
- Tests: e2e.py now also checks guitar track loaded, 0 plucks in Listen, guitar gain 0.6 while hitting / 0 after a
  miss / 0 with the effect off; 64/64 notes, sync 6 ms. Boogie sim 95/96.
- **Still open:** transcription of fingerpicked parts (a third of onsets spurious; bass bleed F2-G#2 below a capo'd
  guitar). Ideas: drop notes without a real attack in the stem's spectral flux; a "chords" version of recording songs.

## v1.79: native Demucs in the APK (all cores)

Phase 2 of the owner's request ("build it into the browser and then create the new APK ... get full use of those
cores"). The WebView can never be cross-origin isolated, so onnxruntime-web is stuck on one thread there; the APK now
has its own separator.
- **`NativeSeparatorPlugin.java`** (`@CapacitorPlugin(name="NativeSeparator")`, registered in MainActivity;
  `com.microsoft.onnxruntime:onnxruntime-android:1.22.0` in app/build.gradle; `ndk.abiFilters arm64-v8a, armeabi-v7a`; minSdk raised 23 → 24 (ORT requires it)
  to keep the APK small). Methods: `status()` → {available, cores, modelBytes, loaded, threads};
  `prepareModel({url,name,expectBytes})` downloads to **`filesDir/models/`** (app storage: survives "Clear cache";
  `.part` file, HTTP Range resume, 6 tries, never kept if < 97% of expected; "progress" events {got,total,note});
  `load({path,threads})` (default min(6, cores-1) intra-op threads, EXTENDED_OPT); `run({mix: base64 LE float32 [2·n]
  planar, n})` → {guitar, band (sum of the other 5 stems), ms}, both base64 [2·n]; `unload()`. All work on one
  background thread. Compile-checked with javac against stub classes (Maven isn't reachable from the workspace); the
  real build is CI.
- **Lab**: when `Capacitor.Plugins.NativeSeparator` is present, "Run on" gains "Phone app, all cores (fastest)" as
  the default; the web runtime isn't even loaded. Any native failure before the first part (status/download/load)
  falls back to the web runtime; a run error is retried once. Chunk accumulation is now runner-agnostic (each runner
  yields guitar G and band B as [2·SEG] planar). Report lines start with `native:`. `window.__labBufs` exposes the
  results for tests.
- Tests: `tools/lab-tests/native.py <audio> [fail]` (fake plugin: guitar = 0.3×, band = 0.7× input; exact to 5e-8;
  `fail` checks the fallback). mt.py and e2e.py unchanged (64/64 notes, sync 5 ms).
- **Was open, see v1.80:** a song made from the 30 s "Thought You Should Know" clip plays
  "very very sped up" in the main app while the backing band sounds right. Tempo detection gives ~140 BPM for that
  clip (176 steps in 30 s). Investigate next.

## v1.78: songs from a recording (Lab) with the band as backing

Owner: guitar stem from the phone run "sounds amazing", no bleed. Asked to build it into the app, then the APK for
multi-core. Phase 1 (this version):
- **Lab** (`lab/stems.html`): after splitting, "Also make a highway song" (default on, title field). Guitar stem →
  22.05 kHz mono → **Basic Pitch** (`lab/basic-pitch/`: esbuild bundle of @spotify/basic-pitch 1.0.1 + tfjs 3, 1.2 MB,
  WebGL backend; model files from the npm package; Apache-2.0) → filters: quiet blips, out-of-range (<D2, >F#6),
  ghosts an octave / 12+7 / two octaves above a note starting together (quieter+shorter, or <0.75× as loud).
  **Tempo** from the full mix (log-energy onset envelope, 11.6 ms frames, autocorrelation 60-180 BPM with a prior at
  110, beat phase, bar accent); first note forced into bar 1 by whole beats; Basic Pitch's onset lag removed (circular
  mean against the 8th grid); notes quantised to 16ths. Saves the band-without-guitar WAV to Cache `fretline-audio`
  (key `<origin>/__fretline/rec/<id>.wav`) and a song `{kind:'rec', recNotes:[{midi,beat,dur,v}], recAudio,
  recOffset (s of beat 0), bpm, bpb:4}` into `localStorage['fretline:songs']`.
- **Main app**: `buildSong` builds `kind:'rec'` with `eventsFromNotes`; My songs shows "From a recording" 🎙;
  `recLoad`/`recTick`/`recStop` (state `RECB`; `REC` was taken) play the recording as the backing: position =
  recOffset + clock·60/bpm + soundDelay·speed, playbackRate = practice speed, re-sync if > 80 ms off, stopped on
  pause/finish/reset; the synthesized band is off for these songs (falls back to it if the audio is missing); deleting
  the song deletes its audio; SW keeps `fretline-audio`.
- Tests: `tools/lab-tests/` (synthetic 100 BPM riff: 99.5 BPM, 64/64 notes on the right beat, 8 extras; backing sync
  1-6 ms). Main regressions unchanged.
Phase 2 next: native Demucs in the APK.

## v1.77: Lab page: split a song with Demucs (on device)

Owner wants to import a band recording, isolate the guitar and build a highway song from it. Discussed limits (guitar
stem is the experimental part of `htdemucs_6s`; all guitars land in one stem; phone speed/memory unknown; weights'
licence not explicitly granted; separation is only step 1, then Basic Pitch → beats → fingering → chords). Step 1 built:
**`lab/stems.html`** (linked from Settings › App), standalone, doesn't touch the main app. onnxruntime-web 1.20.1 from
jsdelivr (WebGPU, falls back to WASM; single thread on GitHub Pages: no cross-origin isolation), model
`adowu/htdemucs-6s-onnx` from Hugging Face (fp16-weights 136 MB default / fp32 258 MB), kept in Cache API
`fretline-models`. Input `mix` [1,2,343980] @ 44.1 kHz, output `stems` [1,6,2,343980] (drums, bass, other, vocals,
guitar, piano); mono mean/std normalisation, 25% overlap, triangular blend; outputs guitar and "band without guitar"
as WAV players/downloads; report = per-chunk times, backend, guitar share. Tested in headless Chrome with a stand-in
ONNX of the same shape (the workspace can't reach Hugging Face): blending exact (max error 0), GPU→WASM fallback works.
Owner's first phone run (SM-S948U1, Android 17 WebView, 8 cores, 8 GB, WebGPU present, single thread): model from
cache, then `Aborted()` while creating the session, with both models and both backends: almost certainly the wasm heap
running out while loading (fp16 weights are expanded to fp32; 'all' optimisation folds the casts into a second full
copy, plus memory arenas). Fix: runtime 1.31.1; "Loading" option, default **lean** = graphOptimizationLevel
'disabled', no CPU arena / memory pattern, sequential; model copy released after load; ORT console messages and page
errors captured into the report. An abort poisons the runtime: reload before trying another setting.
Second phone run (lean, fp16 model, WebGPU and processor): no abort any more, but "Could not find an implementation for
ConstantOfShape(9) node '/real_istft/ConstantOfShape'": in the fp16-weights export that node outputs fp16, which the
web build's CPU kernel only gets past when constant folding removes it (i.e. optimised loading, which runs out of
memory). Default model is now the fp32 export (258 MB) with lean loading; the page explains the error if it recurs.
Third run (fp32 + lean): same ConstantOfShape error. Reproduced locally with one-node models: ConstantOfShape with a
**double** (or bfloat16) value fails in onnxruntime-web at every optimisation level, all other types load. The
StemSplit exports carry float64 in `real_istft`, so they can't run in the browser. Added the SonicDemixer export
(`smank/htdemucs-onnx`, `htdemucs_6s.onnx`, STFT/iSTFT in graph, "no complex dtypes", output `sources`) as default;
inputs/outputs now read by position and logged. Other route if that fails too: demucs-rs (Rust/Burn, WebGPU, Apache-2.0,
6s = 84 MB, demo https://nikhilunni.github.io/demucs-rs/), or the 4-stem split build `monteslu/htdemucs-web-onnx`
(needs our own STFT/iSTFT).
**First success (SonicDemixer build, lean, processor, single thread):** 246 MB download, session in 3.2 s, ~14-16 s per
7.8 s part = 2.43× the audio length (a 3.6-min song ≈ 9 min); guitar share 60%. An earlier download failed with
"network error" when the owner switched to Chrome (WebView backgrounded). Download is now in 16 MB Range pieces, each
retried up to 5×, saved as `?fretline-piece=N` cache keys (not `#`: the Cache API ignores fragments, which made every
piece "resume" piece 0 forever and crashed the tab in testing), so a reload resumes.
Owner on quality: **guitar stem "sounds amazing", no singing or bleed audible**; band-without-guitar has clear vocals
(the song has few other instruments). WebGPU: first part 4.5-5 s (3× the processor) then "Device is lost" on part 2,
twice. Now: on a lost device the session is rebuilt on the GPU (up to 2×, 300 ms pause), then the rest runs on the
processor. Multi-core: `sw.js` adds COOP same-origin + COEP credentialless to navigations under `/lab/` only, the Lab
page registers the SW and reloads once, ORT uses up to 6 threads (tested: isolated, threads work, CDN-origin runtime OK;
main app not isolated). Test hooks: `?ortbase=` and `?modelurl=`.
Next phone run broke two things: (1) the new SW version's `activate` deleted every cache but its own, including
`fretline-models` (now kept); (2) the piece download stopped after the first 16 MB piece on real Hugging Face (works
against a local Range server, so HF/redirect behaviour differs) and cached a 17 MB file → "protobuf parsing failed".
Download is back to one continuous fetch (as in the working run) that continues with `Range: bytes=N-` if the
connection drops, retried up to 6×; files under 97% of the expected size (`EXPECT`) are never cached, and an incomplete
saved copy is discarded. Isolation also showed "threads no" on the phone: COEP is now `require-corp` (script loaded
with crossOrigin=anonymous), up to 2 reload attempts, report logs whether the SW is in charge.
Phone run after that: download + processor fine (13.9 s/part); **WebView never becomes cross-origin isolated** even with
the SW in charge and COEP require-corp (multi-core not available inside the app). GPU: 4.5 s first part, then device
lost before every later part (rebuild 2 s), and **GPU parts came out silent** (guitar share 25% vs 60%): NaN from the
input-normalisation prologue on WebGPU (same as monteslu's notes). Now: `onnxNodes` (minimal protobuf walker) reads
node names from the model; top-level `/Op(_n)` arithmetic/reduce nodes go to `forceCpuNodeNames` for WebGPU; every GPU
output is checked for non-finite values → that part and the rest run on the processor; after the first device loss the
GPU session is rebuilt before every part (cap 6 losses); `navigator.storage.persist()` requested and logged. Tested with
a fake WebGPU session (reset on run 2, NaN from run 4): exact output.
Owner asked to keep the model safe from cache clears: Cache Storage survives Android "Clear cache" but not "Clear
data"; true protection = a native file in the app (APK). Bigger next step proposed: run Demucs natively in the APK
(onnxruntime-android: all cores + NNAPI/GPU), model stored as an app file.
Rerun with 47 nodes pinned to CPU: the GPU reset before finishing even part 1, three times (more CPU↔GPU traffic).
Conclusion: in the WebView only the single-thread processor path works (≈2.4× audio length, guitar stem judged
excellent). Default is now "Processor (reliable)"; graphics chip labelled experimental. storage.persist() is refused
in the WebView. Next: native Demucs in the APK (onnxruntime-android) — awaiting owner's go-ahead. and send the report + say how the guitar track sounds. Then:
Basic Pitch (`@spotify/basic-pitch`, model inside the npm package) on the guitar stem → draft song; backing track =
band without guitar.

## v1.76: research-led: tuning follower and whitened chord sound

Owner asked to research Yousician / Gibson App (gold standard) and Simply Guitar (weak) and strengthen recognition.
Write-up with sources: **`docs/RECOGNITION_RESEARCH.md`** (read it before more detection work). Adopted:
- **Tuning follower**: `followTuning` (in `detectFrame`) records each steady pitch reading's cents from the nearest
  semitone, per note (`TUNE.by[m]`, last 30, used from 5) and overall (`TUNE.all`, last 60, from 10); `tuneCents(m)`
  (≥ 8, ≤ 40) shifts the pitch reading and every expected frequency (`targetScoreBuf`, so targeted checks and
  `lowPartner`; `strumChroma`). Saved in `store` `tune2`. Report header: `tuning ±N cents`. A single global offset cost
  the in-tune boogie 12 steps (sample notes off by different amounts), per-note fixed it. Sim with `DETUNE=±30`
  (new option in `test_window_steal.py` / `test_strums.py`): boogie 54→78 / 43→71, arpeggio 47→64 / 57→60, strums
  95→102 / 99→102.
- **Whitening** in `strumChroma` (each note ÷ its ±6-semitone mean^0.67): strums in tune 100→102.
Regressions all unchanged (boogie 95, swapped 8, E+B 38, E+C# 45, late 96, arpeggio 64 and wrong 0, strums Em/D/G
exact, one-note 33/1/4/4, melody 17, double stops 95, sweeps G/B 18/18 and 0/18).

## v1.75: string colours separate from note colours

Owner asked to colour the strings freely (all one colour or each string) so the coloured notes are easier to read.
Settings › Colours › "String colours": Same as the note colours (default, as before) / All one colour (swatches incl.
grey `#8a8f9a`, or any colour) / Choose each string (6 pickers, start from what's showing). `settings.colors.strings`
('match'|'one'|'custom'), `strOne`, `strCustom`; `applyColors` fills `STRC`, used for the string lines, string letters,
tinted lanes and lit target rings (game and the Colours preview). Notes, hold tails, fretboard dots keep `SCOL`/`FCOL`.

## v1.74: strums must be the right chord, strummed in their own window

Owner's 1.73 report (their uploaded song "Thought You Should Know", strums D/A/Em/G, 72 BPM): 376/399, and playing Em
throughout still counted everything. Two causes in the strum branch of `matchEvent`:
1. Any onset < 300 ms old counted, with no check of what was played.
2. No window start for strums: most hits were "okay -380 ms · picks 0/0": a strum took the previous step's onset and
   the whole song slid one strum early.

Now: the onset must be at/after the step's window start (`G._winAt`, −20 ms) and < 400 ms old, the early-window cap
(half the gap to the previous step) applies to strums too, and the sound must fit the chord: `chordFit(pcs)` =
cosine similarity of a per-note chroma (`strumChroma()`: Goertzel at every note E2..B5 on the 8192 buffer, folded to
12 pitch classes) with a template that includes each chord note's overtones (5th 0.5, major 3rd 0.25, minor 7th 0.15).
The expected chord (`strumPcs`: from `snotes`, else the label; capo applied) must score ≥ 0.5 and ≥ every other chord
in the song (`songChords()`) − 0.015, on 2 frames. Muted (x) strums: timing only. `chordScore`'s spectrum is now read
once per frame (`chromaC`).

Things tried and dropped: the old note-name energy (`chordScore`) can't tell Em from D (the 4096 FFT's 11 Hz bins
put E2 into D#/F and B2 into A#/C); judging only what a strum added (now minus before) and comparing with all 24
triads both wrecked correct playing (27/104).

Sim (`test_strums.py`: `CHORDS=` chart per step, `PLAYC=` what's strummed (one name or a list), voicings in `VO`,
`STTOL=` tolerance; owner's pattern D×3 A×4 Em×6 … with G, `GAP=0.4167`): correct 100/104 (misses: 4 G strums right
after a ringing Em); Em/D/A/G throughout → exactly their own strums (+ the first strum for Em and G). Known leak: a
chord that isn't in the song (C) passes where it fits best among the song's chords (Em, A steps). Regressions unchanged:
melody 17/17, double stops 95/96, arpeggio 64/64, boogie swapped 8, chord-string analysis (differences = the test's
own random noise; v1.72 varies the same way).

**Needs:** owner to play the song again correctly, then Em throughout.

## v1.73: notes picked over a ringing note; the right note played in time

Owner's 1.72 boogie report: 73/96, bars 1-4 32/32, E/A bars 63/64; owner considers the boogie fixed. Two new asks.

**Arpeggios** ("Arpeggios in A minor", 145/160): owner saw other strings lit in the strike zone and correct notes
missed (e.g. open B after open G: #7, #23 "heard G3>G2"). Sim with the arpeggio as played (strings ring until
re-picked; `SEQ=` in `test_window_steal.py`, 56 BPM eighths = `GAP=0.536`): 61/64, G3 (open G) after E3 missed.
Cause in path 2 of `matchEvent`: while the previous note rang, the block returned before the strength history
(`G.tHist`) was written, so after the pick there was no "before" and `rose` never fired. Now `G.tHist` is written every
frame (before the block); the old after-block history is kept as `G.tHistOK` for the re-pick test (`tb`) and as a
first `rose` source. The every-frame history only counts if the note that blocked before (`G.blkBy`, its strength in
`G.blkH`) wasn't itself re-picked (≥ 1.8× jump): without that, D4 played over G4 steps passed (its re-pick lifts G4's
3rd; D4-throughout 4 → 7). Sim: arpeggio 64/64; wrong notes in it (G/B a semitone sharp, C played as B) 0 false;
one-note lesson correct 33, G3 1, D5 4, D4 4 (all unchanged); melody 17/17; double stops 95; boogie E+B 38, swapped
8, late 0.15 96; sweeps G and B strings 18/18, wrong 0/18.

**Hit sound.** Owner: the "play the right note" sound sounds like an inexperienced player. It was played on credit
(`fxHit`), 50-300 ms after the pick and uneven, plus Bluetooth delay. Now with headphones in Play mode (`fxInTime()`),
notes are scheduled on the beat like Listen (`G.fxIdx`, `soundDelay()` + 50 ms lookahead, `playEvent`); `G.fxOn` turns
off on a miss (`fxCut` damps only that note's own voices, matched by start time `voices[s].t`) and on again at the
next hit. Without headphones, or in Wait mode, it stays on credit. Option text: "Also play the right note, in time,
while you hit (use headphones)". Sim: 95 notes scheduled exactly on the beat, 1 cut for the 1 miss; detection unchanged.

**Needs:** owner to try the arpeggio lesson and the in-time sound (Settings › sound effects › the third option).

## v1.72: late first step after a fret change

Owner's 1.71 report (correct playing at 100%, latency 0): 56/96, bars 1-4 32/32 (1.70: 13/32), `2nd` 0.75-0.97 on
correct steps, so the low-overtone check works on the phone. Owner: the first step after a 2-0 → 4-0 switch often
didn't count. The report shows misses with high `2nd` (#58 0.88, #60 0.89, #81 0.85, #85 0.96) and later grades
drifting to +119/+129 ms.

Sim (`LATE=` delays the first step after each change): 100 ms late → 55/96 (same in 1.68 and 1.70, not new). Debug:
on a change over the ringing low E the pick is detected ~110 ms after it happens, the step's late window (gap×0.55 =
236 ms) has closed by then, and confirming the second note takes longer still (lowPartner waits 110 ms). Fix in the
update loop: a two-note step whose latest pick (after the last credit) falls inside its window, allowing 120 ms of
detection lag (never past 90% of the gap to the next step), stays open until 300 ms after that pick (`waX`). Sim:
LATE 0.10/0.15/0.20 → 96/95-96; on time 95/96; swapped 8 (was 7), E+B throughout 38 (36), E+C# throughout 45 (45),
F#2+C#3 on E+C# steps still all rejected; melody 17/17; `test_double_stops.py` 95/96. A pick that lands near the
boundary can now go to the earlier of two identical steps instead of the later one (same score).

Still weak: A+E steps (E3's telling overtone is 165 Hz, under the long buffer's ~215 Hz reach; tracker often reads
E2 for it).

## v1.71: second note judged on its low overtones (8192-sample analyser)

Owner's 1.70 reports (correct playing, boogie; 80% = 56 BPM with latency 0 after the results card's suggestion, and
100% = 70 BPM with latency 100): 42/96 and 27/96. Most misses are E+B steps "heard E2 · picks 2/0" (the tracker never
flicks to B2) and, at 100%, every A step. The 1.68 "27/28 E+B" was inflated: playing E+B on every step kept B2 in
`heardRecent`. The `odd` octave numbers for correct E+C# were 0.6-3.1 (sim octave case 0.4-0.5): no usable threshold,
so the octave idea is dropped (`lowOddR`/`lowOddOk` removed).

Cause: `partnerOk`'s overtone fallback uses `targetScoreBuf`, which skips everything under ~433 Hz at 48 kHz
(semitone neighbours blur in 4096 samples). The partner's telling overtones are all there (B2 370, C#3 277, F#3 370,
G#3 415), so only weak high ones (B2's 5th/7th) were checked. A plain Goertzel with wider neighbours on the 4096 buffer
was tried and leaked (E2's 247 Hz smears into 277): E+B-throughout 36 → 63 false.

Now: a second analyser `analyserL` (fftSize 8192, created in `attachAnalyser`, `longBuf`, read once per frame) and
`lowPartner(n,base,cp)`: the normal targeted score on the long buffer for the partner's unshared overtones between
~215 Hz and ~433 Hz (lowest two). In `partnerOk` it can accept the **upper** note only (`n.midi>base.midi`; letting it
confirm the low E let path 2 pass C#3 phantoms: +10 false), at ≥ 0.75, and only ≥ 110 ms after this step's own pick
(`G._winAt` back, used only here; the long buffer still holds the previous step for ~170 ms). Sim (`test_window_steal.py`,
now with a second analyser, `LPT=` threshold, `LP=` low-pass): measured 110-260 ms after a pick, correct 0.81-0.95,
wrong 0.11-0.64. Hit counts unchanged from 1.70: correct 95/96, E+B throughout 36, E+C# throughout 45, swapped 7; melody
17/17. The sim's sampled notes already passed via the tracker, so the gain only shows on the phone. The report shows
`2nd x.xx` (best low-overtone score 110-260 ms after a pick) per two-note step.

**Needs:** a correct run on 1.71 at 100%; check E+B and A steps now count, and read the `2nd` values (correct should
be ≥ 0.75). Also the owner's runs drift onto the wrong strings later in the song (B section): misses there may be real.

## v1.70: undo 1.69's strict checks; fixed highway speed

Owner's 1.69 report (correct playing, boogie): 14/96. Bars 1-4 (#0-63): E+B 5/16, E+C# 4/16, A+E 6/8, A+F# 0/8, so
both new checks hurt real playing: `lowOddOk` (3rd-overtone test, A+F# and E+C# steps) and the window-start limit on
picks / `recentHeard` (E+B steps, which rely on the tracker flicking to B2). From #64 on the app mostly heard notes one
string lower than charted (F#2+C#3 on B steps, E2+B2 on A steps), so those misses look like real wrong notes, not
detection. Changes:
- `fresh` and `recentHeard` back to 1.68 (no `G._winAt`). The early-window cap (half the gap to the previous step)
  stays. Sim swapped-fret: 7 false (was 11 in 1.68, 5 in 1.69); correct 95/96.
- `lowOddR` is measured only: the report adds `odd x.xx` per two-note step (best ratio in the 150 ms after a pick in
  that step; omitted when the other note shares the 3rd). Sim: real E0+A4 ~2.6; A4+D2 ~0.4-0.55, but ~1.9 when the open
  E from the previous step is still ringing (it really is sounding), so a presence test can't catch that case; it would
  need "low E re-picked" (rise of its odd overtones at the pick). Set a threshold only from the owner's real numbers.
- Highway: measured the other app's recording: constant ~17% of screen width per second the whole song (=
  `W×0.17`). It has no speed setting; slowing the song spreads notes. Removed Settings › Highway speed (`#sZoom`);
  `pps` is fixed; the player's − / + practice speed now spreads notes at the same scroll speed. At 1.0 Fretline's
  boogie in landscape: strings ~33 px apart, notes ~30 px, eighths ~61 px apart (the other app: 41 / 32 / ~49).

**Needs:** a correct run and an A4+D2 run on 1.70, with the `odd` numbers from both.

## v1.69: highway speed in pixels per second; early hits can't take the previous step's pick

**Highway.** Owner: the highway can't be both readable and a reasonable speed; slowing it crowds the notes. Compared
with a screen recording of another tab app (an advanced song): it scrolls ~17% of the screen width per second
(~140 CSS px/s on the owner's phone), whatever the tempo, with ~32 px notes, and lets 16th notes touch. Fretline
was pixels per *beat* (`W/7 × zoom × sqrt(note size)`, then up to ×1.6 more for busy songs), so a 120 BPM song moved
~270-440 px/s and the practice-speed control slowed the highway instead of spreading notes out. Now
`pps = clamp(W×0.17, 110, 220) × zoom` and `ppb = pps / bps()`: same on-screen speed for every song and practice
speed (slower practice = more space between notes), note size no longer changes speed, no busy-song boost (notes
shrink to r ≥ 10 for quick passages instead). Setting renamed "Highway speed" with a hint; `settings.zoom` reset to
1 once (`zoomV2`).

**Detection.** Owner's 1.68 report (boogie): they fretted "fret 4 and fret 2" where the chart said open E + A fret 4
(E0+C#3), and those steps counted; 27/96 overall, many hits graded "okay" 180-470 ms early with picks 0/0.

(a) Octave: A4+D2 = C#3+E3, and E3 carries every even overtone of E2 (the tracker even reported "E2"). Sim: 24/24
E+C# steps credited. New `lowOddOk` (called first in `partnerOk`, so both paths): the step's lowest note's 3rd
overtone must be ≥ 0.15 of its 2nd/4th (Goertzel directly; `targetScoreBuf` skips < ~400 Hz), best reading during
the step (`G._oddMax`); skipped when the other note shares the 3rd (E+B, A+E). Sim ratios: real E0+A4 ~2.6, A4+D2
~0.08, real A0+D4 ~0.18 (closest to the line — watch A+F# steps on the phone). Now 0 of those steps credited. Low E
fretted at 2 (F#2+C#3) was already rejected.

(b) Window: the early hits were the previous step's pick. The early window
(`max(0.25 s, ring-touch time ≤ 0.5 s) + latency`) grows as the highway slows (ring-touch time = note diameter /
speed) and at 70 BPM reached back past the previous step (429 ms). Also `heardRecent` (500 ms) let the previous
step's note count as the partner. Now `hitWindow(e,b,gap,pgap)` caps the early window for single notes / two-note
steps at half the gap to the previous note (min 0.12 s); `G._winAt` (when the step's window opened, set in the update
loop) is required for a fresh pick in path 1 and for `recentHeard` readings. Sim (`test_window_steal.py`): fret 2/4 swapped
11 → 5 false (the rest are the known sampled-note overtone leaks), correct 95/96, E2+B2 throughout 36/96,
`song_report_sim.py` 17/17.

**Needs:** owner to repeat the A4+D2 boogie run (E+C# steps should all miss) and a correct run (watch A+F# steps) and send the report; check that the highway speed feels right
and that correct playing still scores.

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
