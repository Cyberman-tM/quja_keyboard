# Klingon quja' for AnySoftKeyboard

Local development pack for the Latin-script Klingon quja' layout and its first built-in word-suggestion dictionary. pIqaD remains future work.

The keyboard uses the original four-row quja' arrangement. Multi-character letters such as `tlh`, `ch`, `gh`, and `ng` are emitted with `android:keyOutputText`; uppercase Klingon letters have their own keys.

Build the debug APK from the repository root:

```powershell
.\gradlew.bat :addons:languages:tlhingan:apk:assembleDebug
```

The built-in dictionary is an initial candidate list derived from the reviewed boQwI' crosswalk and weighted corpus frequencies. It currently contains 4,176 single-word candidates; corpus-only forms are not included yet. The APK module and status/launcher artwork were copied from the ASK numpad pack as temporary build assets and need replacement before any distribution. pIqaD support remains future work.
