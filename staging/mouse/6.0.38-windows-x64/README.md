# Mouse Browser 6.0.38 — windows-x64

Pinned candidate from source `b9d243dd7507da3c5b5397c62391315c09794db8`,
merged by [source PR #203](https://github.com/jeep-jim/OSMINOG/pull/203)
as `4d3953456f09448c5b2c2bd463496f27fe6c8a9e`.
Both native Windows jobs and their independent readers passed
[source run 45185687846, attempt 1](https://github.com/jeep-jim/OSMINOG/actions/runs/45185687846).
The exact installer and both verification archives are recorded in `pin.json`;
previous 6.0.29 and currentPrevious 6.0.37 remain unchanged.

PUBLISH_OWNER selects the existing workflow, which verifies the installed
application, profile upgrades, public package bytes and anonymous updater
downloads before completing publication. Its results are recorded in
[publisher workflow runs](https://github.com/jeep-jim/OSMINOG-Releases/actions/workflows/publish-mouse638-windows.yml).
This is an unsigned x64 preview.
Publication order: macOS → Linux → Windows, with the previous public channel and packages verified.
The source PR must be merged and the exact successful native workflow source must be an ancestor of main.
