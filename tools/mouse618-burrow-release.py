#!/usr/bin/env python3
"""Publish verified Mouse6.0.18 geometry-only hotfix with all existing release gates."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse616-controls-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='aa9c254a99291eec5dad35349b39cb20c6300cb2','Reviewed616 publisher changed'
code=source.decode('utf-8').replace('6.0.16','6.0.18').replace('mouse616-release','mouse618-release').replace('MOUSE616_','MOUSE618_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once("once('PR=141','PR=150')","once('PR=141','PR=152')")
once("required={'arched-burrow-plus-no-glow'","required={'burrow-down1-height-minus3-width-preserved','owner-exact-128-pixel-small-head','address-focus-native-buttons-first-click','ten-pixel-native-and-shell-corners','fractional-viewport-endpoints-no-rim','footer-preserved-ai-status-only-hidden','grounded-gradient-burrow-hover-only-plus','real-617-to-618-profile-preserving-install','arched-burrow-plus-no-glow'")
once("for m in ['MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'","for m in ['MOUSE_618_BURROW_DOWN1_SHORTER3_BOTH_THEMES_PASS','MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS','MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'")
once('MOUSE_616_REAL_615_TO_616_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_618_REAL_617_TO_618_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-616-controls-light.png'","for n in ['mouse-618-burrow-light.png','mouse-618-burrow-dark.png','mouse-617-chrome-light.png','mouse-617-chrome-dark.png','mouse-616-controls-light.png'")
once('a0ae116da02ea6d45720acb01121a9a3736e5d3e','6cee99f1a69454720ec9b23d7835d597d7b8bd6e')
once('legacy615-update.cjs','legacy617-update.cjs')
once('# Actual released 6.0.15 updater from its immutable tested source.','# Actual released6.0.17 updater from its immutable tested source.')
once('Mouse Browser 6.0.18 — удобные кнопки и аккуратные окна','Mouse Browser 6.0.18 — норка ниже и компактнее')
exec(compile(code,__file__,'exec'),globals())
