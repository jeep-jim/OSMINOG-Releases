#!/usr/bin/env python3
"""Run byte-frozen633 algorithms against634 facts; never rewrite evidence."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained = _reuse['load']('test-mouse633-evidence.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

# The owner634 request supersedes only the download strip geometry and its
# terminal widget. Retained synthetic fixtures are adapted, never native files.
_old_feedback_fixture=feedback_fixture

def feedback_fixture():
 facts,blobs=_old_feedback_fixture()
 import copy
 def current(ui,tab,active,identity):
  ui.update(placement='bottom',pane={'x':0,'y':0,'width':64,'height':104},head={'x':0,'y':0,'width':64,'height':28},slot={'x':0,'y':28,'width':64,'height':54 if active else 76},dock={'x':0,'y':82,'width':64,'height':22} if active else None,activeWidgetCount=int(active),topDownloadCount=0)
  ui['footer'].update(unreadCount=0,badgeColor='rgb(7, 130, 60)',badgeHidden=True)
  if active:
   pill=ui['pill'];pill.update(bounds={'x':0,'y':88,'width':64,'height':16},downloadIds=[identity],count=1,text='',radius='999px',trackColor='rgb(83, 207, 139)',fillColor='rgb(7, 130, 60)',indeterminate=pill['ariaNow'] is None)
   if pill['ariaNow'] is not None:pill['value']=str(int(float(pill['ariaNow'])))+'%'
  else:ui['pill']=None
  return ui
 for row in facts['downloads']['events']:
  tab=row['activity']['tabId'];active=row['task']['phase']=='running'
  baseline=current(copy.deepcopy(row['ui']),tab,False,row['activity']['id'])
  current(row['ui'],tab,active,row['activity']['id']);row['native']['bounds']=copy.deepcopy(row['ui']['slot'])
  row['before']={'ui':baseline,'native':{'tabId':tab,'bounds':copy.deepcopy(baseline['slot'])}}
 for row in facts['downloads']['screenshots']:
  tab=row['native']['tabId'];current(row['ui'],tab,True,'known');row['native']['bounds']=copy.deepcopy(row['ui']['slot'])
 return facts,blobs


def retained_algorithm_identity(self):
 import ast
 original=ast.parse(Path(__file__).with_name('mouse632-evidence.py').read_text())
 current=_reuse['adapted_tree']('mouse632-evidence.py')
 class Restore(ast.NodeTransformer):
  def visit_Constant(self,node):
   if isinstance(node.value,str):node.value=node.value.replace('6.0.34','6.0.32').replace('mouse634-','mouse632-')
   return node
 before={n.name:ast.dump(n) for n in original.body if isinstance(n,ast.FunctionDef)}
 after={n.name:ast.dump(Restore().visit(n)) for n in current.body if isinstance(n,ast.FunctionDef)}
 changed={name for name in before if before[name]!=after[name]}
 self.assertEqual(changed,{'download_geometry','verify_feedback'})
 for name in before:
  if name not in changed:self.assertEqual(before[name],after[name],name)


def terminal_counters(self):
 for received,total in ((0,1048576),(0,0),(0,-1),(57344,1048576)):
  facts,blobs=feedback_fixture()
  native=next(row for row in facts['downloads']['nativeEvents'] if row['activity']['id']=='broken' and row['event']=='done')
  sample=next(row for row in facts['downloads']['events'] if row['activity']['id']=='broken')
  native.update(received=received,total=total);native['activity'].update(received=received,total=max(0,total));sample['activity'].update(received=received,total=max(0,total));sample['task']['percent']=received/total*100 if total>0 else None
  self.assertIsNone(sample['ui']['pill'])
  self.assertEqual(E.verify_feedback(blobs.__getitem__,facts)['nativeDownloadItems'],6)

Evidence630Tests.test_migrated_feature_algorithms_only_change_runtime_and_artifact_names=retained_algorithm_identity
Evidence630Tests.test_retained_core_only_changes_versions_and_superseded_tutorial=retained_algorithm_identity
Evidence630Tests.test_retry_terminal_counters_can_reset_without_erasing_prior_delivery=terminal_counters

if __name__=='__main__':unittest.main()
