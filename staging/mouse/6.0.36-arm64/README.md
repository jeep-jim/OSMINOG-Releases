# Mouse Browser 6.0.36 — arm64

Published on **2026-11-21 at 15:21:57 UTC** from the exact packages in [pin.json](pin.json). The public GitHub release is marked as a prerelease.

## Source and verification

| Evidence | Exact reference |
|---|---|
| Tested source | [`7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3`](https://github.com/jeep-jim/OSMINOG/commit/7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3) |
| Source merge | [PR190](https://github.com/jeep-jim/OSMINOG/pull/190), [`94d5c3d1b7fa7652a0f55b73ba3847458b3d053f`](https://github.com/jeep-jim/OSMINOG/commit/94d5c3d1b7fa7652a0f55b73ba3847458b3d053f) |
| Source native CI | [Run 44913896930](https://github.com/jeep-jim/OSMINOG/actions/runs/44913896930), attempt 1, job 136875265234 |
| Fresh installation and publication | [Run 44917016749](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/44917016749), attempt 1, job 136884799754; **success** |
| Public release | [quadro-macos-v6.0.36-arm64](https://github.com/jeep-jim/OSMINOG-Releases/releases/tag/quadro-macos-v6.0.36-arm64) |

The publisher repeated native installed checks, profile replacement, and independent task, interface and motion-trace verification. The current predecessor upgrade was 6.0.35 to 6.0.36. Separately, the actual released 6.0.29 updater discovered 6.0.36 and anonymously downloaded and verified the pinned DMG; the 6.0.36 updater reported the version as current.

## Public packages

| Package | Bytes | SHA-256 |
|---|---:|---|
| [DMG](https://github.com/jeep-jim/OSMINOG-Releases/releases/download/quadro-macos-v6.0.36-arm64/Mouse-Browser-6.0.36-mac-arm64.dmg) | 137981934 | `8688b4db4bd8d9541d93508ecdb3260727d9c6a975f336cfcd2b086caae704fb` |
| [ZIP](https://github.com/jeep-jim/OSMINOG-Releases/releases/download/quadro-macos-v6.0.36-arm64/Mouse-Browser-6.0.36-mac-arm64.zip) | 140347143 | `8a09929b313afeb9e41aa52f0c079a9044806a41d6b9c301ce66ea9a93034ab0` |

The [legacy Quadro DMG alias](https://github.com/jeep-jim/OSMINOG-Releases/releases/download/quadro-macos-v6.0.36-arm64/Quadro-Browser-6.0.36-mac-arm64.dmg) has the same bytes, size and SHA-256 as the Mouse DMG. The [current update feed](https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/channels/mouse/macos-arm64.json) was verified against the public Mouse DMG URL, size and digest.

The candidate was initially staged with publication disabled. [PR65](https://github.com/jeep-jim/OSMINOG-Releases/pull/65) enabled the three platform pins only after their native source checks passed for the same merged source. This receipt describes hosted native CI verification; it does not claim testing on the owner's physical device or against external model accounts. The application is ad-hoc signed and is not notarized.
