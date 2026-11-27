# Mouse Browser 6.0.43 — Mac arm64 only

This stage is unready. No source, merged-source, run, job, artifact or package-byte
claim is populated, and `PUBLISH_OWNER` is absent. Activating it requires the exact
successful Mac source candidate, its ordinary source merge with the same tree,
actual run/attempt/job provenance, archive digests and full DMG/ZIP byte hashes.

The owner has authorized **Mac only**. There is no Linux or Windows 6.0.43 stage,
workflow or publication entry point. Their published 6.0.42 packages and feeds remain
under the previous release contracts. A later platform task requires a new owner
instruction; this stage cannot activate another platform.

The publisher retains byte-frozen 6.0.42 acceptance and independently replays the
actual source and fresh installed evidence. Current upgrade proof starts from
the published Mac 6.0.42 packages and source `ac51d80d4190bce54d8cc5f7017359dcb8fa838c`;
legacy 6.0.29 discovery, download, replacement and profile compatibility remain.

The added 6.0.43 gate binds native chrome and tab shapes, square seams, traffic-light
hover and Nora shape, real search suggestions and address actions, ordinary-page
theme preference and a distinct restart. Raw native input, process records and
full-display/window-crop/shell-reference pixels are independently read. The
build manifest binds the raw 6.0.43 report, process ledger and acceptance bytes.
Source checker bytes must match the independent publisher reader, apart from its
explicit import path substitution.

Local contract checks:

```sh
python3 -m unittest discover -s tools -p 'test_mouse643_*.py' -v
python3 tools/mouse643-release.py validate-template
python3 tools/mouse643-publish-plan.py macos-arm64
```

Synthetic contract tests are not installed or public acceptance. Publication
creates immutable versioned packages, verifies their public bytes, then advances
the existing Mac feed. Public readiness is recorded only after the actual run.
