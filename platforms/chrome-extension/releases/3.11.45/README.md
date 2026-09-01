# OSMINOG 3.11.45 — UNIFIED TEAM ROOM ROUTING

This release repairs the Team mode routing regression while preserving the working Connection Center and folder update button.

## Changes

- Team mode now always opens the shared “Общий чат” instead of whichever personal agent tab was active.
- Every selected agent reply is routed to the shared main team feed.
- Team messages use a serialized write queue so concurrent replies cannot overwrite or reorder the stored conversation.
- Agent name, provider, color and team-source metadata are preserved in the common feed.
- Personal agent tabs remain available for direct one-to-one conversations.
- A personal tab is explicitly labelled as a personal chat in Team mode.
- Clearing the team transcript removes team messages from the shared feed without deleting unrelated main-chat history.
- The Connection Center, existing-tab provider transport, fixed extension key, permissions and updater bytes are unchanged from 3.11.44.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- Static routing checks confirm no Team entry point uses `team:false`.
- Team events target the main shared feed through a serialized queue.
- Manifest key and permissions are unchanged from 3.11.44.
- The updater is byte-identical to 3.11.44.
- ZIP integrity passes.
- Root manifest version: `3.11.45`.
- Files: `59`.
- Size: `378444` bytes.
- SHA-256: `dbecb4c641c2f5ef7a501d796ae1771033f323b2cee8c9302f2cf574325d3248`.

Runtime verification remains pending until the owner updates from 3.11.44 and runs a real multi-agent Team conversation.
