# Mouse Browser 6.0.32 Windows x64 — publication staging

`pin.json` binds source `ebe2df44f1fc73fa8fa329c01406a360ebf7eef3`, merged by
OSMINOG PR181 as `7875ad0d3506c12cd2e64c6df298670b8ad9fbaa`, to successful
Windows run44683165197 / attempt1. Both jobs passed: builder136111172537 on
windows-2022 and modern136115846365 on windows-latest, using the same installer.
Candidate artifact14605697368 and verification artifact14606565019 have verified
raw ZIP hashes. The actual installer size and SHA256 match the source manifest.
Installed verification and the independent task, owner-feedback and hidden
scrollbar gates passed on the downloaded source evidence.

`PUBLISH_OWNER` now enables publication after the verified source merge.
The publisher rejects an unready or incomplete pin and independently installs
and verifies the same installer before advancing the public Windows channel.
This staging record does not claim that publication has already completed.

The shared scrollbar gate reads the actual `mouse-629-ui-regressions.json`
archive member, validates its Windows632 identity and restoration state, then
checks its unchanged scrollbar payload and rendered frames. The temporary
standalone JSON is not an uploaded source artifact.

The actual published 6.0.29 baseline remains pinned. Retained 631 task/stress
report filenames and markers continue to be validated with version 6.0.32.
