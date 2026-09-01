# OSMINOG 3.11.47 — TEAM LIVE PRESENCE

This release makes every active AI participant visible and identifiable in shared and personal chats.

## Changes

- Every visible response card now keeps an author avatar, author name, provider badge and timestamp.
- Team source responses retain their agent color so authors remain distinguishable while scrolling.
- While an agent is thinking, the shared chat shows a live activity card with provider avatar, agent name, current action and animated typing dots.
- The activity card reports the current Team round and response position as well as a live percentage.
- The exact active agent is highlighted in the left Team chat list with “Пишет в «Общий чат»”.
- Selected teammates waiting for their turn show a separate queued state instead of looking idle.
- The Team participants panel mirrors the same writing and queued states.
- Personal agent chats use the same rich thinking card with avatar, elapsed time, estimated remaining time and progress.
- Stop behavior and all Team chat controls from 3.11.46 remain unchanged.
- Connection Center, fixed extension key, permissions and updater bytes are unchanged from 3.11.46.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- CSS brace validation passes.
- Static contracts confirm message avatars, provider identity, live progress, typing dots, active-agent highlighting and queued states.
- Manifest key and permission arrays match 3.11.46 exactly.
- `osminog-folder-updater.js` is byte-identical to 3.11.46.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.47`.
- Files: `59`.
- Size: `387148` bytes.
- SHA-256: `dabcd956e4f1ad1e9d028c4abd3e6b30a071f3105805976f025e04e60b8e0664`.

Runtime verification remains pending until the owner updates from 3.11.46 and checks a real multi-agent Team conversation.
