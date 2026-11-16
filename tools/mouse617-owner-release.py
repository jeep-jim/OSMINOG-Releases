#!/usr/bin/env python3
"""Publish verified Mouse 6.0.17 through the unchanged checksum-gated pipeline."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse616-controls-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='aa9c254a99291eec5dad35349b39cb20c6300cb2','Reviewed 616 publisher changed'
code=source.decode('utf-8').replace('6.0.16','6.0.17').replace('mouse616-release','mouse617-release').replace('MOUSE616_','MOUSE617_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once("once('PR=141','PR=150')","once('PR=141','PR=151')")
once("required={'arched-burrow-plus-no-glow'","required={'owner-exact-128-pixel-small-head','address-focus-native-buttons-first-click','ten-pixel-native-and-shell-corners','fractional-viewport-endpoints-no-rim','footer-preserved-ai-status-only-hidden','grounded-gradient-burrow-hover-only-plus','real-616-to-617-profile-preserving-install','arched-burrow-plus-no-glow'")
once("for m in ['MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'","for m in ['MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS','MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'")
once('MOUSE_616_REAL_615_TO_616_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_617_REAL_616_TO_617_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-616-controls-light.png'","for n in ['mouse-617-chrome-light.png','mouse-617-chrome-dark.png','mouse-616-controls-light.png'")
once('a0ae116da02ea6d45720acb01121a9a3736e5d3e','de787c71fdfd64f7b9a5a45f7c55b7c4a2bbae2b')
once('legacy615-update.cjs','legacy616-update.cjs')
once('# Actual released 6.0.15 updater from its immutable tested source.','# Actual released 6.0.16 updater from its immutable tested source.')
once('Mouse Browser 6.0.17 — удобные кнопки и аккуратные окна','Mouse Browser 6.0.17 — точные углы, рабочие кнопки и новая морда')
# The reviewed base still requires successful exact native run, merged PR head,
# main ancestry, artifact SHA-256, package hashes, actual installed DMG checks,
# private-mode checks, immutable assets and channel advancement only afterwards.
exec(compile(code,__file__,'exec'),globals())
