# Note and chord recognition: Yousician, Gibson App, Simply Guitar vs Fretline

Research done 18 Nov 2026 (web v1.76). Public sources only: patents, papers, support articles, reviews. None of these
companies publishes its detection code, so the "how" below is inferred from their patents, their engineers'
published research and their own troubleshooting advice. Links at the end.

## Yousician (gold standard)

- **Who builds it.** The detection technology comes from Anssi Klapuri, one of the most cited researchers in
  multi-pitch estimation and music transcription (Tampere University). He was Yousician's CTO and is now its Chief AI
  Officer. Their research team works on transcription, audio-to-score alignment and acoustic modelling.
- **Method family (from Klapuri's published work).** A short-time spectrum is first **whitened**: a bank of ~30 bands
  on a critical-band scale measures the level in each region and flattens it (each band scaled by its level to the
  power −0.67), so the instrument's tone colour and the mic's frequency response don't decide the result. Each candidate
  pitch then gets a **salience** = weighted sum of the strongest bin near each of its harmonics (weights about 1/m,
  so low partials count most); taking the maximum in a small range around each harmonic tolerates slightly
  inharmonic strings. Several notes are found by **estimate-and-cancel**: take the strongest pitch, subtract its
  harmonics from the spectrum, repeat. Klapuri reports that guessing *how many* notes are sounding from one frame is
  unreliable; in a learning app this isn't needed because the expected notes are known.
- **Expected-note / chord-model checking.** Their score-following patent estimates, per audio segment, how likely
  each chord is under chord models, plus "activity" (is anything sounding at all). Their harmonic-feedback patent
  compares the user's harmonic content with the track's, with thresholds tuned on recordings of reference players.
- **Per-string chord feedback.** The app marks a string red when it isn't heard in a strummed chord. Strings marked X
  must be muted, because an extra open string can make the chord count as wrong; the high e is the string most often
  not heard (weak strums).
- **Tuning dependence.** Their first troubleshooting step is to tune with the in-app tuner; other tuners "can cause
  recognition problems". So expected frequencies are tight around standard pitch.
- **Weak spots reported by users.** Correct notes marked wrong in noisy or echoey rooms; some devices (an iPhone vs an
  iPad) recognise worse.

## Gibson App

- Built with **Zoundio** (Stockholm); marketed as "Audio Augmented Reality": listens to note and chord playing in real
  time, acoustic or electric, with headphones. No technical publications or patents about the detector were found.
- Users report chords not always recognised and single notes reported "too low" even when tuned.

## Simply Guitar (the weak one)

- Built by JoyTunes ("MusicSense" engine): a DFT-based real-time transcription (pending patent at the time), on device,
  partly on the GPU; they say it filters out ambient noise and "learns the instrument on the fly".
- **Typical failures in reviews:** the low E and A strings often not detected (even at full volume); Em, Am and D
  chords not recognised; correct playing marked wrong in a quiet room on an acoustic, which blocks progress.
- Their own tips: tune with their tuner every time, remove the phone case, headphones, quiet room, let strings ring,
  strum all the right strings, strum when the line touches the bar. Their PLAY mode doesn't judge notes at all.
- Reading the pattern: a pitch-tracking approach that depends on the fundamental (weak through phone mics below
  ~150 Hz) and on clean, balanced chords, with no tolerance for real-world tone, tuning or strum balance.

## Where Fretline stands (v1.76)

| | Yousician (inferred) | Simply (inferred) | Fretline |
|---|---|---|---|
| Knows what to expect | yes, chord models per segment | yes | yes: targeted checks for the expected notes, the song's chords as rivals |
| Low strings | harmonic summation, low partials weighted most | weak (misses E/A) | judges notes on overtones ≥ ~430 Hz plus the pitch tracker; second note on its 215-430 Hz overtones (8192-sample buffer, v1.71) |
| Chord evidence | chord-model likelihood, per-string | chord template | per-note chroma with an overtone-aware template, whitened (v1.76), vs the song's chords; per-string dead/muted check for chord steps |
| Whitening | yes | unknown | chord sound yes (v1.76); single-note checks compare each harmonic with its semitone neighbours, which is self-normalising |
| Tuning | needs their tuner | needs their tuner | follows the guitar's tuning per note (v1.76) |
| Timing | windowed around the expected time | strum "when the line touches the bar" | window per step, capped at half the gap to the neighbouring steps; late picks get 300 ms to be confirmed |
| Noise / headphones | quiet room, headphones | quiet room, headphones | noise gate, room noise tracking, headphones mode, native mic avoiding Bluetooth call mode |

## What v1.76 adopted

1. **Tuning follower** (Yousician/Simply both need their tuner; Simply "learns on the fly"). Fretline learns how far
   each note sits from standard pitch from steady pitch readings (per note, falling back to all notes), applies it when
   ≥ 8 cents (max 40) to every expected frequency and to the pitch reading, and remembers it between songs. The report
   header shows `tuning ±N cents`. Sim, guitar 30 cents sharp / flat: boogie 54 → 78 and 43 → 71 of 96, arpeggio
   47 → 64 and 57 → 60 of 64, strums 95 → 102 and 99 → 102 of 104; in tune unchanged.
   A single global offset was tried first and cost 12 boogie steps in tune (the sample bank's notes are each off by
   different amounts, as a guitar tuned by ear can be); per-note fixed it.
2. **Spectral whitening for the chord sound** (Klapuri): each note's level is divided by its ±6-semitone neighbourhood
   to the power 0.67 before matching chord templates. Sim strums in tune 100 → 102 of 104; wrong chords unchanged.

## Ideas not done yet

- **Estimate-and-cancel for chords**: find the strongest note, remove its harmonics, look again. Would give a real
  per-string answer for strums (not just "fits this chord best") and could close the "C passes for Em" gap.
- **Learn from the player's own guitar** (Simply's "on the fly", Yousician's reference-player tuning): keep per-note
  timbre (relative harmonic strengths) from confident hits and use it as the template for that note.
- **Chord-change leniency like Yousician's per-string view**: show which string was missing on a strum instead of
  a plain miss (the chord-step dead-string check could run for strums too).

## Sources

- Klapuri, "Multiple Fundamental Frequency Estimation by Summing Harmonic Amplitudes", ISMIR 2006:
  https://archives.ismir.net/ismir2006/paper/000125.pdf
- Yousician patents (Justia): https://patents.justia.com/assignee/yousician-oy
- Klapuri publication list: https://csauthors.net/anssi-klapuri ; Yousician job post (research areas):
  https://auditory.org/mhonarc/2016/msg00036.html
- Yousician support: https://support.yousician.com/hc/en-us/articles/46277332028817-Guitar-sound-recognition-issues
  and https://support.yousician.com/hc/en-us/articles/202893201-Chords-are-not-recognized
- Gibson App launch (Zoundio): https://www.guitarworld.com/news/gibson-unveils-the-gibson-app-the-only-guitar-app-youll-need ;
  user report: https://forum.gibson.com/topic/173784-gibson-app/
- Simply Guitar tips: https://guitar-help.hellosimply.com/en/articles/5135082-improve-note-recognition-in-simply-guitar ;
  JoyTunes engine: https://sdtimes.com/gamification/apps-find-new-ways-spark-interest-music/ ;
  reviews: https://splitmetrics.com/apps/simply-guitar-learn-guitar/id1476695335/ ,
  https://unstar.app/blog/yousician-simply-piano-flowkey-fender-play-music-learning-apps-ranked-2026
