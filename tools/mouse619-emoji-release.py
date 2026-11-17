#!/usr/bin/env python3
"""Publish native-tested Mouse6.0.19 emoji control without changing existing release gates."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse616-controls-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='aa9c254a99291eec5dad35349b39cb20c6300cb2','Reviewed616 publisher changed'
code=source.decode('utf-8').replace('6.0.16','6.0.19').replace('mouse616-release','mouse619-release').replace('MOUSE616_','MOUSE619_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once("once('PR=141','PR=150')","once('PR=141','PR=153')")
once("required={'arched-burrow-plus-no-glow'","required={'native-emoji-picker-macos-visible','emoji-owned-page-ai-shell-focus','emoji-private-workspace-routing','emoji-windows-api-contract','burrow-down1-height-minus3-width-preserved','owner-exact-128-pixel-small-head','address-focus-native-buttons-first-click','ten-pixel-native-and-shell-corners','fractional-viewport-endpoints-no-rim','footer-preserved-ai-status-only-hidden','grounded-gradient-burrow-hover-only-plus','real-618-to-619-profile-preserving-install','arched-burrow-plus-no-glow'")
once("for m in ['MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'","for m in ['MOUSE_619_EMOJI_FOOTER_PAGE_AI_SHELL_FOCUS_PASS','MOUSE_619_NATIVE_CHARACTER_VIEWER_VISIBLE_PASS','MOUSE_618_BURROW_DOWN1_SHORTER3_BOTH_THEMES_PASS','MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS','MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'")
once("for marker in ['MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS'","for marker in ['MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS','MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS'")
once('MOUSE_616_REAL_615_TO_616_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_619_REAL_618_TO_619_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-616-controls-light.png'","for n in ['mouse-619-native-picker.png','mouse-619-native-picker.json','mouse-619-emoji-normal-light.png','mouse-619-emoji-normal-dark.png','mouse-619-emoji-private-light.png','mouse-619-emoji-private-dark.png','mouse-618-burrow-light.png','mouse-618-burrow-dark.png','mouse-617-chrome-light.png','mouse-617-chrome-dark.png','mouse-616-controls-light.png'")
once('a0ae116da02ea6d45720acb01121a9a3736e5d3e','ec8054399238fc38bf7df02b5b4996250d1fd2f5')
once('legacy615-update.cjs','legacy618-update.cjs')
once('# Actual released 6.0.15 updater from its immutable tested source.','# Actual released6.0.18 updater from its immutable tested source.')
once('Mouse Browser 6.0.19 — удобные кнопки и аккуратные окна','Mouse Browser 6.0.19 — системная панель эмодзи')
exec(compile(code,__file__,'exec'),globals())
