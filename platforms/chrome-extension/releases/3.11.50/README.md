# OSMINOG 3.11.50 — OSMINOG EXECUTOR RUNTIME

This is a corrective release for the action loop that did not execute reliably in 3.11.49.

## Changes

- Canvas actions use a short dedicated executor instruction instead of receiving the entire Owner Max tool catalog.
- The first executor answer must contain a real `osminog.patch/v1` block or one essential data request.
- Plans, promises and “starting” messages do not count as completion.
- The chat shows factual stage messages when execution starts, when a prose-only answer is rejected and when an additional continuation begins.
- Unknown-duration tasks show an indeterminate marker instead of a fabricated percentage.
- Public protocol names are now `osminog.request/v1`, `osminog.patch/v1`, `osminog.browser_presence/v1` and `osminog.tool_result/v1`.
- Machine context markers are `OSMINOG_CONTEXT_V1` and `OSMINOG_TOOL_RESULT_V1`.
- Live canvas assets are emitted as `osminog://asset/...`.
- Legacy `briefcraft.patch/v1`, `briefcraft.request/v1` and asset URIs are accepted only inside compatibility parsers and are normalized to OSMINOG.
- The source/release publisher, team chat, provider health, fixed extension key and existing updater implementation are preserved.

## Verification

- 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- A focused executor contract test confirms the canvas prompt requires `osminog.patch/v1` and does not emit BriefCraft protocol names.
- Parser tests confirm both new and legacy patch input produce a normalized `osminog.patch/v1` action.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.50`.
- Files: `59`.
- Size: `397097` bytes.
- SHA-256: `aa86483f1d358836cf6288283761adf0c5304406c418e4a7dded463dc502f0da`.

Runtime verification remains pending until the owner updates and runs a real canvas creation command from the OSMINOG chat.
