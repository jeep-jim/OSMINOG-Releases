#!/usr/bin/env python3
"""Expand reviewed text transforms only. No API, release, pin or package access."""
import builtins,pathlib
file=pathlib.Path(__file__).with_name('mouse620-release.py');code=file.read_text()
for _ in range(5):
 if 'def import_candidate():' in code:break
 output=[]
 ns={'__file__':str(file),'__name__':'publisher_contract','compile':lambda text,*args,**kwargs:text,'exec':lambda text,*args,**kwargs:output.append(text)}
 builtins.exec(builtins.compile(code,str(file),'exec'),ns)
 assert len(output)==1,'Ambiguous publisher transform'
 code=output[0]
else:raise AssertionError('Publisher did not resolve')
builtins.compile(code,str(file),'exec')
for required in ["V='6.0.20'","PR=155","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","Source is not an ancestor of main","Artifact checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy619-update.cjs","ref=d4c14032a221f98f8026f1bea36cf8afc55c7511","history-meaningful-visits-not-actions","head-glasses-theme-identical","twelve-pixel-pane-corners-clean-compositor","capture-off-private-no-read","MOUSE_620_REAL_HISTORY_NO_ACTION_FLOOD_PASS","MOUSE_620_UPDATE_HEAD_PREVIEW_ARCHIVE_CONTROLS_PASS","MOUSE_620_INSTALLED_ICNS_DOCK_UI_HEAD_PASS","MOUSE_620_REAL_619_TO_620_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS","MOUSE_PROFILE_COOKIE_RESTART_PASS","mouse-620-history.png","mouse-620-local-archive-dark.png"]:
 assert required in code,required
assert "'glasses-left-one-source-pixel'" not in code
assert "'ten-pixel-native-and-shell-corners'" not in code
print('MOUSE620_REVIEWED_PUBLISHER_GATES_PASS')
