# OSMINOG 3.11.52 — WORKSPACE APP RUNTIME

This corrective release makes application creation from the permanent chat deterministic.

## Root cause

- Version 3.11.51 correctly routed long-running commands into the autonomous executor.
- Application requests still depended on the connected model returning a valid `osminog.patch/v1` canvas mutation.
- The exact owner wording used the Russian infinitive `сделать`; the app-intent classifier only recognized imperative forms such as `сделай`.
- When the model returned prose or an HTML draft without a patch, no real window or launcher was installed.

## Changes

- Adds a dedicated `app` execution mode for application, editor, player, studio and extension requests inside OSMINOG.
- Recognizes natural Russian forms including `сделать`, `создать`, `написать`, `реализовать` and `добавить`.
- The connected AI now produces one standalone HTML document with inline CSS and JavaScript.
- OSMINOG itself validates the response and deterministically creates:
  - a hidden, editable code application window;
  - a visible desktop launcher linked to that exact window.
- The launcher opens its application on a single click.
- Application installation is applied immediately for an explicit creation command and remains undoable.
- HTML source is kept inside an editable OSMINOG code object in preview mode.
- If provider output has no usable HTML, OSMINOG installs a built-in working fallback instead of returning another promise.
- The image-editor fallback supports file selection, drag/drop, brush, eraser, line, brush size/color, undo, clear, grayscale, invert and PNG export.
- The runtime is provider-independent and works with any provider routed through the permanent chat.
- Existing canvas patches, Poseidon source repair, repository/release publishing, team chat, fixed extension key and button updater are preserved.

## Verification

- All 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- Routing tests pass for the exact screenshot request plus alternate app, source repair, canvas widget, canvas edit and ordinary chat wording.
- Patch validation preserves `action`, `actionValue`, `codeViewMode` and `codeSplit`.
- Static runtime checks confirm app responses call the deterministic installer instead of the canvas patch retry.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.52`.
- Files: `59`.
- Size: `402198` bytes.
- SHA-256: `bd9b87445f0538976740a9e3652b76a192acf4fc0d75d416e8b86c2459dc321e`.

Runtime verification remains pending until the owner updates and repeats the image-editor request from the permanent main chat.
