#!/usr/bin/env python3
"""6.0.12: retain exact-byte/source checks; require AI history and runtime recovery."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse609-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='d471823a6eaffad9d34a196604ab64d11cd2d490','Base publisher changed; review required'
code=source.decode('utf-8').replace('6.0.9','6.0.12').replace('mouse609-release','mouse612-release').replace('MOUSE609_','MOUSE612_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=141','PR=144')
once("required={'capture-legacy-recovery-picker-single-frame'","required={'runtime-destroyed-page-guards','shell-renderer-recovery','ai-sidebar-back-forward-native','glasses-exact-one-pixel-left','private-theme-light-dark-live','purple-incognito-glasses','toolbar-glasses-pixels-both-themes','capture-legacy-recovery-picker-single-frame'")
once("smoke=(OUT/'quadro-smoke-write.log').read_text()","smoke=(OUT/'quadro-smoke-write.log').read_text()\n if 'MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS' not in (OUT/'quadro-mouse-private-smoke.log').read_text():raise ValueError('Actual private-theme verification missing')\n if 'MOUSE_612_REAL_SHELL_CRASH_PRIVATE_RECOVERY_AND_PAGE_CLOSE_STRESS_PASS' not in (OUT/'quadro-runtime-612.log').read_text():raise ValueError('Actual renderer-crash recovery verification missing')")
once("for m in ['MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'","for m in ['MOUSE_612_AI_NATIVE_BACK_FORWARD_REDIRECT_SPA_PROVIDER_ISOLATION_PASS','MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'")
once('MOUSE_609_REAL_608_TO_609_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_612_REAL_611_TO_612_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-609-real-menu-tab-click.png'","for n in ['mouse-612-ai-navigation-light.png','mouse-612-ai-navigation-dark.png','mouse-612-runtime-recovered.png','mouse-611-private-light.png','mouse-611-private-dark.png','mouse-609-real-menu-tab-click.png'")
once('d76c837311c1691fcc4e0e3af311b9905fc7e37e','a1d99edec218e9e3e0868b1c4dd84bf887d58e7d')
once('legacy608-update.cjs','legacy611-update.cjs')
once('# Actual shipped 6.0.8 update module, not the new implementation pretending to be old.','# Actual shipped 6.0.11 update module, not a new module impersonating it.')
once('Mouse Browser 6.0.12 — захват экрана и удобство окон','Mouse Browser 6.0.12 — навигация ИИ и устойчивость')
exec(compile(code,__file__,'exec'),globals())
