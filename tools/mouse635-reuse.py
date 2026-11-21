#!/usr/bin/env python3
"""Byte-frozen634 algorithms with explicit635 runtime/module identities.

Native634 report names and thresholds remain intact. Only the reviewed new
search surface, real634 predecessor and separate owner635 gate differ.
"""
import ast
import hashlib
from pathlib import Path
import runpy

FROZEN = {'mouse634-capture-evidence.py': 'c46d3bd3244b6484c143042004b2c85bdb8e39b37f9e872e5eae9a13399c209a', 'mouse634-context-evidence.py': '724d56b11690e4a7897626fa0f1edf88bc09d6d507b9882d8e792b628c039288', 'mouse634-current.py': 'ca9d6c61e93a91f590dda5ee58532b6041227509aec7e92bd3bc37522a677cd8', 'mouse634-download-evidence.py': '4e654a795e07847bef5adb4f66e43394f54d4f43624e0aa437de427e6abe5fe7', 'mouse634-evidence.py': '70dd37092448bc91ed0142b180af01781ef73fbbe64b274724015e9dbc69092d', 'mouse634-feedback-evidence.py': '44da6cd898b32ef61729423f4ef6c1d03c28c506ca9622e0038d5614519442cc', 'mouse634-focused-evidence.py': 'd214c9f7fe4de4c48e4760b4c64337159f798a779b81364bdc1799f7f5049384', 'mouse634-linux-evidence.py': 'cf4751e7edcc5bbe2ce42d1a04d0c9d1c883217200ce04e140cb75829d137f07', 'mouse634-linux-release.py': '3de279999854e6685400e729cacc94d35ae4898fb322b76f4c50f331642aca15', 'mouse634-native-evidence.py': '5219ae1ebc3428163f4492f9f99a6288a68f942fda62e6ca939adc3435c45e00', 'mouse634-owner-feedback-evidence.py': '30feb04b6aa7d5a0cbf8ca6bb1d7189c9a4183ce540bb19ec3b69b356764aa9d', 'mouse634-release.py': '10a2dc57bb9ea42fc9ed213e1d3bf77110d51bf467733e9f272c24234ee4f64f', 'mouse634-retained-owner-evidence.py': '1998ae2996cc3f9c52c6fbc4769e8b3f831f3967e92b45114f6854faed2edada', 'mouse634-reuse.py': 'f41170e120647525663288d618335e29e92ee37ee922f19f9c7b5486a5da77c9', 'mouse634-search-evidence.py': 'f828c2ed5d299d440b116a6ac118ca3df02eaeedcba370a90a66be6d92d009f0', 'mouse634-task-evidence.py': 'e7644ef99c80b409222d824ded491777e03162516c13d926c54bacb9862f658f', 'mouse634-ui-evidence.py': '095c072e3997008b42ebc531d1055993d5333af51f3bef5a5f2e8f520a8135ce', 'mouse634-upgrade-evidence.py': '04f9df24e2824159342d475138ae15b56c97cc5a00356e5ce229ab86e5195cf7', 'mouse634-windows-release.py': 'ac0567d946b31c8cfa3a55d3607b8ad827994c1c64f5b6f0a9c8e3563f2e3ada', 'mouse634-workspace-evidence.py': '9bda2e1e1253da9edf512475db7d3cb78a80baa8712150fcffe5148b46f20b1d', 'test-mouse634-evidence.py': '3270f23f11e406e1ecf39926b6769907a0f5023044e40e15fe8efb654ec7e42d', 'test-mouse634-ui-evidence.py': '920ecd9ab13af70d01bddeb1acf71b2e99b6c268d2aace9c55c306396f282f83', 'test_mouse634_context_evidence.py': 'e6488e8ac38bb89a9799d545b8144d07d0e83d057ba593130b83a8ab0ac9c147', 'test_mouse634_feedback_evidence.py': 'aecc771da687e01fc8ea54191f12ce49461f42f3bdf7f994297ea14a414f82af', 'test_mouse634_linux_evidence.py': '1eb45056cdd7ae01301c12e3f3e80b70da86698ed31252f3bbbde5dc4c80f4ea', 'test_mouse634_linux_release.py': '48e26e3b5c1ab9770c94b9c17bec7e84c7dc9810ff19ba96ea14342fbe7f530c', 'test_mouse634_native_report.py': '47fa3ff1282030db897b889dff21f9ed899cbd2237d0ad95027d5a51c05c6cd2', 'test_mouse634_owner_feedback_evidence.py': 'cca9d90f9654f720ec19d3445cce7905017e9aa6b07f981dd75257c01930181d', 'test_mouse634_release_bytes.py': '8d40bdc014c04fe23d909086f2be9dccb97e6c9db2e45ab2f1e6354cd709f2a2', 'test_mouse634_retained_owner_evidence.py': 'b8c8747dbd617ae45581d08343e46f11997818652b076a6098580727d81a5414', 'test_mouse634_reuse.py': 'fde6d57b27e85bc6b6d56542a50747fe669170119af49872019490f74f5496aa', 'test_mouse634_search_evidence.py': '1b36924dc7e975e127e44fda17c8fe6a5d7868d4bafbb8c29eae1cd5e141c699', 'test_mouse634_task_evidence.py': '112c40bfe4d808e82b154f1c4adb05432aac25cc3ab6c4a9351b4c8b0127867d', 'test_mouse634_upgrade_evidence.py': '314261986804f31269fb72f41bef2073bdc9ab91a396bbb2584d6aa3c99c1d31', 'test_mouse634_windows_release.py': '702af0d3492a7347bc2f5a3b99e46f5447851014e082031be5557aec5e32cc5f', 'test_mouse634_workspace_evidence.py': 'c1315b8401c002f6bee52e6f7ff606c417eaba02b01c2865dc7ddf710a212bff'}
BASELINES = {'darwin': {'name': 'Mouse-Browser-6.0.34-mac-arm64.dmg', 'tag': 'quadro-macos-v6.0.34-arm64', 'size': 139344967, 'sha256': 'fd7bd882aaf948e623b8cb6affec0f9890be959add178cb88250b0a24f45dfab'}, 'win32': {'name': 'Mouse-Browser-6.0.34-Windows-x64.exe', 'tag': 'mouse-windows-v6.0.34-x64', 'size': 126570020, 'sha256': 'ab0762924e28151b66728cf79a024c5fa7956e11b724d7fbe015491d15fb11a0'}, 'linux': {'appimage': {'name': 'Mouse-Browser-6.0.34-Linux-x64.AppImage', 'tag': 'mouse-linux-v6.0.34-x64', 'size': 137051426, 'sha256': '6aebb0925d83a5fb505f20dceee969ded130070df96dd2f991eab347466e0f77'}, 'deb': {'name': 'Mouse-Browser-6.0.34-Linux-x64.deb', 'tag': 'mouse-linux-v6.0.34-x64', 'size': 106622916, 'sha256': 'f18f38d137f8d6a20e3a810abcfb38b34adbb68b55c040f0614fb58e3d0169ae'}}}
PREVIOUS_LINUX = {'version': '6.0.34', 'source': 'bc4cafb5c2db9cfc80165a7c470c813f0235cd04', 'updaterBlobSHA': '91ab363f926774825caf8055b2d3d81bf0d51264', 'packages': {'Mouse-Browser-6.0.34-Linux-x64.AppImage': {'size': 137051426, 'sha256': '6aebb0925d83a5fb505f20dceee969ded130070df96dd2f991eab347466e0f77'}, 'Mouse-Browser-6.0.34-Linux-x64.deb': {'size': 106622916, 'sha256': 'f18f38d137f8d6a20e3a810abcfb38b34adbb68b55c040f0614fb58e3d0169ae'}}}
MODULES = {name: name.replace('mouse634-', 'mouse635-').replace('test_mouse634_', 'test_mouse635_') for name in FROZEN}
MODULES.update({
 'mouse634-native-evidence.py':'mouse635-retained-native-evidence.py',
 'mouse634-owner-feedback-evidence.py':'mouse635-retained-owner-evidence.py',
 'mouse634-retained-owner-evidence.py':'mouse635-633-owner-evidence.py',
 'test_mouse634_owner_feedback_evidence.py':'test_mouse635_retained_owner_evidence.py',
 'test_mouse634_retained_owner_evidence.py':'test_mouse635_633_owner_evidence.py',
})


def checked(name):
 if name not in FROZEN: raise ValueError('Unreviewed635 dependency: '+name)
 raw=Path(__file__).with_name(name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=FROZEN[name]: raise ValueError('Immutable635 dependency changed: '+name)
 return raw


def legacy():
 checked('mouse634-reuse.py')
 return runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))


def target(name):
 if name in MODULES: return MODULES[name]
 old=legacy()
 previous=old['MODULES'].get(name)
 if previous is None and name.startswith(('mouse632-','test_mouse632_','test-mouse632-')):
  previous=name.replace('mouse632-','mouse634-').replace('test_mouse632_','test_mouse634_')
 if previous not in MODULES: raise ValueError('Unreviewed635 dependency: '+name)
 return MODULES[previous]


def adapted_tree(name, *, current_native=False):
 if current_native and name!='mouse634-native-evidence.py': raise ValueError('Current native identity is restricted to the frozen native primitive')
 tree=ast.parse(checked(name),filename=str(Path(__file__).with_name(name))) if name in FROZEN else legacy()['adapted_tree'](name)
 class Identity(ast.NodeTransformer):
  def visit_Constant(self,node):
   if not isinstance(node.value,str): return node
   value=node.value.replace('6.0.34','6.0.35').replace('MOUSE634_','MOUSE635_').replace('publish-mouse634','publish-mouse635')
   for old,new in MODULES.items(): value=value.replace(old,new)
   for old,new in [('mouse634-windows-release','mouse635-windows-release'),('mouse634-linux-release','mouse635-linux-release'),('mouse634-release','mouse635-release'),
       ('mouse-634-upgrade','mouse-635-upgrade'),('mouse-634-profile-upgrade','mouse-635-profile-upgrade'),('mouse-634-search','mouse-635-search'),
       ('MOUSE_634_REAL_633_TO_634_PROFILE_PASS','MOUSE_635_REAL_634_TO_635_PROFILE_PASS'),
       ('MOUSE_634_UPGRADE_PROFILE_','MOUSE_635_UPGRADE_PROFILE_'),
       ('MOUSE_634_REAL_629_TO_634_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_635_REAL_629_TO_635_REPLACE_RELAUNCH_PROFILE_PASS'),
       ('MOUSE_634_WINDOWS_REAL_629_TO_634_PROFILE_PASS','MOUSE_635_WINDOWS_REAL_629_TO_635_PROFILE_PASS'),
       ('real-633-to-634-profile-preserving-replacement','real-634-to-635-profile-preserving-replacement'),
       ('real-629-to-634-profile-preserving-install','real-629-to-635-profile-preserving-install')]: value=value.replace(old,new)
   if name in ('mouse634-upgrade-evidence.py','test_mouse634_upgrade_evidence.py','mouse634-current.py','mouse634-linux-release.py','mouse633-linux-evidence.py','test_mouse634_linux_evidence.py','test_mouse634_linux_release.py'):
    value=value.replace('6.0.33','6.0.34').replace('actual633','actual634').replace('published633','published634').replace('legacy633-update','legacy634-update').replace('Mouse634 preserved profile fixture','Mouse635 preserved profile fixture')
   if name=='mouse634-native-evidence.py' and node.value==r'mouse-634-[a-z0-9-]+\.png':
    value=r'mouse-635-[a-z0-9-]+\.png' if current_native else r'mouse-(?:634-|635-search-)[a-z0-9-]+\.png'
   if name in ('test_mouse633_native_report.py','test-mouse633-evidence.py') and value=='mouse634-': value='mouse635-'
   if name=='test_mouse632_windows_release.py' and value=='Immutable634 dependency changed: mouse633-ui-evidence.py':value='Immutable635 dependency changed: mouse634-ui-evidence.py'
   return ast.copy_location(ast.Constant(value=value),node) if value!=node.value else node
 tree=Identity().visit(tree)
 # The replacement algorithms are unchanged; only immutable predecessor data
 # advances to the independently downloaded public634 bytes.
 if name in ('mouse634-upgrade-evidence.py','mouse634-linux-release.py'):
  key,value=('BASELINES',BASELINES) if name=='mouse634-upgrade-evidence.py' else ('PREVIOUS',PREVIOUS_LINUX)
  assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets)]
  if len(assignments)!=1: raise ValueError('Predecessor identity assignment changed: '+name)
  assignments[0].value=ast.parse(repr(value),mode='eval').body
 return ast.fix_missing_locations(tree)


def load(name, *, namespace=None, current_native=False):
 scope=namespace if namespace is not None else {};original=scope.get('__name__')
 scope['__file__']=str(Path(__file__).with_name('mouse635-native-evidence.py' if current_native else target(name)));scope['__name__']='retained635_'+name.replace('-','_')
 try: exec(compile(adapted_tree(name,current_native=current_native),scope['__file__'],'exec'),scope)
 finally:
  if original is not None: scope['__name__']=original
 return scope
