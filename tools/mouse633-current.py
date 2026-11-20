#!/usr/bin/env python3
"""Version633 source helpers and current632-to633 evidence composition."""
import base64
import hashlib
import json
from pathlib import Path
import runpy


def fetch_helpers(api, source_repo, source, output):
    for name in ('mouse-633-upgrade.py','mouse-633-profile-upgrade.cjs'):
        obj=api(source_repo, 'contents/tools/'+name+'?ref='+source)
        raw=base64.b64decode(obj['content'])
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=obj.get('sha'):
            raise ValueError('Mouse633 source helper Git blob differs: '+name)
        (output/name).write_bytes(raw)


def verify_upgrade(read, *, platform, arch, package):
    marker='MOUSE_633_REAL_632_TO_633_PROFILE_PASS'
    outer=read('mouse-633-upgrade.log')
    if not isinstance(outer,bytes) or not 0<len(outer)<=16*1024**2 or marker not in outer.decode('utf-8').splitlines():
        raise ValueError('Actual published632 replacement process marker missing')
    if platform=='win32':
        raw=read('mouse-windows-verification.json')
        if not isinstance(raw,bytes) or not 0<len(raw)<=4*1024**2:
            raise ValueError('Windows633 current process wrapper missing')
        report=json.loads(raw)
        for key,name,required,budget in (
            ('freshUpgrade','mouse-633-upgrade.json',marker,480000),
            ('ownerFeedback','mouse-633-owner-feedback.json','MOUSE_633_OWNER_FEEDBACK_PASS',270000)):
            stage=report.get('checks',{}).get(key,{})
            if (stage.get('exitCode')!=0 or type(stage.get('pid')) is not int or stage['pid']<=0 or
                    type(stage.get('elapsedMs')) not in (int,float) or not 0<stage['elapsedMs']<=budget or
                    stage.get('requiredMarkers')!=[required] or
                    stage.get('reportSha256')!=hashlib.sha256(read(name)).hexdigest()):
                raise ValueError('Windows633 current process/report byte binding failed: '+key)
    checker=runpy.run_path(str(Path(__file__).with_name('mouse633-upgrade-evidence.py')))
    return checker['verify'](read,expected_platform=platform,expected_arch=arch,expected_package=package)
