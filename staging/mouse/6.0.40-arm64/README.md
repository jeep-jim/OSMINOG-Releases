# Mouse Browser 6.0.40 — macOS arm64

This ready candidate is pinned to accepted source PR 216:
https://github.com/jeep-jim/OSMINOG/pull/216

- Tested source: `7428ecf52698e62468bb7befb9d7d2d06ee7b6d9`.
- Accepted merge: `7e0de1d371f206c26879d502ab2e4b470731da53`.
- Identical tested and merged tree: `0c98e782ae21f4818ec6ab83d037e54ca7f3e444`.
- Mac source run: https://github.com/jeep-jim/OSMINOG/actions/runs/45730096243
- Successful native job: `139609673154`, attempt 1.
- Candidate artifact: `15076654018`; verification artifact: `15076484752`.

The ZIP archives and both package sizes/SHA-256 values were independently
recomputed. The full publisher readers passed against the actual source
reports, native input receipts and decoded OS captures, including the new
Settings navigation/search/glass proof and retained AdBlock, browser, profile,
update, task/stress and motion checks. Other source platforms, including
Linux Noble and Modern Windows, also completed their native gates.

Publication imports these exact packages without rebuilding them and must pass
fresh installed Mac verification before uploading public assets or advancing
the channel. The real 6.0.39 predecessor is public; legacy 6.0.29 profile/updater
gates remain required. This is an ad-hoc signed preview, not notarized.

Publication order is macOS → Linux → Windows. Only this Mac candidate is
activated here. The next platform requires verified public Mac package bytes
and the canonical update feed.
