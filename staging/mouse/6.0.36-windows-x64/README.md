# Mouse Browser 6.0.36 — windows-x64

Published on **2026-11-21 at 15:23:41 UTC** from the exact installer in [pin.json](pin.json). The public GitHub release is marked as a prerelease.

## Source and verification

| Evidence | Exact reference |
|---|---|
| Tested source | [`7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3`](https://github.com/jeep-jim/OSMINOG/commit/7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3) |
| Source merge | [PR190](https://github.com/jeep-jim/OSMINOG/pull/190), [`94d5c3d1b7fa7652a0f55b73ba3847458b3d053f`](https://github.com/jeep-jim/OSMINOG/commit/94d5c3d1b7fa7652a0f55b73ba3847458b3d053f) |
| Source native CI | [Run 44913896890](https://github.com/jeep-jim/OSMINOG/actions/runs/44913896890), attempt 1; primary job 136875265386 and modern Windows job 136879429468 both succeeded |
| Fresh installation and publication | [Run 44917454695](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/44917454695), attempt 1, job 136886078196; **success** |
| Public release | [mouse-windows-v6.0.36-x64](https://github.com/jeep-jim/OSMINOG-Releases/releases/tag/mouse-windows-v6.0.36-x64) |

The same installer passed both source Windows jobs and another fresh installation in the publisher. Installed UI, task/stress, profile preservation and current 6.0.34-to-6.0.36 upgrade checks passed. Separately, the actual released 6.0.29 updater discovered 6.0.36 and anonymously downloaded and verified the installer; the 6.0.36 updater reported the version as current.

## Public package

| Package | Bytes | SHA-256 |
|---|---:|---|
| [Windows x64 installer](https://github.com/jeep-jim/OSMINOG-Releases/releases/download/mouse-windows-v6.0.36-x64/Mouse-Browser-6.0.36-Windows-x64.exe) | 125834363 | `443496508013d5734e8a81c7eb0ddb33cedad4149440da3c04ff891486c6cf61` |

[Current update feed](https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/windows/mouse-x64/latest.json) and [versioned 6.0.36 feed](https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/windows/mouse-x64/releases/6.0.36.json) were verified to contain the same public installer URL, size and digest.

The first publication attempt, [run 44917016603](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/44917016603), stopped in metadata preflight because Python decoded UTF-8 release notes as Windows cp1252. [The UTF-8 correction](https://github.com/jeep-jim/OSMINOG-Releases/commit/baeff8ac7dcde75e7af8d6e4b0795e1b91c78c6b) added explicit decoding, Windows Python UTF-8 mode and two regressions; all 21 release contracts passed. The successful publication reused the same source and installer pins.

The candidate was initially staged with publication disabled. [PR65](https://github.com/jeep-jim/OSMINOG-Releases/pull/65) enabled the three platform pins only after their native source checks passed for the same merged source. This receipt describes hosted native CI verification; it does not claim testing on the owner's physical device or against external model accounts. The Windows installer is unsigned.
