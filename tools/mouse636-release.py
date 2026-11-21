#!/usr/bin/env python3
"""Exact package publication through retained gates and mandatory636 evidence."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse636-reuse.py')))
_reuse['load']('mouse634-release.py',namespace=globals())

GATES=[('x-taskStressGate','mouse636-task-evidence.py'),('x-ownerFeedbackGate','mouse636-feedback-evidence.py'),('x-currentOwnerGate','mouse636-633-owner-evidence.py'),('x-currentContextGate','mouse636-context-evidence.py'),('x-workspaceGeometryGate','mouse636-workspace-evidence.py'),('x-currentUpgradeGate','mouse636-upgrade-evidence.py'),('x-current634OwnerGate','mouse636-retained-owner-evidence.py'),('x-current635OwnerGate','mouse636-owner-feedback-evidence.py'),('x-searchRemovalGate','mouse636-search-removal-evidence.py'),('x-performanceGate','mouse636-performance-evidence.py'),('x-libraryStabilityGate','mouse636-library-evidence.py'),('x-agentInlineGate','mouse636-agent-inline-evidence.py'),('x-paneLayoutGate','mouse636-pane-layout-evidence.py')]
RETAINED_DEPENDENCIES=('mouse636-retained-native-evidence.py','mouse636-download-evidence.py','mouse636-capture-evidence.py','mouse636-focused-evidence.py','mouse636-reuse.py')
CURRENT_DEPENDENCIES=('mouse636-native-evidence.py','mouse636-library-evidence.py','mouse636-search-removal-evidence.py','mouse636-performance-evidence.py','mouse636-agent-inline-evidence.py','mouse636-pane-layout-evidence.py','mouse636-context-evidence.py','mouse636-reuse.py')
GATES.append(('x-motionTraceGate','mouse636-motion-trace.py'))
_trace636=runpy.run_path(str(Path(__file__).with_name('mouse636-motion-trace.py')))


def verify_628_trace(read,provenance):
 names=['mouse-628-motion-trace.json','mouse-628-motion.json']
 blobs={name:read(name) for name in names}
 if not all(0<len(value)<=72*1024**2 for value in blobs.values()):raise ValueError('Missing/oversized trace input')
 report=_trace636['verify_trace_data'](json.loads(blobs[names[0]]),json.loads(blobs[names[1]]))
 if report.get('status')!='pass' or report.get('algorithm')!=_trace636['ALGORITHM'] or report.get('directIdentityLink') is not False:raise ValueError('Motion trace rejected')
 return {'version':V,'inputs':{name:{'size':len(blobs[name]),'sha256':sha(blobs[name])} for name in names},'provenance':provenance,'evidence':report}


def validate_template():
 if PIN.get('version')!=V or type(PIN.get('ready')) is not bool:raise ValueError('Mouse636 pin template identity/state invalid')
 if not (STAGE/'RELEASE_NOTES.md').read_text(encoding='utf-8').startswith('# Mouse Browser 6.0.36'):raise ValueError('Release notes version mismatch')
 schema=json.loads((STAGE/'evidence.schema.json').read_text(encoding='utf-8'))
 required=set(_evidence.JSON_NAMES)|{'mouse-631-native.json','mouse-631-task.json','mouse-631-stress.json','mouse-632-media.json','mouse-632-footer.json','mouse-632-documents.json','mouse-633-owner-feedback.json','mouse-633-context-menu.json','mouse-636-retained-owner-feedback.json','mouse-634-download-widget.json','mouse-634-ai-download-widget.json','mouse-634-focused-chrome.json','mouse-636-upgrade.json','mouse-636-upgrade-write.json','mouse-636-upgrade-read.json','mouse-636-owner-feedback.json','mouse-636-search-removal.json','mouse-636-agent-inline.json','mouse-636-performance.json','mouse-636-baseline-performance.json','mouse-636-desktop-transition.json','mouse-635-library.json'}
 if set(schema['required'])!=required or schema['x-motionTraceGate']['algorithm']!=_trace636['ALGORITHM']:raise ValueError('Evidence schema mismatch')
 for key,module in GATES:
  gate=schema[key]
  if gate['validator']!='tools/'+module or gate['sha256']!=sha(Path(__file__).with_name(module).read_bytes()) or gate['sourceAndFreshInstalled'] is not True:raise ValueError('Independent636 checker contract mismatch: '+module)
 for key,names in [('x-current634OwnerGate',RETAINED_DEPENDENCIES),('x-current635OwnerGate',CURRENT_DEPENDENCIES)]:
  if schema[key].get('dependencies')!={name:sha(Path(__file__).with_name(name).read_bytes()) for name in names}:raise ValueError('Independent636 dependency hashes differ: '+key)
 if PIN['ready'] is False:
  for key in ('source','run','artifact','archiveSHA256','verificationArtifact','verificationSHA256','sourcePR','sourceMerge','sourceAttempt','sourceJob'):
   if PIN.get(key) is not None:raise ValueError('Unready template contains provenance claims: '+key)
  if set(PIN.get('packages',{}))!={DMG,ZIP} or any(value!={'size':None,'sha256':None} for value in PIN['packages'].values()):raise ValueError('Unready template contains package claims')
  if (STAGE/'PUBLISH_OWNER').exists():raise ValueError('Unready template must not have an owner trigger')
 print('MOUSE636_RELEASE_TEMPLATE_CONTRACT_PASS',flush=True)


if __name__=='__main__':
 actions={'validate-template':validate_template,'validate':validate,'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('Expected validate-template, validate, import, publish or channel')
 if sys.argv[1] not in ('validate-template','validate'):
  runpy.run_path(str(Path(__file__).with_name('mouse636-publish-plan.py')))['require_ready']('macos-arm64')
  validate()
 actions[sys.argv[1]]()
