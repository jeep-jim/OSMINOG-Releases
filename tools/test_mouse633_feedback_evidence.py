#!/usr/bin/env python3
"""Retained media/document/footer rejection fixtures, synthetic inputs only.

The new owner report is checked separately. These unchanged media/document
algorithms and updated footer cases run through production verify_retained.
"""
import runpy
from pathlib import Path
from types import SimpleNamespace
import unittest
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_tests = _reuse['load']('test_mouse632_feedback_evidence.py', namespace=globals())
globals().update({key:value for key,value in _tests.items() if not key.startswith('__')})
CURRENT = CHECK
CHECK = SimpleNamespace(JSON_NAMES=CURRENT.CORE_JSON_NAMES, T=CURRENT.T, verify=CURRENT.verify_retained)
_old_fixtures = fixtures


def fixtures():
    files, facts = _old_fixtures()
    footer = facts[CHECK.JSON_NAMES[2]]
    footer.pop('manualHelper')
    footer['agentAvailability'] = dict.fromkeys(('settingsEntry','startEntry','providerEntry','openedExplicitly',
        'disabledUntilEnabled','closed','pagesPreserved','layoutPreserved','restoredAfterReload'), True)
    for row in footer['cases']:
        row['controls']['right'][-1] = 'settings-button'
        row['controls']['footerSettings'] = 1
        row['controls']['footerClosePane'] = 0
    return files, facts


def current_entry_contract(self):
    for group in ('websiteOffer','agentAvailability'):
        for field,value in self.original[CHECK.JSON_NAMES[2]][group].items():
            if type(value) is not bool: continue
            self.setUp();self.footer[group][field]=1;self.reject()
    self.setUp();self.footer['websiteOffer']['confirmedUrl']='https://example.com';self.reject('destination')
    self.setUp();self.footer['cases'][0]['controls']['right'][-1]='quit';self.reject('footer order')
    self.setUp();self.footer['cases'][0]['controls']['footerSettings']=0;self.reject('obsolete')
    for value in (None,False,1):
        self.setUp();self.footer['cases'][0]['controls']['footerClosePane']=value;self.reject('obsolete')


FeedbackContract.test_website_confirmation_and_manual_helper_cannot_be_missing_or_truthy = current_entry_contract


class LinuxRetainedFeedback(unittest.TestCase):
    # Reuse fixture setup without duplicating the inherited rejection suite.
    setUpClass = classmethod(FeedbackContract.setUpClass.__func__)
    setUp = FeedbackContract.setUp
    verify = FeedbackContract.verify
    def test_complete_linux_feedback_scope(self):
        for value in self.facts.values(): value.update(platform='linux',arch='x64')
        for row in self.footer['cases']: row['controls']['source']='mouse-head.svg'
        result=self.verify('linux','x64')
        self.assertTrue(result['ok'])
        self.assertEqual(result['documents']['unchangedOriginalFiles'],9)
        self.assertTrue(result['footer']['agentRestored'])


if __name__ == '__main__': unittest.main()
