#!/usr/bin/env python3
"""Publish exact native-tested Mouse 6.0.17 bytes using the unchanged 6.0.16 release gates."""
import hashlib,pathlib,sys
base=pathlib.Path(__file__).with_name('mouse616-controls-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='aa9c254a99291eec5dad35349b39cb20c6300cb2','Previous publisher changed; review required'
end="exec(compile(code,__file__,'exec'),globals())\n"
text=source.decode('utf-8')
assert text.endswith(end),'Publisher loader changed'
# Run only the reviewed source transformation, NOT its release actions.
namespace={'__file__':str(base),'__name__':'mouse617_source_transform'}
exec(compile(text[:-len(end)],str(base),'exec'),namespace)
code=namespace['code'].replace('6.0.16','6.0.17').replace('mouse616-release','mouse617-release').replace('MOUSE616_','MOUSE617_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=150','PR=151')
once("required={'arched-burrow-plus-no-glow'","required={'owner-exact-128-pixel-small-head','address-focus-native-buttons-first-click','ten-pixel-native-and-shell-corners','fractional-viewport-endpoints-no-rim','footer-preserved-ai-status-only-hidden','grounded-gradient-burrow-hover-only-plus','real-616-to-617-profile-preserving-install','arched-burrow-plus-no-glow'")
once("for m in ['MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'","for m in ['MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS','MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS'")
once('MOUSE_616_REAL_615_TO_616_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_617_REAL_616_TO_617_REPLACE_RELAUNCH_PROFILE_PASS')
once("for n in ['mouse-616-controls-light.png'","for n in ['mouse-617-chrome-light.png','mouse-617-chrome-dark.png','mouse-616-controls-light.png'")
once('a0ae116da02ea6d45720acb01121a9a3736e5d3e','de787c71fdfd64f7b9a5a45f7c55b7c4a2bbae2b')
once('legacy615-update.cjs','legacy616-update.cjs')
once('# Actual released 6.0.15 updater from its immutable tested source.','# Actual released 6.0.16 updater from its immutable tested source.')
once('Mouse Browser 6.0.17 — удобные кнопки и аккуратные окна','Mouse Browser 6.0.17 — точные скругления, рабочие кнопки и новая морда')
if sys.argv[1:]==['validate']:
 compile(code,__file__,'exec')
 for required in ["PR=151","V='6.0.17'","mouse-arm64-candidate","(419668574,HEAD,'completed','success')","legacy616-update.cjs","MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS","MOUSE_617_REAL_616_TO_617_REPLACE_RELAUNCH_PROFILE_PASS"]:
  assert required in code,required
 assert "pr.get('merged')" in code and 'Source is not an ancestor of main' in code
 assert 'Refusing to overwrite different existing bytes' in code and 'Refusing channel downgrade' in code
 print('MOUSE617_PUBLISHER_CONTRACT_PASS')
else:
 exec(compile(code,__file__,'exec'),globals())
