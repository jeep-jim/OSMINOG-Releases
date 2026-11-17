#!/usr/bin/env python3
"""Publish exact tested621 bytes. Expand reviewed620 transforms without release side effects."""
import builtins,hashlib,pathlib,sys
base=pathlib.Path(__file__).with_name('mouse620-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='efedd433b547ed26205b3fcbf8286fea22903332','Reviewed620 publisher changed'
code=source.decode('utf-8')
# Each inherited wrapper validates its own input blob. Intercept only its final
# compile/exec, so validation never reads a pin, token, API or package.
for _ in range(8):
 if '\ndef import_candidate():' in code:break
 output=[]
 scope={'__file__':str(base),'__name__':'reviewed_source_transform','compile':lambda text,*a,**k:text,'exec':lambda text,*a,**k:output.append(text)}
 builtins.exec(builtins.compile(code,str(base),'exec'),scope)
 assert len(output)==1,'Ambiguous inherited source transform'
 code=output[0]
else:raise AssertionError('Unresolved publisher')
code=code.replace('6.0.20','6.0.21').replace('mouse620-release','mouse621-release').replace('MOUSE620_','MOUSE621_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=155','PR=156')
once("required={'history-meaningful-visits-not-actions'","required={'five-desktops-live-pages-preserved','smooth-native-desktop-slide','expiring-central-feedback-no-footer-text','native-image-file-drag-between-pages','global-page-zoom-existing-future','annotation-select-mouse-keyboard-green-palette','section-labels-after-count','history-meaningful-visits-not-actions'")
for old,new in [
 ('burrow-down1-height-minus3-width-preserved','top-plus-bottom-centered-burrow'),
 ('grounded-gradient-burrow-hover-only-plus','grounded-gradient-desktop-burrow'),
 ('arched-burrow-plus-no-glow','ordinary-top-plus-no-glow'),
 ('mouse-burrow-new-tab-button','mouse-burrow-desktop-button'),
 ('head-glasses-theme-identical','restored-619-private-artwork-and-glasses'),
 ('real-619-to-620-profile-preserving-install','real-620-to-621-profile-preserving-install'),
 ('MOUSE_620_REAL_619_TO_620_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_621_REAL_620_TO_621_REPLACE_RELAUNCH_PROFILE_PASS'),
 ('MOUSE_618_BURROW_DOWN1_SHORTER3_BOTH_THEMES_PASS','MOUSE_621_TOP_PLUS_BOTTOM_BURROW_BOTH_THEMES_PASS'),
 ('d4c14032a221f98f8026f1bea36cf8afc55c7511','aa58a5c412403790b49aa88eb7374c20a27510b6'),
 ('legacy619-update.cjs','legacy620-update.cjs'),
 ('# Actual released6.0.19 updater from its immutable tested source.','# Actual released6.0.20 updater from its immutable tested source.'),
 ('Mouse Browser 6.0.21 — мордочка, локальный архив и аккуратная история','Mouse Browser 6.0.21 — рабочие столы и удобное перетаскивание')]:once(old,new)
once("for m in ['MOUSE_620_REAL_HISTORY_NO_ACTION_FLOOD_PASS'","for m in ['MOUSE_621_DESKTOPS_TOASTS_ZOOM_EDITOR_PASS','MOUSE_621_NATIVE_CROSS_PAGE_PNG_DRAG_PASS','MOUSE_621_SMOOTH_DESKTOP_NATIVE_SLIDE_PASS','MOUSE_620_REAL_HISTORY_NO_ACTION_FLOOD_PASS'")
once("for n in ['mouse-620-history.png'","for n in ['mouse-621-desktops-light.png','mouse-621-desktops-dark.png','mouse-621-toast-light.png','mouse-621-toast-dark.png','mouse-621-zoom-light.png','mouse-621-zoom-dark.png','mouse-621-annotation-select.png','mouse-620-history.png'")
# Owner replaced the old hover-only top burrow with a permanent plus and moved
# the exact burrow to the footer. New both-theme geometry/click checks replace
# screenshots of the superseded top placement, not retained behavior checks.
once("'mouse-618-burrow-light.png','mouse-618-burrow-dark.png'","'mouse-621-bottom-burrow-light.png','mouse-621-bottom-burrow-dark.png'")
once("'mouse-615-burrow-light.png','mouse-615-burrow-dark.png','mouse-615-burrow-hover-light.png','mouse-615-burrow-hover-dark.png',",'')
builtins.compile(code,__file__,'exec')
for required in ["V='6.0.21'","PR=156","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","Source is not an ancestor of main","Artifact checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy620-update.cjs","ref=aa58a5c412403790b49aa88eb7374c20a27510b6","MOUSE_621_NATIVE_CROSS_PAGE_PNG_DRAG_PASS","MOUSE_621_REAL_620_TO_621_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS","MOUSE_PROFILE_COOKIE_RESTART_PASS","capture-off-private-no-read","twelve-pixel-pane-corners-clean-compositor","mouse-621-bottom-burrow-dark.png"]:
 assert required in code,required
if sys.argv[1:]==['validate']:
 print('MOUSE621_REVIEWED_PUBLISHER_GATES_PASS')
else:
 builtins.exec(builtins.compile(code,__file__,'exec'),globals())
