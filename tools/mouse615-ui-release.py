#!/usr/bin/env python3
"""6.0.15 exact verified packages; no rebuild, no legacy asset overwrite."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse609-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='d471823a6eaffad9d34a196604ab64d11cd2d490','Base publisher changed; review required'
code=source.decode('utf-8').replace('6.0.9','6.0.15').replace('mouse609-release','mouse615-release').replace('MOUSE609_','MOUSE615_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=141','PR=149')
once("(417128557,HEAD,'completed','success')","(419668574,HEAD,'completed','success')")
once("a['name']=='quadro-arm64-candidate'","a['name']=='mouse-arm64-candidate'")
code=code.replace('quadro-build.json','mouse-build.json').replace('quadro-smoke-write.log','mouse-smoke-write.log').replace('QUADRO_ARM64_SMOKE_PASS','MOUSE_ARM64_SMOKE_PASS')
once("('tools/quadro-verify.py','quadro-verify.py')","('tools/mouse-verify.py','mouse-verify.py')")
once("('desktop/quadro-update.cjs','quadro-update.cjs')","('desktop/mouse-update.cjs','mouse-update.cjs')")
once("required={'capture-legacy-recovery-picker-single-frame'","required={'arched-burrow-button-hover-mouse-no-glow','separated-footer-library-original-controls','real-update-badge-normal-mode-metadata-only','mouse-burrow-new-tab-button','ai-fullscreen-restore-normal-private-no-reload','tabs-fit-swap-expand-address-ai-height-selection','ai-bundled-official-picker','ai-history-buttons','cyan-ai-active-both-themes','adjacent-new-tab','glasses-left-one-source-pixel','destroyed-view-lifetime','bounded-shell-recovery','private-theme-light-dark-live','capture-legacy-recovery-picker-single-frame'")
once("smoke=(OUT/'mouse-smoke-write.log').read_text()","smoke=(OUT/'mouse-smoke-write.log').read_text()\n private=(OUT/'mouse-mouse-private-smoke.log').read_text()\n for marker in ['MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS','MOUSE_614_AI_FULLSCREEN_RESTORE_PRIVATE_PASS']:\n  if marker not in private:raise ValueError('Actual private verification missing: '+marker)")
once("for m in ['MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'","for m in ['MOUSE_615_ARCH_BUTTON_HOVER_AND_SEPARATE_FOOTER_BOTH_THEMES_PASS','MOUSE_614_REAL_UPDATE_BADGE_BOTH_THEMES_AND_BURROW_CLICK_PASS','MOUSE_614_AI_FULLSCREEN_RESTORE_NORMAL_PASS','MOUSE_613_TABS_REGROW_AFTER_CLOSE_PASS','MOUSE_613_TABS_SWAP_ADDRESS_AI_CHROME_PASS','MOUSE_612_AI_LOGOS_NAV_ACTIVE_AND_ADJACENT_PLUS_PASS','MOUSE_612_DESTROYED_GUESTS_DISPOSE_AND_SHELL_RECOVERY_PASS','MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS'")
once('MOUSE_609_REAL_608_TO_609_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_615_REAL_614_TO_615_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-609-real-menu-tab-click.png'","for n in ['mouse-615-burrow-light.png','mouse-615-burrow-dark.png','mouse-615-burrow-hover-light.png','mouse-615-burrow-hover-dark.png','mouse-614-burrow-update-light.png','mouse-614-burrow-update-dark.png','mouse-614-ai-fullscreen-normal-light.png','mouse-614-ai-fullscreen-normal-dark.png','mouse-614-ai-fullscreen-private-light.png','mouse-614-ai-fullscreen-private-dark.png','mouse-613-ai-choice-light.png','mouse-613-ai-choice-dark.png','mouse-613-address-light.png','mouse-613-address-dark.png','mouse-612-ai-light.png','mouse-612-ai-dark.png','mouse-611-private-light.png','mouse-611-private-dark.png','mouse-609-real-menu-tab-click.png'")
once('d76c837311c1691fcc4e0e3af311b9905fc7e37e','a1ced2b21e9fae9be7f3c6eb80c02cffbc827b80')
once("old=api(SOURCE,'contents/desktop/quadro-update.cjs?ref=","old=api(SOURCE,'contents/desktop/mouse-update.cjs?ref=")
once('legacy608-update.cjs','legacy614-update.cjs')
once('# Actual shipped 6.0.8 update module, not the new implementation pretending to be old.','# Actual released 6.0.14 module from its immutable source.')
once('Mouse Browser 6.0.15 — захват экрана и удобство окон','Mouse Browser 6.0.15 — живая норка и нижние кнопки')
exec(compile(code,__file__,'exec'),globals())
