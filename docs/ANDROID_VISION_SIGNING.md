# OSMINOG Vision Android signing and release

The Vision package ID is `com.osminog.vision`. Android only accepts in-place updates when every APK is signed by the same private key as the installed package.

The private keystore is intentionally not committed to this public repository. Store these four repository Actions secrets in `jeep-jim/OSMINOG-Releases`:

- `OSMINOG_ANDROID_SIGNING_KEYSTORE_B64`
- `OSMINOG_ANDROID_SIGNING_STORE_PASSWORD`
- `OSMINOG_ANDROID_SIGNING_KEY_ALIAS`
- `OSMINOG_ANDROID_SIGNING_KEY_PASSWORD`

The private signing archive generated for the initial Vision release contains the keystore and the exact values for those secrets. Keep an offline backup and never commit the archive, JKS, base64 value, or passwords.

## Release flow

1. Build and test the Android Vision source in `jeep-jim/OSMINOG`.
2. Record the successful source workflow run ID, artifact name, version name/code, application ID and source APK path in `staging/android-vision/<version>/release.json`.
3. Add `PUBLISH-READY` only after the four signing secrets exist.
4. The release workflow downloads the unsigned APK artifact, signs it with the persistent keystore, verifies the APK signature and package identity, installs and launches it in an API 35 emulator, and captures the first screen.
5. It publishes an immutable GitHub release and advances `channels/android-vision/dev.json` only after remote asset size and SHA-256 readback pass.

The app updater independently checks the HTTPS feed, APK size, SHA-256, package ID, increasing version code and signing certificate before opening Android's installer. Android still requires the user to confirm the installation.

Do not rotate the signing key after the first release. Losing it means existing installations cannot receive in-place updates; users would have to uninstall and reinstall, losing app-local data.
