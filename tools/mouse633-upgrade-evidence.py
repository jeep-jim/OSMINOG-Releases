#!/usr/bin/env python3
"""Verify actual published632 profile preservation separately from frozen629 gates."""
import hashlib
import json
import re

BASELINES = {
 'darwin': {'name':'Mouse-Browser-6.0.32-mac-arm64.dmg','tag':'quadro-macos-v6.0.32-arm64','size':137839606,
            'sha256':'c6a6d1d6ce6e5ed2fdd1fbd7735c4c3c37e4c80e77781c84cdf9608ca56d7ec2'},
 'win32': {'name':'Mouse-Browser-6.0.32-Windows-x64.exe','tag':'mouse-windows-v6.0.32-x64','size':125728399,
           'sha256':'824c5c1eb1bd3a31079d9f8c8109cb37a815f9c4b1d6fa498f79604f8dbde02e'}}
SOURCE = 'real installed executable and owned loopback CDP fixture'
METHOD = 'verified package replacement and actual old/new profile processes; retained629 gate tests updater'


def need(value, message):
 if not value: raise ValueError('Mouse633 actual632 upgrade: '+message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def read_json(read,name):
 raw=read(name)
 need(isinstance(raw,bytes) and 0<len(raw)<=1024**2,'missing or oversized '+name)
 value=json.loads(raw);need(isinstance(value,dict),'non-object '+name)
 return raw,value


def verify(read, *, expected_platform, expected_arch, expected_package):
 need((expected_platform,expected_arch) in (('darwin','arm64'),('win32','x64')),'unsupported target')
 raw,facts=read_json(read,'mouse-633-upgrade.json')
 baseline=BASELINES[expected_platform]
 expected_baseline={**baseline,'url':'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/'+baseline['tag']+'/'+baseline['name']}
 need(facts.get('ok') is True and not facts.get('error') and facts.get('fromVersion')=='6.0.32' and
      facts.get('toVersion')=='6.0.33' and facts.get('platform')==expected_platform and
      facts.get('baseline')==expected_baseline and facts.get('package')==expected_package,'wrong versions or immutable package bytes')
 need(facts.get('method')==METHOD and facts.get('physicalUserDeviceVerified') is False,
      'package replacement method or physical scope misrepresented')
 need(facts.get('closedProfileUnchanged') is True and facts.get('differentProcesses') is True and
      isinstance(facts.get('closedProfileSha256'),str) and re.fullmatch('[0-9a-f]{64}',facts['closedProfileSha256']),
      'closed profile preservation is not bound')
 reports=[];inputs={'mouse-633-upgrade.json':sha(raw)}
 for mode,version,key in [('write','6.0.32','oldWrite'),('read','6.0.33','newRead')]:
  name='mouse-633-upgrade-'+mode+'.json';data,report=read_json(read,name);bound=facts.get(key,{})
  need(bound.get('reportSha256')==sha(data) and bound.get('result')==report,'raw native profile report differs')
  inputs[name]=sha(data)
  need(report.get('ok') is True and not report.get('error') and
       (report.get('version'),report.get('platform'),report.get('arch'),report.get('mode'))==
       (version,expected_platform,expected_arch,mode) and type(report.get('pid')) is int and report['pid']>0,
       'native old/new runtime identity differs')
  need(report.get('source')==SOURCE and report.get('physicalUserInputVerified') is False and
       report.get('nativeExit')=={'code':0,'signal':None},'actual process lifecycle or input scope differs')
  identity=report.get('identity',{})
  need(identity.get('version')==version and identity.get('platform')==expected_platform and
       identity.get('arch')==expected_arch and identity.get('test') is True,'installed runtime identity absent')
  log=read('mouse-633-upgrade-'+mode+'.log')
  need(isinstance(log,bytes) and 0<len(log)<=8*1024**2 and sha(log)==bound.get('logSha256') and
       'MOUSE_633_UPGRADE_PROFILE_'+mode.upper()+'_PASS' in log.decode('utf-8').splitlines(), 'native probe log differs')
  app=read('mouse-633-upgrade-'+mode+'-app.log')
  need(isinstance(app,bytes) and 0<len(app)<=16*1024**2 and
       all(marker in app.decode('utf-8') for marker in ('MOUSE_EXIT_SAVED','MOUSE_APP_QUIT')),
       'old/new app did not save and quit through its real lifecycle')
  profile=report.get('profile',{})
  need(all(profile.get(flag) is True for flag in ('cookiePreserved','localStoragePreserved','bookmarkPreserved',
       'tabPreserved','preferencesPreserved')) and profile.get('preferences')=={'theme':'dark','aiWidth':413,'libraryWidth':417},
       'profile values were not preserved')
  need(isinstance(profile.get('pageId'),str) and bool(profile['pageId']) and
       isinstance(profile.get('url'),str) and re.fullmatch(r'http://127\.0\.0\.1:\d+/persisted',profile['url']) and
       isinstance(profile.get('tokenSha256'),str) and re.fullmatch('[0-9a-f]{64}',profile['tokenSha256']),
       'owned profile identity missing')
  reports.append(report)
 need(reports[0]['pid']!=reports[1]['pid'] and reports[0]['profile']==reports[1]['profile'],
      'same process or different profile cannot prove an upgrade')
 if expected_platform=='win32':
  for key in ('oldInstallation','replacement'):
   installation=facts.get(key,{})
   need(installation.get('exitCode')==0 and installation.get('peMachine')=='0x8664' and
        installation.get('unicodeAndSpaces') is True,'native Windows installation failed')
 return {'ok':True,'fromVersion':'6.0.32','toVersion':'6.0.33','platform':expected_platform,'arch':expected_arch,
         'method':METHOD,'inputs':inputs,'baseline':expected_baseline,'package':expected_package,
         'oldPid':reports[0]['pid'],'newPid':reports[1]['pid'],'closedProfileSha256':facts['closedProfileSha256']}
