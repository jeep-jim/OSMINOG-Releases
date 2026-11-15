#!/usr/bin/env python3
"""6.0.13 adapter: exact source/native-tested bytes and actual previous updater."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse609-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='d471823a6eaffad9d34a196604ab64d11cd2d490','Base publisher changed; review required'
code=source.decode('utf-8').replace('6.0.9','6.0.13').replace('mouse609-release','mouse613-release').replace('MOUSE609_','MOUSE613_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=141','PR=146')
once("required={'capture-legacy-recovery-picker-single-frame'","required={'all-tabs-one-row','swap-panes-tabs-no-reload','expanded-address','compact-ai-selected','full-display-editor-fit','footer-library-right','ai-bundled-official-picker','ai-history-buttons','cyan-ai-active-both-themes','adjacent-new-tab','glasses-left-one-source-pixel','destroyed-view-lifetime','bounded-shell-recovery','private-theme-light-dark-live','capture-legacy-recovery-picker-single-frame'")
once("smoke=(OUT/'quadro-smoke-write.log').read_text()","smoke=(OUT/'quadro-smoke-write.log').read_text()\n if 'MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS' not in (OUT/'quadro-mouse-private-smoke.log').read_text():raise ValueError('Actual private-theme verification missing')")
once("for m in ['MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'","for m in ['MOUSE_613_WORKSPACE_AND_FULL_SCREEN_PASS','MOUSE_612_AI_LOGOS_NAV_ACTIVE_AND_ADJACENT_PLUS_PASS','MOUSE_612_DESTROYED_GUESTS_DISPOSE_AND_SHELL_RECOVERY_PASS','MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'")
once('MOUSE_609_REAL_608_TO_609_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_613_REAL_612_TO_613_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-609-real-menu-tab-click.png'","for n in ['mouse-613-ui-light.png','mouse-613-ui-dark.png','mouse-613-full-display-editor.png','mouse-613-entire-screen-legacy.png','mouse-613-entire-screen-native.png','mouse-612-ai-light.png','mouse-612-ai-dark.png','mouse-611-private-light.png','mouse-611-private-dark.png','mouse-609-real-menu-tab-click.png'")
once('d76c837311c1691fcc4e0e3af311b9905fc7e37e','4f0bee5ac4c2740e03cbd6a253cf7f99fdae2bd0')
once('legacy608-update.cjs','legacy612-update.cjs')
once('# Actual shipped 6.0.8 update module, not the new implementation pretending to be old.','# Actual shipped 6.0.12 updater, not the new implementation pretending to be old.')
once('Mouse Browser 6.0.13 — захват экрана и удобство окон','Mouse Browser 6.0.13 — вкладки и полный снимок экрана')
exec(compile(code,__file__,'exec'),globals())
