#!/usr/bin/env python3
"""Exact package publication through retained gates and mandatory636 evidence."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse637-reuse.py')))
_reuse['load']('mouse634-release.py',namespace=globals())

GATES=[('x-taskStressGate','mouse637-task-evidence.py'),('x-ownerFeedbackGate','mouse637-feedback-evidence.py'),('x-currentOwnerGate','mouse637-633-owner-evidence.py'),('x-currentContextGate','mouse637-context-evidence.py'),('x-workspaceGeometryGate','mouse637-workspace-evidence.py'),('x-currentUpgradeGate','mouse637-upgrade-evidence.py'),('x-current634OwnerGate','mouse637-retained-owner-evidence.py'),('x-current635OwnerGate','mouse637-owner-feedback-evidence.py'),('x-searchRemovalGate','mouse637-search-removal-evidence.py'),('x-performanceGate','mouse637-performance-evidence.py'),('x-libraryStabilityGate','mouse637-library-evidence.py'),('x-agentInlineGate','mouse637-agent-inline-evidence.py'),('x-paneLayoutGate','mouse637-pane-layout-evidence.py')]
RETAINED_DEPENDENCIES=('mouse637-retained-native-evidence.py','mouse637-download-evidence.py','mouse637-capture-evidence.py','mouse637-focused-evidence.py','mouse637-reuse.py','mouse637-zoom-evidence.py')
CURRENT_DEPENDENCIES=('mouse637-native-evidence.py','mouse637-library-evidence.py','mouse637-search-removal-evidence.py','mouse637-performance-evidence.py','mouse637-agent-inline-evidence.py','mouse637-pane-layout-evidence.py','mouse637-context-evidence.py','mouse637-reuse.py','mouse637-zoom-evidence.py')
FEATURE_DEPENDENCIES=('mouse637-native-evidence.py','mouse637-presets-evidence.py','mouse637-sidebar-focus-evidence.py','mouse637-library-actions-evidence.py','mouse637-update-ui-evidence.py')
GATES.extend([('x-motionTraceGate','mouse637-motion-trace.py'),('x-current637FeaturesGate','mouse637-features-evidence.py'),('x-currentUpdateButtonGate','mouse637-update-button-evidence.py'),('x-currentHelpersGate','mouse637-current.py')])
_trace636=runpy.run_path(str(Path(__file__).with_name('mouse637-motion-trace.py')))
_channel637=runpy.run_path(str(Path(__file__).with_name('mouse637-public-channel.py')))
_preserved_channel=channel


def channel():
 _preserved_channel()
 _channel637['verify'](OUT,PIN,'darwin')


def verify_628_trace(read,provenance):
 names=['mouse-628-motion-trace.json','mouse-628-motion.json']
 blobs={name:read(name) for name in names}
 if not all(0<len(value)<=72*1024**2 for value in blobs.values()):raise ValueError('Missing/oversized trace input')
 report=_trace636['verify_trace_data'](json.loads(blobs[names[0]]),json.loads(blobs[names[1]]))
 if report.get('status')!='pass' or report.get('algorithm')!=_trace636['ALGORITHM'] or report.get('directIdentityLink') is not False:raise ValueError('Motion trace rejected')
 return {'version':V,'inputs':{name:{'size':len(blobs[name]),'sha256':sha(blobs[name])} for name in names},'provenance':provenance,'evidence':report}


def validate_template():
 if PIN.get('version')!=V or type(PIN.get('ready')) is not bool:raise ValueError('Mouse636 pin template identity/state invalid')
 if not (STAGE/'RELEASE_NOTES.md').read_text(encoding='utf-8').startswith('# Mouse Browser 6.0.37'):raise ValueError('Release notes version mismatch')
 schema=json.loads((STAGE/'evidence.schema.json').read_text(encoding='utf-8'))
 required=set(_evidence.JSON_NAMES)|{'mouse-631-native.json','mouse-631-task.json','mouse-631-stress.json','mouse-632-media.json','mouse-632-footer.json','mouse-632-documents.json','mouse-633-owner-feedback.json','mouse-633-context-menu.json','mouse-636-retained-owner-feedback.json','mouse-634-download-widget.json','mouse-634-ai-download-widget.json','mouse-634-focused-chrome.json','mouse-637-upgrade.json','mouse-637-upgrade-write.json','mouse-637-upgrade-read.json','mouse-636-owner-feedback.json','mouse-636-search-removal.json','mouse-636-agent-inline.json','mouse-637-performance.json','mouse-637-baseline-performance.json','mouse-636-desktop-transition.json','mouse-635-library.json','mouse-637-features.json','mouse-637-features-write.json','mouse-637-features-processes.json','mouse-637-update-button.json','mouse-637-update-button-profile-write.json','mouse-637-update-button-profile-read.json','mouse-637-update-button-native.json'}
 if set(schema['required'])!=required or schema['x-motionTraceGate']['algorithm']!=_trace636['ALGORITHM']:raise ValueError('Evidence schema mismatch')
 for key,module in GATES:
  gate=schema[key]
  if gate['validator']!='tools/'+module or gate['sha256']!=sha(Path(__file__).with_name(module).read_bytes()) or gate['sourceAndFreshInstalled'] is not True:raise ValueError('Independent636 checker contract mismatch: '+module)
 for key,names in [('x-current634OwnerGate',RETAINED_DEPENDENCIES),('x-current635OwnerGate',CURRENT_DEPENDENCIES),('x-current637FeaturesGate',FEATURE_DEPENDENCIES),('x-currentHelpersGate',('mouse637-windows-display-evidence.py',))]:
  if schema[key].get('dependencies')!={name:sha(Path(__file__).with_name(name).read_bytes()) for name in names}:raise ValueError('Independent636 dependency hashes differ: '+key)
 features=runpy.run_path(str(Path(__file__).with_name('mouse637-features-evidence.py')))
 feature_gate=schema['x-current637FeaturesGate']
 if (feature_gate.get('nativeCaptureNames')!=features['CAPTURES'] or feature_gate.get('nativeCaptures')!=len(features['CAPTURES'])
     or feature_gate.get('writeNativeCaptures')!=len(features['CAPTURES'])-2 or feature_gate.get('readNativeCaptures')!=2):
  raise ValueError('Exact637 feature frame ledger differs')
 if schema.get('x-publicationDependencies')!={'mouse637-public-channel.py':sha(Path(__file__).with_name('mouse637-public-channel.py').read_bytes())}:
  raise ValueError('Published636 anonymous updater checker hash differs')
 if PIN['ready'] is False:
  for key in ('source','run','artifact','archiveSHA256','verificationArtifact','verificationSHA256','sourcePR','sourceMerge','sourceAttempt','sourceJob'):
   if PIN.get(key) is not None:raise ValueError('Unready template contains provenance claims: '+key)
  if set(PIN.get('packages',{}))!={DMG,ZIP} or any(value!={'size':None,'sha256':None} for value in PIN['packages'].values()):raise ValueError('Unready template contains package claims')
  if (STAGE/'PUBLISH_OWNER').exists():raise ValueError('Unready template must not have an owner trigger')
 print('MOUSE637_RELEASE_TEMPLATE_CONTRACT_PASS',flush=True)


if __name__=='__main__':
 actions={'validate-template':validate_template,'validate':validate,'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('Expected validate-template, validate, import, publish or channel')
 if sys.argv[1] not in ('validate-template','validate'):
  runpy.run_path(str(Path(__file__).with_name('mouse637-publish-plan.py')))['require_ready']('macos-arm64')
  validate()
 actions[sys.argv[1]]()
