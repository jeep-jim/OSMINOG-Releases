# OSMINOG 3.11.51 — AUTONOMOUS SELF-BUILD

This corrective release reconnects the permanent main chat to the autonomous Poseidon executor.

## Root cause

- The autonomous executor already supported up to 12 tool hops, source writes, repository publication and release publication.
- The chat composer always routed every normal message through the parallel-agent runner instead.
- That runner intentionally completed after one provider answer, so the main chat did not continue autonomously and never reached the source/release workflow.
- The composer also removed attachments before the selected runner could consume them.

## Changes

- The permanent main chat now uses the autonomous executor.
- Personal agent chats retain the parallel runner.
- Tool requests and progress text are shown as separate messages while work continues.
- The executor continues for up to 12 tool hops and six explicit continuation turns until the required mutation succeeds or a concrete blocker is returned.
- `почини сам себя`, `исправь настройки чата` and extension/module repair wording route to Poseidon source tools.
- Explicit canvas/widget/object commands continue to use validated `osminog.patch/v1` canvas actions.
- Attached images, PDFs and code/text files survive composer routing.
- `source_publish` remains the repository command and `release_publish` remains the release/update-feed command, both behind the existing owner confirmation.
- The fixed Chrome key, permissions and updater implementation are unchanged from 3.11.50.

## Verification

- All 24 JavaScript files pass `node --check`.
- All packaged JSON files parse successfully.
- Routing tests cover source self-repair, chat-interface repair, Grafix extension creation, canvas widget creation, repository publication, release publication and ordinary discussion.
- Static executor checks confirm the main chat calls the autonomous runner while personal agents call the parallel runner.
- ZIP integrity passes and `manifest.json` is at the archive root.
- Root manifest version: `3.11.51`.
- Files: `59`.
- Size: `397477` bytes.
- SHA-256: `9d97f10614d89e585b6949405c49b5fe93b81c7c345a099b93b9f59261fe9861`.

Runtime verification remains pending until the owner updates and runs a real `почини сам себя` or module-creation command from the permanent main chat.
