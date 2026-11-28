#!/usr/bin/env python3
"""Retain the immutable acceptance lineage for current Mac 6.0.45."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse645-reuse.py")))["execute"]('mouse637-current.py', globals())

# All helper bytes are fetched from the accepted source commit and Git-blob checked.
HELPERS += ('mouse-638-feedback-run.py', 'mouse-638-acceptance.py', 'mouse-638-crx-proof.cjs')

# New639 runner and reader are fetched only from the accepted source Git tree.
HELPERS += ('mouse-639-adblock-run.py', 'mouse-639-acceptance.py')

#640 Settings is independently read from the combined native feature captures.
HELPERS += ('mouse-640-settings-acceptance.py',)

#641 separately binds actual user flows, two installed processes and raw pixels.
HELPERS += ('mouse-641-workspace-run.py', 'mouse-641-workspace-acceptance.py')

#642 binds real keyboard layouts, consent-based correction and saved tones.
HELPERS += ('mouse-642-controls-run.py', 'mouse-642-controls-acceptance.py')

#643 is Mac-only and adds raw native chrome/search/address/page-theme proof.
HELPERS += ('mouse-643-polish-run.py', 'mouse-643-polish-acceptance.py')

#644 binds native website themes, filter subscriptions and installed display names.
HELPERS += ('mouse-644-sync-run.py', 'mouse-644-sync-acceptance.py', 'mouse-644-branding.swift')
