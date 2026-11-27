# Mouse Browser 6.0.42 — windows-x64

This is an unready, fail-closed staging template. No source commit, successful job, artifact or package digest is claimed until the corresponding immutable CI outputs have passed independent acceptance. It must not have `PUBLISH_OWNER` while `ready` is false.

Publication order is **macOS → Linux → Windows**. The accepted source and its ordinary merge must have identical trees, and all ready platforms must bind that same source, merge and pull request. Candidate archive digests, verification archive digests, successful run/attempt/job intervals and package byte hashes must come from actual outputs. Linux additionally requires Noble; Windows additionally requires modern Windows.

The publisher imports exact tested packages, repeats installed native acceptance, replays independent readers over raw process and image evidence, publishes immutable versioned packages, reads them back anonymously in full, then advances the existing feed. It preserves previous releases. The active mouse.black synchronizer consumes independently published platform feeds after full download verification.

The 642 reader retains rendering, AdBlock, Settings and flexible-workspace acceptance. It additionally requires actual same-site navigation in the original WebContents and corner-control restoration of the saved grid. Current upgrade evidence must start from published 6.0.41; legacy629 compatibility remains. The raw feature report names retain their established suite identifiers.

Local contract commands:

```sh
python3 -m unittest discover -s tools -p "test_mouse642_*.py" -v
python3 tools/mouse642-release.py validate-template
python3 tools/mouse642-linux-release.py validate-template
python3 tools/mouse642-windows-release.py validate-template
```

Synthetic mutation tests validate rejection behavior; they do not establish installed or public release acceptance. Activation and final receipts must be recorded only after actual successful checks.
