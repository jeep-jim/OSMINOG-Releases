# OSMINOG 3.11.44 — CONNECTION CENTER UI REPAIR

This release repairs the 3.11.43 connection UI regression while preserving the safe existing-tab session model and the proven update button.

## Changes

- Restores the familiar “Internal tabs” interface as a polished unified AI connection center.
- Every connect action from chat, agent settings, Modules, desktop provider shortcuts, the provider catalog and Google AI opens the same center.
- The center lists every active provider session separately.
- Quick access contains the preinstalled chat providers plus every provider added through Modules, Media Crew or desktop shortcuts.
- An already-open provider tab is detected and can be attached without creating a new tab.
- “Open for login” remains an explicit visible-tab action; no hidden or minimized provider window is created.
- The small grey header connect button is removed.
- A large, clear connect button is restored inside an empty disconnected chat.
- The previous agent/chat interface remains intact.
- Team and settings panes now respond to the actual chat-window width and become overlays when the window is too narrow, instead of crushing the conversation.
- Direct ChatGPT transport, DeepSeek existing-tab transport, reconnect notifications and Custom OpenAI-compatible transport are preserved.
- The 3.11.43 fixed extension key, permissions and updater bytes are unchanged.

## Verification

- 24 JavaScript files pass `node --check`.
- 9 JSON files parse successfully.
- Connection-center smoke test passed with connected, core, selected-module and desktop-shortcut providers.
- CSS structure check passed.
- No `chrome.windows.create` background-window path exists.
- The updater is byte-identical to 3.11.43.
- Manifest key and permissions are unchanged.
- ZIP integrity passes.
- Root manifest version: `3.11.44`.
- Files: `59`.
- Size: `378050` bytes.
- SHA-256: `ada1b5e73bd257ca01edbdf449ed2d4e5aecffcf9947638d5c262d8e1a764c6b`.

Runtime verification remains pending until the owner updates from 3.11.43 and tests DeepSeek plus one provider added through Modules.
