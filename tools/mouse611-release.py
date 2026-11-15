#!/usr/bin/env python3
"""6.0.11 adapter: retain exact provenance, installed DMG and immutable release checks."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse609-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='d471823a6eaffad9d34a196604ab64d11cd2d490','Base publisher changed; review required'
code=source.decode('utf-8')
code=code.replace('6.0.9','6.0.11').replace('mouse609-release','mouse611-release').replace('MOUSE609_','MOUSE611_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=141','PR=143')
once("required={'capture-legacy-recovery-picker-single-frame'","required={'private-theme-light-dark-live','purple-incognito-glasses','toolbar-glasses-pixels-both-themes','capture-legacy-recovery-picker-single-frame'")
once("smoke=(OUT/'quadro-smoke-write.log').read_text()","smoke=(OUT/'quadro-smoke-write.log').read_text()\n if 'MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS' not in (OUT/'quadro-mouse-private-smoke.log').read_text():raise ValueError('Actual private-theme verification missing')")
once("for m in ['MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'","for m in ['MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'")
once('MOUSE_609_REAL_608_TO_609_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_611_REAL_610_TO_611_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-609-real-menu-tab-click.png'","for n in ['mouse-611-private-light.png','mouse-611-private-dark.png','mouse-610-footer-light.png','mouse-610-footer-dark.png','mouse-609-real-menu-tab-click.png'")
once('d76c837311c1691fcc4e0e3af311b9905fc7e37e','0e88c2df3a67c7eb9535b4faa3f72942f22fce50')
once('legacy608-update.cjs','legacy610-update.cjs')
once('# Actual shipped 6.0.8 update module, not the new implementation pretending to be old.','# Actual shipped 6.0.10 update module, not the new implementation pretending to be old.')
once('Mouse Browser 6.0.11 — захват экрана и удобство окон','Mouse Browser 6.0.11 — светлая тема инкогнито')
exec(compile(code,__file__,'exec'),globals())
