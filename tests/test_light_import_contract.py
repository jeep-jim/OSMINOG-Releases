import importlib.util,pathlib,unittest
spec=importlib.util.spec_from_file_location('importer',pathlib.Path(__file__).resolve().parents[1]/'tools/import_verified_chrome_ci.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LightGates(unittest.TestCase):
 def test_light_adds_gate_never_replaces_old_gates(self):
  self.assertEqual(m.required_workflows('light-storage'),m.REQUIRED_WORKFLOWS|{412858774})
  self.assertEqual(m.required_workflows(None),m.REQUIRED_WORKFLOWS)
 def test_unknown_profile_rejected(self):
  with self.assertRaises(ValueError):m.required_workflows('skip-ci')
