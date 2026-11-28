# Mouse 6.0.44 — pinned Mac arm64 publication

**Source accepted and pinned; publication pending.** `pin.json` is ready for the
authorized publisher and `PUBLISH_OWNER` is present. Fresh publisher native
verification, package upload, Mac channel advancement and mouse.black
verification remain pending.

## Accepted source

| Binding | Accepted value |
| --- | --- |
| Source HEAD | [`ad9b8c217da8917f95a2d672e62790f474daef4b`](https://github.com/jeep-jim/OSMINOG/commit/ad9b8c217da8917f95a2d672e62790f474daef4b) |
| Merged source PR | [OSMINOG#226](https://github.com/jeep-jim/OSMINOG/pull/226) |
| Source merge | [`161f2ebda378c48c1ae714c671c2d91830c4558f`](https://github.com/jeep-jim/OSMINOG/commit/161f2ebda378c48c1ae714c671c2d91830c4558f) |
| Successful native run | [46106499427](https://github.com/jeep-jim/OSMINOG/actions/runs/46106499427), attempt 1 |
| Successful native job | [140860337521](https://github.com/jeep-jim/OSMINOG/actions/runs/46106499427/job/140860337521) |
| Candidate artifact | `mouse-arm64-candidate`, ID `15248501921` |
| Verification artifact | `mouse-arm64-verification`, ID `15247979966` |

Both artifact ZIP SHA-256 hashes and the exact DMG/ZIP byte lengths and SHA-256
hashes are recorded in `pin.json`. The source run verified the installed and
updated display name `Mouse`, all 56 bundle localizations, website themes,
network filters, performance, actual 6.0.43 update/profile retention and the
reduced-motion scenario with two recorded frames.

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

`PUBLISH_OWNER` contains exactly:

```text
Mouse Browser 6.0.44: publish pinned source and verified Mac packages
```

1. Merge the activation PR after its contract checks pass. The ordinary push
   trigger on the release repository's main branch starts `publish-mouse644.yml`.
2. The publisher imports the pinned packages, checks their exact successful
   source job/attempt, artifact origin/time and merged source HEAD, and repeats
   the installed native checks on macOS arm64.
3. After immutable package upload and public byte/hash verification, the
   publisher advances only the existing Mac channel.
4. Verify the channel and mouse.black catalog/link/full DMG hash independently.

Local checks:

```sh
python3 tools/mouse644-release.py validate-template
python3 tools/mouse644-publish-plan.py macos-arm64
```

The final command must print `publish=true` for this exact authorized pin.
The workflow retains all frozen and current contract suites. Pin validation
does not replace the independent source/fresh-install or public-byte gates.

After activation, `publish-mouse644.yml` imports (does not rebuild) those bytes,
repeats installed native checks on macOS arm64, uploads immutable packages,
verifies public download hashes and advances only the existing Mac channel.
Its verification artifact is `mouse644-release-verification-attempt-N`.
Verify `https://mouse.black/downloads.json`, the English/Russian download links,
full DMG byte length/SHA-256, HEAD and Range responses after the catalog sync.
