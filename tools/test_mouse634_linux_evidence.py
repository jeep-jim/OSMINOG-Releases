#!/usr/bin/env python3
"""Retained Linux parser fixtures; native/sandbox tests remain unchanged."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_tests=_reuse['load']('test_mouse633_linux_evidence.py',namespace=globals())
globals().update({key:value for key,value in _tests.items() if not key.startswith('__')})
# Isolate the retained native-install gate. Both real upgrade formats and owner634
# are exercised independently by the complete current634 contract test modules.
E['verify']=E['verify_preserved']
_old_linux_fixture=fixture

def fixture():
 p,report,native,files,refresh=_old_linux_fixture();report.update(firstLinuxRelease=False,previousVersion='6.0.33');refresh();return p,report,native,files,refresh


def current_baseline(self):
 result=self.invoke();self.assertEqual(result['sandboxRendererCount'],4);self.assertEqual(len(result['nativeCaptures']),6);self.assertEqual(result['previousVersion'],'6.0.33');self.assertFalse(result['firstLinuxRelease'])


def bad_baseline(self):
 for key,value in [('platform','win32'),('version','6.0.32'),('previousVersion',None),('firstLinuxRelease',True),('ownerDeviceVerified',True)]:
  old=self.report[key];self.report[key]=value;self.refresh()
  with self.subTest(key=key),self.assertRaises(ValueError):self.invoke()
  self.report[key]=old

LinuxInstalledEvidence.test_complete_synthetic_native_contract_and_appimage_launcher_pid_difference=current_baseline
LinuxInstalledEvidence.test_wrong_os_version_or_invented_previous_release_fails=bad_baseline
if __name__=='__main__':unittest.main()
