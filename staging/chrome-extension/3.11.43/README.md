# OSMINOG 3.11.43 — UNIFIED AI SESSIONS

This candidate moves provider connections into one session center inside chat settings and removes silent background provider windows.

## Changes

- Every provider connect action now searches for an already-open matching Chrome tab first.
- Connect no longer creates or minimizes a hidden Chrome window.
- A provider page is opened only through the explicit “Open for login” action.
- The working conversation stays inside the OSMINOG chat for ChatGPT, DeepSeek, Google AI, Gemini, Claude, Alice, Nano Banana and generic registry providers.
- The former standalone “Internal tabs” window is removed; its toolbar button now opens the connection center in chat settings.
- The selected chat shows a compact connect action whenever its provider is offline.
- Closing a linked tab or navigating away from the provider emits a disconnect event and shows a reconnect notification naming the provider.
- Existing linked tabs remain reusable across project agents.
- Generic registry providers use the same attached-tab transport, with provider-specific bridges where available.
- The verified 3.11.42 GitHub update-button feed contract and fixed extension key are unchanged.

## Chrome boundary

Protected provider pages cannot be rendered directly inside a Manifest V3 extension because their CSP / X-Frame-Options policies block embedding. OSMINOG therefore keeps the actual project chat inside its own window, attaches an existing authenticated provider tab when needed, and never creates that tab silently. Literal in-window provider WebViews require a native desktop shell or official provider APIs.

## Verification

- 24 JavaScript files pass `node --check`.
- 9 JSON files parse successfully.
- No `chrome.windows.create` background-window path remains.
- The updater file is byte-identical to the working 3.11.42 build.
- Manifest key and permissions are unchanged.
- ZIP integrity passes.
- Root manifest version: `3.11.43`.
- Files: `59`.
- Size: `375069` bytes.
- SHA-256: `db29e7bcf99cee27d50c73ed9e571de47b7e10a21eb4996a628783ba4f103306`.

Runtime verification remains pending until the owner updates from 3.11.42 and exercises attach, disconnect and reconnect with live provider tabs.
