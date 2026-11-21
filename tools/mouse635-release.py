#!/usr/bin/env python3
"""Exact package publication through retained gates and mandatory635 evidence."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse635-reuse.py')))
_reuse['load']('mouse634-release.py',namespace=globals())

GATES=[('x-taskStressGate','mouse635-task-evidence.py'),('x-ownerFeedbackGate','mouse635-feedback-evidence.py'),('x-currentOwnerGate','mouse635-633-owner-evidence.py'),('x-currentContextGate','mouse635-context-evidence.py'),('x-workspaceGeometryGate','mouse635-workspace-evidence.py'),('x-currentUpgradeGate','mouse635-upgrade-evidence.py'),('x-current634OwnerGate','mouse635-retained-owner-evidence.py'),('x-current635OwnerGate','mouse635-owner-feedback-evidence.py'),('x-publicSearchGate','mouse635-public-search-evidence.py'),('x-libraryStabilityGate','mouse635-library-evidence.py'),('x-agentChatGate','mouse635-agent-chat-evidence.py'),('x-paneLayoutGate','mouse635-pane-layout-evidence.py')]
RETAINED_DEPENDENCIES=('mouse635-retained-native-evidence.py','mouse635-download-evidence.py','mouse635-capture-evidence.py','mouse635-focused-evidence.py','mouse635-search-evidence.py','mouse635-reuse.py')
CURRENT_DEPENDENCIES=('mouse635-native-evidence.py','mouse635-library-evidence.py','mouse635-public-search-evidence.py','mouse635-agent-chat-evidence.py','mouse635-pane-layout-evidence.py','mouse635-context-evidence.py','mouse635-reuse.py')


def validate_template():
 if PIN.get('version')!=V or type(PIN.get('ready')) is not bool:raise ValueError('Mouse635 pin template identity/state invalid')
 if not (STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser 6.0.35'):raise ValueError('Release notes version mismatch')
 schema=json.loads((STAGE/'evidence.schema.json').read_text())
 required=set(_evidence.JSON_NAMES)|{'mouse-631-native.json','mouse-631-task.json','mouse-631-stress.json','mouse-632-media.json','mouse-632-footer.json','mouse-632-documents.json','mouse-633-owner-feedback.json','mouse-633-context-menu.json','mouse-634-owner-feedback.json','mouse-634-download-widget.json','mouse-634-ai-download-widget.json','mouse-634-focused-chrome.json','mouse-635-search.json','mouse-635-upgrade.json','mouse-635-upgrade-write.json','mouse-635-upgrade-read.json','mouse-635-owner-feedback.json','mouse-635-public-search.json','mouse-635-library.json'}
 if set(schema['required'])!=required or schema['x-motionTraceGate']['algorithm']!='mouse628-motion-trace-evidence-v2':raise ValueError('Evidence schema mismatch')
 for key,module in GATES:
  gate=schema[key]
  if gate['validator']!='tools/'+module or gate['sha256']!=sha(Path(__file__).with_name(module).read_bytes()) or gate['sourceAndFreshInstalled'] is not True:raise ValueError('Independent635 checker contract mismatch: '+module)
 for key,names in [('x-current634OwnerGate',RETAINED_DEPENDENCIES),('x-current635OwnerGate',CURRENT_DEPENDENCIES)]:
  if schema[key].get('dependencies')!={name:sha(Path(__file__).with_name(name).read_bytes()) for name in names}:raise ValueError('Independent635 dependency hashes differ: '+key)
 if PIN['ready'] is False:
  for key in ('source','run','artifact','archiveSHA256','verificationArtifact','verificationSHA256','sourcePR','sourceMerge','sourceAttempt','sourceJob'):
   if PIN.get(key) is not None:raise ValueError('Unready template contains provenance claims: '+key)
  if set(PIN.get('packages',{}))!={DMG,ZIP} or any(value!={'size':None,'sha256':None} for value in PIN['packages'].values()):raise ValueError('Unready template contains package claims')
  if (STAGE/'PUBLISH_OWNER').exists():raise ValueError('Unready template must not have an owner trigger')
 print('MOUSE635_RELEASE_TEMPLATE_CONTRACT_PASS',flush=True)


if __name__=='__main__':
 actions={'validate-template':validate_template,'validate':validate,'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('Expected validate-template, validate, import, publish or channel')
 if sys.argv[1] not in ('validate-template','validate'):validate()
 actions[sys.argv[1]]()
