#!/usr/bin/env python3
"""Synthetic Linux634 pin and package policy; no native/publication claims."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_tests=_reuse['load']('test_mouse633_linux_release.py',namespace=globals())
globals().update({key:value for key,value in _tests.items() if not key.startswith('__')})
_old_pin_fixture=fixture

def fixture():
 result=_old_pin_fixture();result['previous']=copy.deepcopy(P['PREVIOUS']);return result


def actual_baseline(self):
 for prior in (None,{},'6.0.33',{'version':'6.0.33','platform':'win32'}):
  value=fixture();value['previous']=prior
  with self.subTest(prior=prior),self.assertRaisesRegex(ValueError,'actual published633'):self.invoke(value)
 value=fixture();name=next(iter(value['previous']['packages']));value['previous']['packages'][name]['sha256']='0'*64
 with self.assertRaisesRegex(ValueError,'actual published633'):self.invoke(value)

LinuxPins.test_linux_has_no_invented_prior_release=actual_baseline
if __name__=='__main__':unittest.main()
