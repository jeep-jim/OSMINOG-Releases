# OSMINOG 3.11.46 — TEAM CHAT CONTROLS

This release adds a dedicated control surface for the shared Team chat while preserving ordinary provider settings in every personal agent tab.

## Changes

- The gear in “Общий чат” now opens “Настройки общего чата”, not the active provider configuration.
- Personal agent tabs still open the existing agent, provider, connection, colors, tools, Poseidon and GitHub settings.
- Team owners can select the participants used by the next shared mission.
- Work mode can be set to discuss and execute, discuss only, or project review.
- Team rounds can be limited from one to six.
- Every visible agent contribution is prompted and hard-clipped to the selected 80, 180, 350 or 700-word limit.
- A two, five or ten-minute total deadline can stop future agent launches; unlimited mode remains available.
- The optional final shared summary can be enabled or disabled for discussion/review.
- Verified patch auto-application and full-project access remain explicit Team controls.
- A large Stop control appears in Team settings, and the composer send button turns into a red Stop button while the Team cycle is running.
- Stop prevents all new agent requests and discards the result of an already in-flight provider request.
- Team settings persist per project and are locked while a cycle is running.
- Connection Center, fixed extension key, permissions and updater bytes are unchanged from 3.11.45.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- Static contracts confirm the Team settings UI and Team runtime controls are wired.
- Manifest key and permission arrays match 3.11.45 exactly.
- `osminog-folder-updater.js` is byte-identical to 3.11.45.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.46`.
- Files: `59`.
- Size: `384465` bytes.
- SHA-256: `9a1987f255b000597f5e426c5bef348ca78962878677d0efc49e7e8b3d5a9e25`.

Runtime verification remains pending until the owner updates from 3.11.45 and checks the controls in a real multi-agent Team conversation.
