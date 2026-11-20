# Mouse Browser 6.0.32 Windows x64 — publication staging

`pin.json` is an unready template. Unknown commit, run, job, artifact, size and
checksum values are intentionally null. Fill them only from the successful
exact-source Windows CI run, including both supported Windows runner jobs.

`PUBLISH_OWNER` is intentionally absent. Create it with the exact text
`Publish verified Mouse Browser 6.0.32 Windows x64` only after the source PR is
merged and the immutable installer and verification artifacts are pinned.
The publisher rejects an unready or incomplete pin and independently installs
and verifies the same installer before advancing the public Windows channel.

The actual published 6.0.29 baseline remains pinned. Retained 631 task/stress
report filenames and markers continue to be validated with version 6.0.32.
