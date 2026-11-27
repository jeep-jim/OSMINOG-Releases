# Mouse Browser 6.0.42 — linux-x64

This directory binds the 6.0.42 candidate to immutable CI outputs. In the unready state, source, job, artifact and package claims remain empty, and `PUBLISH_OWNER` must not exist. Activation records those exact verified claims in `pin.json` and adds the owner trigger; it does not by itself establish a public release.

Publication order is **macOS → Linux → Windows**. The accepted source and its ordinary merge must have identical trees, and all ready platforms must bind that same source, merge and pull request. Candidate archive digests, verification archive digests, successful run/attempt/job intervals and package byte hashes must come from actual outputs. Linux additionally requires Noble; Windows additionally requires modern Windows.

The publisher imports exact tested packages, repeats installed native acceptance, replays independent readers over raw process and image evidence, publishes immutable versioned packages, reads them back anonymously in full, then advances the existing feed. It preserves previous releases. The active mouse.black synchronizer consumes independently published platform feeds after full download verification.

The 642 reader retains rendering, AdBlock, Settings and flexible-workspace acceptance. It additionally requires actual same-site navigation in the original WebContents and corner-control restoration of the saved grid. Current upgrade evidence must start from published 6.0.41; legacy629 compatibility remains. The raw feature report names retain their established suite identifiers.

The controls642 gate also requires synchronized white/black tone presets and sliders, Settings-only interface language, actual OS input-layout selection with physical-key evidence, consent-only RU/EN correction, preserved paragraph content and native Undo, and saved tones restored in a distinct process. Independent readers verify the actual process records and native images. Linux system-layout selection is supported on X11; Wayland is reported unavailable.

Local contract commands:

```sh
python3 -m unittest discover -s tools -p "test_mouse642_*.py" -v
python3 tools/mouse642-release.py validate-template
python3 tools/mouse642-linux-release.py validate-template
python3 tools/mouse642-windows-release.py validate-template
```

Synthetic mutation tests validate rejection behavior; they do not establish installed or public release acceptance. Activation and final receipts must be recorded only after actual successful checks.
