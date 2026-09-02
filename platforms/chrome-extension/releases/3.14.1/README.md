# OSMINOG Chrome 3.14.1 — PRESENCE RECOVERY

This recovery release keeps the 3.14 desktop design and restores the working connection model verified against the 3.11.26, 3.11.32 and 3.11.33 builds.

## Restored

- The ChatGPT connect button now starts the connector instead of being intercepted by the Access Center.
- ChatGPT first uses the direct authenticated session and falls back to an attached ChatGPT tab when direct access is unavailable.
- The saved ChatGPT route reconnects on OSMINOG startup and drives the real header status indicator.
- Live Presence is available inside the unified Access Center with view, comment and edit roles.
- Claude, DeepSeek, Gemini and Google AI can again use reusable managed background sessions.
- Missing provider sessions are created in the managed background window; authorization can be surfaced only when user interaction is required.
- Provider requests and tool-result continuations stay on the selected transport for the entire task.
- The session list reports whether a tab is managed and whether its composer passed a live readiness probe.

## Preserved

- The 3.14 application dock, colorful icon art, unified movable windows, browser/editor, graphics studio, modules, team tools, Owner Runtime and Poseidon/GitHub controls remain in place.
- No project storage reset or data migration is performed by this update.

## Verification

- JavaScript syntax and manifest/build metadata checks.
- Connection routing contract checks for direct ChatGPT, attached-tab fallback, Live Presence and managed background sessions.
- ZIP integrity and SHA-256 verification before publication.
