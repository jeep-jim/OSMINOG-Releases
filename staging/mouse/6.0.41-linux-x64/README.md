# Mouse Browser 6.0.41 — linux-x64

This activation pins the accepted Mouse Browser 6.0.41 source and the exact independently verified Linux packages. The publisher imports these bytes and must complete fresh installed verification before public release. Publication order: **Mac → Linux → Windows**.

## Accepted source and immutable packages

[Source PR218](https://github.com/jeep-jim/OSMINOG/pull/218) was accepted and merged with an ordinary merge. The tested head is a parent of that merge, and both trees are identical.

| Provenance | Verified value |
|---|---|
| Tested source | `3a32e02a8893b4c2f1397cd0a08e94af737f42fc` |
| Ordinary source merge | `ceaef4d7d22d91a2b5ab4decd05f1c16e5ea9dd1` |
| Tested and merged tree | `bf4b60b717d14479f621709ba242ed0c0e569b70` |
| Linux source run | [45830569937](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569937), attempt 1 |
| Successful Ubuntu 22.04 job | `139945933865` |
| Successful Ubuntu Noble job | `139953041288` |
| Candidate artifact | `15122917500`, 229722369 bytes |
| Candidate ZIP SHA256 | `ed87d8221f42b13d783602b5582156d5fb6702c9fd23fb76a6c5a246b2ebb5cb` |
| Primary verification artifact | `15121499521`, 72197946 bytes |
| Primary verification ZIP SHA256 | `924580064f3fc4a2ddcf0816090211ec82e7dcb6bd69ef900d27acc68126ebb6` |
| Noble verification artifact | `15122679659`, 11434232 bytes |
| Noble verification ZIP SHA256 | `13fe2c6ef738a61991789f0e514d257ad01712c2e4f72a1b77542e21f5ee5ac2` |

The primary job ran on 2026-11-26 from 13:35:13Z to 13:47:47Z; the Noble job ran from 13:47:50Z to 13:51:18Z. All three artifact creation times are within their corresponding successful job intervals. Their complete ZIP sizes and SHA256 hashes, source/run/attempt bindings and actual package bytes were independently checked. ZIP digests are distinct from the inner verification JSON hashes.

| Package | Bytes | SHA256 |
|---|---:|---|
| Mouse-Browser-6.0.41-Linux-x64.AppImage | 128822176 | `d68443f65a82d108162a2f528c4898abc8406150f270a19e09b3a257f84238f0` |
| Mouse-Browser-6.0.41-Linux-x64.deb | 101395748 | `42b1f88a013fffe8b786b1d2db910f3662b9f1f85f334a7042525e2a19571532` |

## Independent source acceptance

The complete retained Linux publisher evidence chain, current 6.0.40 upgrade evidence, all four current readers and the separate Noble dependency/install/native/profile evidence passed on the actual source artifacts. Source helper Git blobs and checker bytes were also compared. [Publisher PR93](https://github.com/jeep-jim/OSMINOG-Releases/pull/93) binds the exact 641 glass-library geometry without modifying frozen older validators.

The installed source gates cover classic/grid page identity, native blank-page drag and held edge transfer, pane insertion, tiny headers, separate theme surfaces, exact-host AdBlock exceptions with actual request ledgers, native Settings entry paths, persistence, media removal with ongoing site audio, extension popup destruction, retained file/library/profile input and same-run predecessor performance. Existing lower AI panes remain explicitly labelled fixtures; ordinary new AI links use actual trusted native anchor input.

The same accepted source also passed [Mac45830569948](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569948) and [Windows45830569936](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569936), including the separate modern Windows job. Source acceptance and offline re-reading do not replace the fresh publisher installation.

## Ordered publication and required fresh verification

The preceding [Mac publisher 45844915958](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45844915958), attempt 1 on activation merge `d1c2ceb2cef26deae1d0cefc02542b194f1ebe3f`, completed successfully. Its fresh installed, release, channel and shipped-updater steps all succeeded. The public Mac release was published at 2026-11-26T15:32:17Z; its five asset identities and canonical 6.0.41 feed match the accepted pin.

Before this Linux activation is merged, the existing Linux PR contract must additionally download both public Mac DMG and ZIP anonymously and verify their full sizes and SHA256 against the Mac pin. Pull-request publication jobs are skipped, so this order gate does not publish Linux. The independent Mac fresh-artifact audit must also pass before merge. The Linux push contract repeats the same full public predecessor gate before the Linux publisher starts.

The Linux publisher must import the exact AppImage and deb, install and exercise them on a fresh Ubuntu 22.04 X11 desktop, recompute the retained and current readers, and compare the immutable public release asset sizes and digests with the verified local packages. It then writes the versioned and canonical feeds and runs the actual shipped 6.0.40 updater to anonymously discover and fully download both package formats. Final acceptance separately reads back both public feed files; the archived updater receipts do not substitute for that versioned-feed readback. The existing `previous` and `currentPrevious` blocks remain bound to real immutable 6.0.40 bytes.

Ubuntu 22.04 and Noble CI evidence does not claim testing on the owner's Linux Mint device. All existing sandbox, profile, security, native input, graphics and performance gates remain active. The dedicated 641 write/restart process budgets remain 270/120 seconds, with inner scenario budgets of 240/90 seconds and a separate native-input ledger capped at 160; retained combined features remain capped at 230.

Windows activation follows only after the public Mac and Linux packages and feeds have been verified.

Local activation contract checks:

```sh
python3 tools/mouse641-release.py validate-template
python3 tools/mouse641-linux-release.py validate-template
python3 tools/mouse641-windows-release.py validate-template
```

All five required PR checks must pass before the activation merge. The push workflow independently verifies ordered public predecessors and then performs fresh Linux verification before publication.
