#!/usr/bin/env python3
"""Reuse immutable635 algorithms with explicit636 runtime/module identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse637-reuse.py")))
_reuse["load"]('mouse635-windows-release.py',namespace=globals())
_channel637=runpy.run_path(str(Path(__file__).with_name('mouse637-public-channel.py')))
_preserved_channel=channel


def channel():
 _preserved_channel()
 _channel637['verify'](OUT,pin(),'win32')


def validate_template():
 p=json.loads((STAGE/'pin.json').read_text(encoding='utf-8'))
 if p.get('version')!=VERSION or type(p.get('ready')) is not bool or p.get('sourceBranch')!='main' or p.get('previous')!=PREVIOUS_WINDOWS:
  raise ValueError('Invalid637 Windows candidate or retained predecessor')
 if not (STAGE/'RELEASE_NOTES.md').read_text(encoding='utf-8').startswith('# Mouse Browser '+VERSION):
  raise ValueError('Windows release notes version differs')
 if p['ready'] is False:
  for key in ('source','sourceMerge','sourcePR','run','attempt','job','artifact','artifactSHA256','verificationArtifact','verificationSHA256'):
   if p.get(key) is not None:raise ValueError('Unready Windows provenance must be null: '+key)
  if p.get('package')!={'name':'Mouse-Browser-6.0.37-Windows-x64.exe','size':None,'sha256':None} or (STAGE/'PUBLISH_OWNER').exists():
   raise ValueError('Unready Windows package claims or owner trigger')
 return p

if __name__=="__main__":
 commands={"validate-template":validate_template,"import":import_candidate,"verify":verify_installed,"publish":publish,"channel":channel}
 if len(sys.argv)!=2 or sys.argv[1] not in commands: raise SystemExit("Expected a supported publisher action")
 if sys.argv[1] != 'validate-template':
  runpy.run_path(str(Path(__file__).with_name('mouse637-publish-plan.py')))['require_ready']('windows-x64')
 commands[sys.argv[1]]()
