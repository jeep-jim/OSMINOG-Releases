# Mouse Browser 6.0.41 — Windows x64

## Activation prerequisites

Mac 6.0.41 is public and independently verified: [publisher45844915958](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45844915958), attempt 1, fresh job `139996836668`, activation merge `d1c2ceb2cef26deae1d0cefc02542b194f1ebe3f`. All fresh installed and actual629/640 update gates passed; independent archive replay passed 13 groups and all eight saved-report equality checks. The canonical Mac feed and five public asset identities match the accepted pin. The additional [Linux PR95 ordered-publication contract45851734433](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45851734433), job `140019557944`, fully downloaded and verified both public Mac DMG and ZIP before Linux activation.

Linux 6.0.41 has completed its [fresh publisher45852450598](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45852450598), attempt 1, job `140023079054`, on activation merge `42e71474a9f8c520e5569f4dd0aebf47003f9924`. Fresh installed/native verification passed from 2026-11-26T15:53:35Z to 16:06:17Z; the release was published at 16:10:07Z and its actual 6.0.40 anonymous updater step passed at 16:10:08Z–16:10:28Z. The five public release assets and separate canonical/versioned 6.0.41 feed readbacks match the accepted AppImage and deb. Before this Windows activation is merged, the independent complete Linux fresh-artifact audit must also pass. The existing Windows PR contract additionally requires complete anonymous downloads of both Mac packages and both Linux packages; publication jobs are skipped for pull requests.

This activation pins the exact accepted Windows installer for the ordered Mac → Linux → Windows release. Both preceding public platforms must be verified before the ordinary activation merge. The publisher must import these exact bytes and pass fresh installed verification before the Windows release. Windows remains an unsigned preview; the source manifest reports unsigned signing and Authenticode NotSigned.

## Accepted source

[Source PR218](https://github.com/jeep-jim/OSMINOG/pull/218) was ordinary-merged as `ceaef4d7d22d91a2b5ab4decd05f1c16e5ea9dd1`. The exact tested source is `3a32e02a8893b4c2f1397cd0a08e94af737f42fc`, and the source and merge tree is `bf4b60b717d14479f621709ba242ed0c0e569b70`. Later documentation-only commits do not change this accepted package identity.

[Windows source run 45830569936](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569936), attempt 1, completed successfully on the accepted source:

| Job | Result | Actual API interval (UTC) |
| --- | --- | --- |
| [Primary 139945934660](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569936/job/139945934660) | SUCCESS | 2026-11-26T13:35:13Z–2026-11-26T13:55:40Z |
| [Modern 139957514950](https://github.com/jeep-jim/OSMINOG/actions/runs/45830569936/job/139957514950) | SUCCESS | 2026-11-26T13:55:43Z–2026-11-26T14:15:21Z |

## Immutable source artifacts

The complete ZIP bytes were downloaded once and checked against their recorded size and SHA256. Artifact creation falls within the corresponding successful job and upload step.

| Artifact | ID | ZIP bytes | Created at (UTC) | Full ZIP SHA256 |
| --- | --- | --- | --- | --- |
| Candidate | 15124096197 | 113771118 | 2026-11-26T13:55:29Z | `5bf56e780a20d1bac7bab4be65e77eee86d4a11244128196ddad9a9f1ad01e94` |
| Primary verification | 15124435968 | 125315449 | 2026-11-26T13:55:35Z | `d0eba7974d6ae679440767f052a8abe73918cfd6715ae05976d8b04e37a16d52` |
| Modern verification | 15126871064 | 120605639 | 2026-11-26T14:15:16Z | `c0324068d1ee4ec4cfb22392b662422c6d6853ec1e90487a5b7ad9b8bf3d0285` |

Installer: `Mouse-Browser-6.0.41-Windows-x64.exe`, 113759784 bytes, SHA256 `1e6f4860869fe1060dde1f009fad4fd74b4f4f3adb2cf0f28122047d66e0c341`. The actual installed `Mouse Browser.exe` SHA256 is identical in primary and modern: `2e6810eda60337e12d64dfdd03e3d81a081a09488a1f08e6ab0a01bca7a42207`.

The modern immutable-input receipt binds this source, run/attempt, package and the primary inner verification JSON SHA256 `c67015e3c6ee233ac62e800b4191974d6ca6d71147fd7cc5f2c2310167972a81`. That inner JSON digest is distinct from the full verification ZIP digest pinned in `verificationSHA256`.

## Independent evidence

The complete offline replay used the actual production readers after the reviewed 641-only geometry correction in [Releases PR93](https://github.com/jeep-jim/OSMINOG-Releases/pull/93), merge `bd1b1e6fa4eaadaf6c678206679d3b82d65609dd`. The adapter SHA256 is `e502a8b4d9230bc303411fc975fb1b53034af9ce0e4288f290678fd29341bf89`; its fingerprint stayed unchanged during replay. Frozen 629/640 gates and source package bytes remain unchanged.

Primary replay passed all 25 recorded stages: retained verification/task/feedback/current-upgrade, exact source helper bytes, all four current evidence readers and fresh-form readback predicates on the existing source archive. Modern replay passed all nine mandatory stages, including immutable primary binding, retained feedback/current-upgrade and the same four current readers. The original failed modern geometry report remains preserved as history; the complete corrected replay supersedes that result.

Evidence report SHA256 values:

- Primary full replay: `17cfbc6e7293fcfabf7ad76f070c83b4bc671b5d3b2b01a9e8a52d82129f6ed6`.
- Modern complete replay: `69d5a246479dcf163f8600a6a6044428635afb4f3a0800dcb8bda9d463070efb`.
- Combined source offline acceptance: `2ff1cd353fbd92bfc70a79f6f4b35695a360aa3ffb42e5f56e0d96a6d078b2e3`.
- Raw API job/artifact provenance snapshot: `eb7a230be6749beadb174e0580743311a3436f2c7ee3e79b82d787e01e563b73`.

This is offline acceptance of actual installed source CI evidence. It did not perform a new publisher installation, release upload or public download verification.

## Required publisher and public acceptance

The ready pin retains both predecessor routes: legacy `previous` 6.0.29 and `currentPrevious` 6.0.40. It preserves the profile, App ID, Chromium partition, cookies, tabs, desktops and updater compatibility. The publisher must recheck exact source/merge/primary/modern provenance, import the immutable installer, run the required native and retained checks in a fresh installed Windows process, and recheck the installer bytes before publishing.

The target release tag is `mouse-windows-v6.0.41-x64`; canonical feed `platforms/windows/mouse-x64/latest.json`; versioned feed `platforms/windows/mouse-x64/releases/6.0.41.json`. Final acceptance requires a non-draft public release, matching feed URL/size/SHA256, complete anonymous installer download, and actual legacy/current updater discovery. The ready pin, successful source CI and offline replay alone are not publication receipts.
