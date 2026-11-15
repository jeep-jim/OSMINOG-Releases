#!/usr/bin/env python3
"""Narrow 6.0.10 adaptation of the exact audited-in-session 6.0.9 release script.
Keep all source, native, installer, immutable-byte and static-channel checks.
"""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse609-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='d471823a6eaffad9d34a196604ab64d11cd2d490','Base release script changed; re-review required'
code=source.decode('utf-8')
code=code.replace('6.0.9','6.0.10').replace('mouse609-release','mouse610-release').replace('MOUSE609_','MOUSE610_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=141','PR=142')
once("required={'capture-legacy-recovery-picker-single-frame'","required={'purple-incognito-glasses','toolbar-glasses-pixels-both-themes','capture-legacy-recovery-picker-single-frame'")
once("for m in ['MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'","for m in ['MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'")
once('MOUSE_609_REAL_608_TO_609_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_610_REAL_609_TO_610_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-609-real-menu-tab-click.png'","for n in ['mouse-610-footer-light.png','mouse-610-footer-dark.png','mouse-607-incognito-artwork.png','mouse-609-real-menu-tab-click.png'")
once('d76c837311c1691fcc4e0e3af311b9905fc7e37e','ccb83f3ed5fb9b4c62d818c1582eeaf08f477ecd')
once('legacy608-update.cjs','legacy609-update.cjs')
once('# Actual shipped 6.0.8 update module, not the new implementation pretending to be old.','# Actual shipped 6.0.9 update module, not the new implementation pretending to be old.')
once('Mouse Browser 6.0.10 — захват экрана и удобство окон','Mouse Browser 6.0.10 — фиолетовые очки')
exec(compile(code,__file__,'exec'),globals())
