# Mouse 6.0.44 — Mac arm64 publication template

This stage is **not ready**. The source SHA, merged PR, successful native run,
attempt/job, verification and package artifact IDs/hashes and DMG/ZIP hashes must
be filled from the actual accepted candidate. There is no PUBLISH_OWNER trigger.
Synthetic rejection tests do not mean the application has passed native checks.

Only macOS arm64 is authorized. Windows/Linux stay on 6.0.42. Earlier publishers,
pins, release assets and feeds are immutable; 644 wraps the frozen 643 validators
and retains the exact published 643 and legacy 629 update/profile tests.

The added gates independently read 644 subscription/theme proof and actual
Finder/Bundle names before and after the published 643 in-app update. The native
publisher repeats the source Swift display-name check against its fresh install.
Both raw branding receipts are hashed, bound to their installation paths and
matched to the source manifest or actual update receipt. All source helpers are
fetched from the pinned Git tree; the independent readers and Swift must match.

## Authorized execution

1. Accept a successful exact-source Mac CI run and merge its PR.
2. Populate pin.json from those verified bytes and identifiers.
3. Validate the complete source and independent evidence.
4. Add PUBLISH_OWNER containing exactly
   `Mouse Browser 6.0.44: publish pinned source and verified Mac packages`
   and merge the activation PR into the release repository's main branch.
5. The ordinary push trigger on main starts publish-mouse644.yml. No manual
   dispatch, token extraction or alternate project credentials are needed.
6. Only after fresh installed checks, immutable package upload and public hash
   verification may the publisher advance the existing Mac channel.
7. Verify the channel and mouse.black catalog/link/full DMG hash independently.

Local checks:

```sh
python3 -m unittest discover -s tools -p 'test_mouse642_*.py' -v
python3 -m unittest discover -s tools -p 'test_mouse643_*.py' -v
python3 -m unittest discover -s tools -p 'test_mouse644_*.py' -v
python3 -m py_compile tools/mouse644-*.py
python3 tools/mouse644-release.py validate-template
python3 tools/mouse644-publish-plan.py macos-arm64
```

The final command must print publish=false until actual acceptance is complete.

`pin.json` requires the accepted source HEAD, merged PR and merge commit, native
run/attempt/job, both artifact IDs and whole-archive SHA-256 hashes, and each
DMG/ZIP byte length and SHA-256. The inherited import validator checks the exact
successful source job, artifact origin/time, merged source HEAD and package
bytes. Never fill these fields from a failed attempt or an unrelated rerun.

After activation, `publish-mouse644.yml` imports (does not rebuild) those bytes,
repeats installed native checks on macOS arm64, uploads immutable packages,
verifies public download hashes and advances only the existing Mac channel.
Its verification artifact is `mouse644-release-verification-attempt-N`.
Verify `https://mouse.black/downloads.json`, the English/Russian download links,
full DMG byte length/SHA-256, HEAD and Range responses after the catalog sync.
