#!/usr/bin/env python3
"""Publish634 through frozen633 package gates and the current native request."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained=_reuse['load']('mouse633-release.py',namespace=globals())
globals().update({key:value for key,value in _retained.items() if not key.startswith('__')})

# Task progress remains in the header; only actual downloads moved below pages.
FEATURE_TOKENS_630=(FEATURE_TOKENS_630-{'header-progress-pill'})|{'header-task-progress-pill'}
FEATURE_TOKENS_632|={'pane-bottom-download-widgets','green-download-counter','right-ai-links-lower-preview','rounded-capture-composition'}
_retained.update(FEATURE_TOKENS_630=FEATURE_TOKENS_630,FEATURE_TOKENS_632=FEATURE_TOKENS_632)


def validate_template():
 if PIN.get('version')!=V or type(PIN.get('ready')) is not bool:
  raise ValueError('Mouse634 pin template version/state invalid')
 if not (STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser 6.0.34'):
  raise ValueError('Release notes version mismatch')
 schema=json.loads((STAGE/'evidence.schema.json').read_text())
 required=set(_evidence.JSON_NAMES)|{'mouse-631-native.json','mouse-631-task.json','mouse-631-stress.json','mouse-632-media.json','mouse-632-footer.json','mouse-632-documents.json','mouse-633-owner-feedback.json','mouse-633-context-menu.json','mouse-634-owner-feedback.json','mouse-634-download-widget.json','mouse-634-ai-download-widget.json','mouse-634-focused-chrome.json','mouse-634-upgrade.json','mouse-634-upgrade-write.json','mouse-634-upgrade-read.json'}
 if set(schema['required'])!=required or schema['x-motionTraceGate']['algorithm']!='mouse628-motion-trace-evidence-v2':
  raise ValueError('Evidence schema mismatch')
 gates=[('x-taskStressGate','mouse634-task-evidence.py'),('x-ownerFeedbackGate','mouse634-feedback-evidence.py'),('x-currentOwnerGate','mouse634-retained-owner-evidence.py'),('x-currentContextGate','mouse634-context-evidence.py'),('x-workspaceGeometryGate','mouse634-workspace-evidence.py'),('x-currentUpgradeGate','mouse634-upgrade-evidence.py'),('x-current634OwnerGate','mouse634-owner-feedback-evidence.py')]
 for key,module in gates:
  gate=schema[key]
  if gate['validator']!='tools/'+module or gate['sha256']!=sha(Path(__file__).with_name(module).read_bytes()) or gate['sourceAndFreshInstalled'] is not True:
   raise ValueError('Independent634 checker contract mismatch: '+module)
 dependencies=schema['x-current634OwnerGate'].get('dependencies',{})
 names=('mouse634-native-evidence.py','mouse634-download-evidence.py','mouse634-capture-evidence.py','mouse634-focused-evidence.py')
 if dependencies!={name:sha(Path(__file__).with_name(name).read_bytes()) for name in names}:
  raise ValueError('Independent634 native dependency hashes differ')
 if PIN['ready'] is False:
  for key in ('source','run','artifact','archiveSHA256','verificationArtifact','verificationSHA256','sourcePR','sourceMerge','sourceAttempt','sourceJob'):
   if PIN.get(key) is not None: raise ValueError('Unready template contains provenance claims: '+key)
  if set(PIN.get('packages',{}))!={DMG,ZIP} or any(value!={'size':None,'sha256':None} for value in PIN['packages'].values()): raise ValueError('Unready template contains package claims')
  if (STAGE/'PUBLISH_OWNER').exists(): raise ValueError('Unready template must not have an owner trigger')
 print('MOUSE634_RELEASE_TEMPLATE_CONTRACT_PASS',flush=True)


if __name__=='__main__':
 actions={'validate-template':validate_template,'validate':validate,'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions: raise SystemExit('Expected validate-template, validate, import, publish or channel')
 if sys.argv[1] not in ('validate-template','validate'): validate()
 actions[sys.argv[1]]()
