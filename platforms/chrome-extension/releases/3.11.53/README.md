# OSMINOG 3.11.53 — NATIVE WORKSPACE APPS

This corrective release replaces the prototype-button application shell introduced in 3.11.52 with a native desktop application experience inside OSMINOG.

## Root cause

- The 3.11.52 installer deliberately created a normal `button` object sized `190 × 76`.
- Clicking it exposed the generic `code + preview` canvas object.
- The generated application existed, but the user saw a canvas prototype button and developer shell instead of a desktop icon and application window.

## Changes

- Workspace application launchers render as rounded desktop icons with an automatically derived letter and a label below.
- Clicking the icon opens the application in a clean internal window with no URL bar, `index.html` tab or code editor.
- The internal window supports minimize and reopens from the same desktop icon.
- A deliberate `</>` control opens the editable source; `Open app` returns to the clean application window.
- Application iframes allow generated downloads such as PNG export.
- Existing application pairs created by 3.11.52 migrate automatically based on their `canvas-app` link; users do not need to recreate them.
- New application installations persist explicit `launcherStyle`, `appIcon` and `appWindow` properties.
- The autonomous Poseidon executor, built-in image editor, source publication, release publication and button updater remain preserved.

## Verification

- All packaged JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- Static migration checks confirm that legacy 3.11.52 `canvas-app` links become desktop launchers and clean application windows.
- Static interaction checks confirm open, minimize, reopen, developer mode and return-to-app paths.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.53`.
- Files: `59`.
- Size: `403761` bytes.
- SHA-256: `793b06d9e8cbe388c4c6c1e67a781f960362b00d1fe8d7dfd71bf668e43bd3f5`.

Owner runtime verification remains pending until this build is published and the existing Image Studio launcher is reopened.
