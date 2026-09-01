# OSMINOG 3.11.49 — POSEIDON AUTONOMOUS RUNTIME

This release restores the useful autonomous behavior from 3.11.34 and makes it explicit, bounded and verifiable.

## Changes

- Action requests no longer finish after a plan, promise or one status message.
- Poseidon can continue through up to 12 tool hops and six automatic continuation turns.
- The chat shows short progress messages between tool steps without exposing hidden chain-of-thought.
- Canvas edits, OSMINOG source edits, repository writes and releases have separate completion rules.
- A canvas request is complete only after a real patch is applied.
- A source task is complete only after `write_dev_file` succeeds.
- “Запиши в репозиторий” invokes an owner-confirmed source archive operation.
- “Выпусти версию” invokes an owner-confirmed release operation that archives source, uploads the verified ZIP and updates the updater feed.
- The local Poseidon source folder can be packaged into a deterministic STORE-method ZIP entirely inside the extension.
- The package builder validates the manifest, version, fixed extension key and JSON files, then calculates SHA-256 before publication.
- Private source/package publication and public release publication are restricted to the two owner repositories.
- GitHub release asset upload permission is requested together with API permission.
- Team chat, provider health checks, the fixed extension key and the existing updater implementation are preserved.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- CSS brace validation passes.
- The in-app ZIP builder produced a valid archive in an isolated test, including a UTF-8 filename.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.49`.
- Files: `59`.
- Size: `396224` bytes.
- SHA-256: `69c382a6479419c31bc820ba4fb6412f3b709db75450f4d86a9e4a787546546e`.

Runtime verification remains pending until the owner updates from 3.11.48 and runs one real source-edit and release-command cycle from the OSMINOG chat.
