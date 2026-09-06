# OSMINOG 3.21.0 — candidate, not live-verified

## Implemented
- First-open local-folder selection using the existing project folder API.
- Portable workspace snapshot with all current projects and project-scoped ChatGPT-agent histories, threads and pins. Credentials are excluded.
- Remove the 140-message persistence cutoff; model context remains separately bounded.
- Serialize folder writes, report permission/write errors and recover after access returns.
- Include the current project map on every internal agent request, including Google AI. Avoid using the active chat's history for a different agent.
- Drive session expiry/state validation, truthful connection status, list/read/text-import tools and chat memory in explicit Drive workspace sync.
- Read/write assets in the selected user GitHub repository, independently of product-owner access. Existing file writes require its SHA.
- Figma file URL and exact node-id retrieval through the existing token integration.
- Load HTML into the existing manual browser editor and export its current DOM to a selected local folder.

## Boundaries that remain
- The emergency external ChatGPT DOM transport block is retained. No unrelated conversations are read or mirrored.
- relayHttpBase and relayWsBase are empty. External chat Live Presence requires a deployed authenticated connector and provider support; it is not fixed by setting a UI badge to On.
- Google OAuth client ID and real Drive/Figma credentials are not configured in this test environment. Live integrations require account verification.
- Directory selection/renewed filesystem permission requires a user action. Login alone does not transfer local files to another computer.
- This snapshot covers canvas/project data and the main agent histories, not a universal backup of every subsystem's browser storage. Already truncated old messages cannot be reconstructed.
- Browser HTML editor removes scripts using its existing sanitizer. Export preserves external resource URLs and is not an offline dependency bundle or full application build pipeline.
- Figma complex layout translation and full generated-app/manual-editor roundtrip are not live-verified.

## Research basis
- Chrome File System Access: https://developer.chrome.com/docs/capabilities/web-apis/file-system-access
- Persistent permissions: https://developer.chrome.com/blog/persistent-permissions-for-the-file-system-access-api
- Google Drive file scope: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Figma authentication/scopes: https://developers.figma.com/docs/rest-api/authentication/

## Verification
Local: JavaScript syntax; privacy no-mirroring regression; 400-message memory retention, project isolation, secret exclusion, idempotent merge, serial writes and permission failure/retry.
All three CI workflows passed at a517ca9076ab5d3a7fa2423682086ca1b38111d9. Browser tests cover folder onboarding, manual HTML edits/export, cross-project isolation, graphics, chat layout and documents. Live provider sessions remain unverified; runtimeVerified=false.
