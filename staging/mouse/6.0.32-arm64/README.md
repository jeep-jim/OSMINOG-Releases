# Mouse Browser 6.0.32 macOS arm64 — publication staging

`pin.json` binds source `ebe2df44f1fc73fa8fa329c01406a360ebf7eef3`, merged by
OSMINOG PR181 as `7875ad0d3506c12cd2e64c6df298670b8ad9fbaa`, to successful
Mac run44683165219 / attempt1 / job136111128286. The candidate artifact14606425355
and verification artifact14606545088 were downloaded and their raw ZIP hashes
checked against GitHub. Both package hashes were checked against the actual
DMG/ZIP bytes and SHA256SUMS. All four independent source-evidence gates passed.
The real published6.0.29 baseline retains its immutable source, updater and package pins.

`PUBLISH_OWNER` now enables publication of these exact reviewed packages after
the source merge. `validate-template` and `validate` check the complete pin;
`import`, `publish` and `channel` additionally require the recorded provenance,
fresh installed acceptance and verified public assets. No package is rebuilt here.
This staging record is not a claim that publication has already completed.

The 631 task/stress filenames and markers are retained with runtime 6.0.32.
Their installed-process wrapper additionally requires the `stationaryMedia`
stage and `MOUSE_632_STATIONARY_MEDIA_PASS`. Native footer, view-only document
and quiet optional assistant contracts explicitly replace the former UI/editing
expectations in the new 632 checker only. Earlier publishers remain immutable.

The new owner-feedback checker runs on the source verification archive and on
fresh installed evidence before publication. A same-version or newer update
channel cannot be overwritten with different metadata or downgraded.
