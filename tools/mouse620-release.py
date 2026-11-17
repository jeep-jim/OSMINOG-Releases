#!/usr/bin/env python3
"""Publish exact native-tested620; inherit immutable619/616/609 release guards."""
import hashlib,pathlib
source=pathlib.Path(__file__).with_name('mouse619-emoji-release.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='22b487709c9e8694ece285dfbf356fab57467f70','Reviewed619 publisher changed'
code=source.decode('utf-8').replace('6.0.19','6.0.20').replace('mouse619-release','mouse620-release').replace('MOUSE619_','MOUSE620_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once("once('PR=141','PR=154')","once('PR=141','PR=155')")
once("required={'library-favicons-file-icons-list-grid-safe-selection'","required={'history-meaningful-visits-not-actions','update-minimized-live-progress','head-everywhere-native-icons','download-image-previews','local-opt-in-clipboard-and-screenshot-copies','capture-off-private-no-read','aligned-checkboxes-ai-square-controls','library-favicons-file-icons-list-grid-safe-selection'")
once('ten-pixel-native-and-shell-corners','twelve-pixel-pane-corners-clean-compositor')
once('real-618-to-619-profile-preserving-install','real-619-to-620-profile-preserving-install')
once("for m in ['MOUSE_619_LIBRARY_ICONS_VIEWS_TOPBAR_SELECTION_SAFE_CLEAR_PASS'","for m in ['MOUSE_620_REAL_HISTORY_NO_ACTION_FLOOD_PASS','MOUSE_620_UPDATE_HEAD_PREVIEW_ARCHIVE_CONTROLS_PASS','MOUSE_620_INSTALLED_ICNS_DOCK_UI_HEAD_PASS','MOUSE_619_LIBRARY_ICONS_VIEWS_TOPBAR_SELECTION_SAFE_CLEAR_PASS'")
once('MOUSE_619_REAL_618_TO_619_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_620_REAL_619_TO_620_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-619-tab-flow-light.png'","for n in ['mouse-620-history.png','mouse-620-download-previews-light.png','mouse-620-download-previews-dark.png','mouse-620-local-archive-light.png','mouse-620-local-archive-dark.png','mouse-620-text-preview-light.png','mouse-620-text-preview-dark.png','mouse-619-tab-flow-light.png'")
once('ec8054399238fc38bf7df02b5b4996250d1fd2f5','d4c14032a221f98f8026f1bea36cf8afc55c7511')
once('legacy618-update.cjs','legacy619-update.cjs')
once('# Actual released6.0.18 updater from its immutable tested source.','# Actual released6.0.19 updater from its immutable tested source.')
once('Mouse Browser 6.0.20 — эмодзи, вкладки и удобная библиотека','Mouse Browser 6.0.20 — мордочка, локальный архив и аккуратная история')
once("exec(compile(code,__file__,'exec'),globals())","once('glasses-left-one-source-pixel','head-glasses-theme-identical')\nexec(compile(code,__file__,'exec'),globals())")
exec(compile(code,__file__,'exec'),globals())
