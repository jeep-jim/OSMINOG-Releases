# OSMINOG 3.11.48 — LIVE PROVIDER HEALTH

This release fixes external AI agents that appeared connected but failed when Team Room tried to send a message.

## Changes

- Provider state is no longer inferred from a matching open URL alone.
- “On” now requires a live composer probe or an authenticated direct-session probe.
- An existing linked tab that cannot accept a prompt is shown as “Не готов”, with its real probe error.
- Connection Center offers “Переподключить” for a linked but unusable tab.
- Team Room preflights every selected external agent before spending a round.
- Agents that fail the preflight are excluded from that run and receive a precise shared-chat error instead of silently appearing active.
- If no selected agent is ready, Team Room stops before sending any provider request.
- Google AI composer discovery now supports additional textarea, contenteditable, combobox and plaintext editor patterns.
- Composer and send-button discovery traverse open Shadow DOM trees.
- Generic web-chat providers, including Alice, use the broader composer discovery path.
- DeepSeek readiness is verified through its authenticated direct web-session probe.
- Team presence, message avatars, fixed extension key, permissions and updater bytes are unchanged from 3.11.47.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- CSS brace validation passes.
- Static contracts confirm live provider probing, Google/generic composer discovery, Shadow DOM traversal, not-ready UI and Team preflight.
- Manifest key and permission arrays match 3.11.47 exactly.
- `osminog-folder-updater.js` is byte-identical to 3.11.47.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.48`.
- Files: `59`.
- Size: `388634` bytes.
- SHA-256: `e5623a3f2cf9386f03a1891daafd58008f0b7fbbc0f4ae391527095d6369a035`.

Runtime verification remains pending until the owner updates from 3.11.47, reconnects Google AI/Alice and runs a real multi-agent Team mission.
