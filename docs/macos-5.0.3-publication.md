# macOS5.0.3 publication plan — 2026-11-13

The owner confirmed M1 Pro and requested full-width browser panes after closing the right AI panel. Source PR129 adds a Mac-only correction and native regression checks for1/2/4/6 panes at1440/1100/900, reopen and retained page state.

Previous run43398829975 verified DMG installation but stopped before publication because tag-based GET did not resolve a draft. New publisher uses numeric release ID, requires exact asset sizes and digests, and only then changes draft=false. It never replaces a published asset and preserves the old5.0.2 draft unpublished.

Publication is NOT established by this commit. Check source run43399939933, source merge and the new release run plus actual release assets before giving an installation URL. Windows, Chrome, Android channels remain unchanged.
