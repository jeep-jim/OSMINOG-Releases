# Mouse Browser 6.0.32 macOS arm64 — publication staging

`pin.json` is an unready template. The source commit, PR, merge, run, successful
attempt/job, artifact IDs and all candidate package sizes/checksums remain null
until they are copied from successful exact-source native CI. The real published
6.0.29 baseline keeps its existing immutable source, updater and package pins.

`PUBLISH_OWNER` is deliberately absent. Create it only after the source PR is
merged and exact packages and native evidence are pinned, with the exact text:
`Mouse Browser 6.0.32: publish pinned source and verified Mac packages`.
`validate-template` checks the pending contract; `validate`, `import`, `publish`
and `channel` reject a pending or incomplete pin. No package is rebuilt here.

The 631 task/stress filenames and markers are retained with runtime 6.0.32.
Their installed-process wrapper additionally requires the `stationaryMedia`
stage and `MOUSE_632_STATIONARY_MEDIA_PASS`. Native footer, view-only document
and quiet optional assistant contracts explicitly replace the former UI/editing
expectations in the new 632 checker only. Earlier publishers remain immutable.

The new owner-feedback checker runs on the source verification archive and on
fresh installed evidence before publication. A same-version or newer update
channel cannot be overwritten with different metadata or downgraded.
