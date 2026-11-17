# Fretline for Android

A [Capacitor](https://capacitorjs.com/) wrapper that turns the Fretline web app into an installable Android app.

- The app loads the live site (`https://robdevora.github.io/Fretline/`), so changes to `index.html` reach the app without a new APK.
- Native extras: **Open with Fretline** for MIDI / MusicXML / Guitar Pro / ChordPro files, **Share → Fretline**, and downloads from other websites (no browser cross-site blocking).
- Every push that changes `android-app/` builds a new APK with GitHub Actions and publishes it to the
  [`android-latest` release](https://github.com/RobDeVora/Fretline/releases/tag/android-latest):
  `https://github.com/RobDeVora/Fretline/releases/download/android-latest/Fretline.apk`
- The APK is signed with `android/app/fretline.keystore` so updates install over the previous version.
  This key is in the public repo, which is fine for a personal sideloaded app but not for the Play Store.
