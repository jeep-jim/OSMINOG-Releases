# OSMINOG 3.11.42 — POSEIDON MAX ACCESS

This candidate unifies the capability contract exposed to external ChatGPT, internal agents and custom providers.

## Changes

- External ChatGPT Presence receives the real Owner Max capability manifest instead of the canvas-only subset.
- Tool execution supports up to eight calls per hop and eight consecutive tool-result hops.
- Image objects can be delivered to an AI as real image bytes through `read_asset`.
- AI-generated or externally hosted assets can be placed on the canvas through `asset_create`.
- Added project tools: list, create, switch and rename.
- Added agent tools: create, update, remove and delegate.
- Added an owner-confirmed custom command registry supporting prompt, tool and chained commands.
- Read-only external roles cannot invoke mutating tools.
- Existing validated canvas patches, Undo, Poseidon source-folder guard and owner-confirmed GitHub writes are preserved.
- The 3.11.41 GitHub update-button feed contract is unchanged.

## Verification

- 24 JavaScript files pass `node --check`.
- 9 JSON files parse successfully.
- Custom command registry smoke test passes.
- ZIP integrity passes.
- Root manifest version: `3.11.42`.
- Files: `59`.
- Size: `372440` bytes.
- SHA-256: `a8651f1467291743378b7ad6a151208368aca51bf9ab85f9f4a63389562d6ca2`.

Runtime verification remains pending until the owner updates from 3.11.41 and exercises the new Presence tools.
