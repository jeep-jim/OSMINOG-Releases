# Mouse 6.0.44 — pinned Mac arm64 release

**Mac 6.0.44 published: source, publisher and public verification PASS.**
Only macOS arm64 was published. Windows/Linux remain on 6.0.42 unchanged.

## Accepted source and immutable pin

| Binding | Accepted value |
| --- | --- |
| Source HEAD | `ad9b8c217da8917f95a2d672e62790f474daef4b` |
| Merged source PR | [OSMINOG#226](https://github.com/jeep-jim/OSMINOG/pull/226) |
| Source merge | `161f2ebda378c48c1ae714c671c2d91830c4558f` |
| Successful source run | [46106499427](https://github.com/jeep-jim/OSMINOG/actions/runs/46106499427), attempt 1 |
| Successful source job | `140860337521` |
| Candidate artifact | `mouse-arm64-candidate`, ID `15248501921` |
| Verification artifact | `mouse-arm64-verification`, ID `15247979966` |
| Publisher activation merge | `1e85e195bcee576ce15f86f4e5a1289e4209e190` |

[Immutable pin](https://github.com/jeep-jim/OSMINOG-Releases/blob/1e85e195bcee576ce15f86f4e5a1289e4209e190/staging/mouse/6.0.44-arm64/pin.json)
records the accepted run/attempt/job, both artifact archive SHA-256 hashes,
package lengths/hashes and published 643/legacy 629 baselines.

| Package | Bytes | SHA-256 |
| --- | ---: | --- |
| `Mouse-Browser-6.0.44-mac-arm64.dmg` | 132744234 | `c489a46d5fd32888533e91ccdaa4f069dc7b461a3c41d8b0d4cf2286e31bb375` |
| `Mouse-Browser-6.0.44-mac-arm64.zip` | 132788013 | `bc389f06274ef7b72ee28bc1255e2265cf1bc9f205e065bae5d1955a0d88e6af` |

## Successful publisher and public verification

[Run 46108907151](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/46108907151), attempt 1, native
[job 140868484487](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/46108907151/job/140868484487), at the activation merge above: **SUCCESS**, completed 28 November 2026 at 12:14:39 KRAT.
[Publisher acceptance](https://github.com/jeep-jim/OSMINOG/blob/main/docs/desktop/evidence/mouse644-publisher-acceptance.json)
records fresh native, actual 643→644/legacy 629→644 update/profile and name gates.
Reduced motion passed with 2 source frames and 1 fresh-publisher frame.

| Result | Verified value |
| --- | --- |
| [Release](https://github.com/jeep-jim/OSMINOG-Releases/releases/tag/quadro-macos-v6.0.44-arm64) | ID `461318997`, tag `quadro-macos-v6.0.44-arm64`, published 28 November 2026 at 12:14:08 KRAT |
| Publisher verification artifact | ID `15248993797`, 117577119 bytes |
| Artifact SHA-256 | `9678f9bd99e3b8226f273e7237a7e03e38e3955432cee019aefd97c75a962190` |
| [Public receipt](https://github.com/jeep-jim/OSMINOG/blob/main/docs/desktop/evidence/mouse644-public-macos.json) | PASS, 28.11.2026 12:17:27 KRAT |
| Public receipt SHA-256 | `8c2027053d6e070bcc102b49487146d32f14c9f34e947238f6b099c04071764d` |

## Identity and release gates

Source CI verified **Mouse** through native FileManager/Bundle checks, 56
bundle localizations, website themes/filters, private/restart, performance,
actual 643 update/profile retention.
Physical `Mouse Browser.app`, executable `Mouse Browser`, App ID
`com.osminog.desktop.preview` and profile `Trader OS` remain compatible with 643.
The Mac menu/About names are also set to Mouse. These are installed CI checks,
not a test of the owner's Mac or every website.

The publisher imported these exact DMG/ZIP bytes **without rebuilding**, checked
source/run/attempt/job, artifact provenance/hashes and the merged helper tree,
then repeated fresh native and published 643/legacy 629 updater/profile gates.
Raw branding receipts bind names to actual install/update paths. Earlier
publishers, pins and release assets are preserved; frozen validators remain
unchanged. Only the [Mac feed](https://github.com/jeep-jim/OSMINOG-Releases/blob/3c84b8e9ea6e4afd915987b7509a527de10b13ca/channels/mouse/macos-arm64.json) advanced after uploaded assets passed public byte/hash checks. Separate anonymous 629/643 updater probes accepted the exact DMG.

The final public receipt confirms feed/catalog 6.0.44, HTTP 200 and the current
Mac link on `/`, `/en/`, `/ru/`, the full DMG length/SHA-256, HEAD 200/Range 206.
It covers the DMG download; both release packages matched the pin in publisher
verification. Windows/Linux catalog entries remained unchanged. All times above
are KRAT (UTC+7). Scope and limits: [task record](https://github.com/jeep-jim/OSMINOG/blob/main/docs/desktop/2026-11-28-mouse644-filter-updates-page-themes.md).
