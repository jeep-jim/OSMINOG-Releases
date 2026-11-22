#!/usr/bin/env python3
"""Portable actual-core/launcher tests and an explicit Mac owned-child contract."""
import argparse
import ast
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import runpy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('host_observer', TOOLS / 'mouse637-host-observer.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

DRIVER = r'''
#define MOUSE_HOST_OBSERVER_TEST 1
#include SOURCE
typedef struct { uint64_t now; int cycles, mode, root_reads; Process root, child, parent; } Fake;
static uint64_t fake_now(void *p) { Fake *f=p; return ++f->now; }
static int fake_read(void *p,int pid,Process *out) {
 Fake *f=p;
 if (f->cycles>=4 && pid==101) return ESRCH;
 if (pid==101) { *out=f->root; ++f->root_reads; }
 else if (pid==102) { *out=f->child; }
 else if (pid==9) { *out=f->parent; f->now+=7; }
 else return ESRCH;
 if (f->mode==4 && pid==102 && f->cycles>=2) out->ppid=1;
 if (f->mode==5 && pid==102 && f->cycles>=2) { out->start_abs+=500;out->start_usec++; }
 if (f->mode==6 && pid==102 && f->cycles>=2) { strcpy(out->path,"/owned/new-image");out->uuid[0]=2; }
 if (f->mode==7 && pid==102 && f->cycles>=2) return EACCES;
 if (pid==101 && f->cycles>=2) {
  if (f->mode==18 || f->mode==20 || f->mode==22 || f->mode==23 || f->mode==24 || f->mode==28) {
   strcpy(out->path,"/owned/python-runtime");out->uuid[0]=3;
  }
  if (f->mode==21 || f->mode==32) { strcpy(out->path,"/unowned/unknown-runtime");out->uuid[0]=4; }
  if ((f->mode==22 && f->cycles>=3) || f->mode==25) { strcpy(out->path,"/owned/root");out->uuid[0]=1; }
  if (f->mode==26) { strcpy(out->path,"/owned/python-runtime");out->uuid[0]=4; }
  if (f->mode==28) out->ppid=1;
  if (f->mode==35) out->ppid=1;
 }
 if (pid==101 && f->mode==36 && f->cycles==1) out->ppid=1;
 if (pid==9) {
  if (f->mode==23 && f->cycles>=2) { out->start_abs+=500;out->start_usec++; }
  if (f->mode==24 && f->cycles>=2) { strcpy(out->path,"/unowned/changed-parent");out->uuid[0]=4; }
  if (f->mode==29) return ESRCH;
  if (f->mode==30) out->uid++;
  if (f->mode==31) out->start_abs=f->root.start_abs+1;
 }
 out->user=f->now/10;out->system=f->now/20;out->runnable=1; /* no runnable >= CPU assumption */
 return 0;
}
static int fake_children(void *p,int pid,int *out,size_t cap) {
 Fake *f=p;(void)cap;
 if (f->mode==3 && pid==101) { ++f->root.start_abs; ++f->root.start_usec; }
 if (f->mode==8) return -EACCES;
 if (f->mode==9) return MAX_OWNED+1;
 if (pid==101 && !(f->mode==4 && f->cycles>=2)) { out[0]=102;return 1; }
 return 0;
}
static int fake_host(void *p,uint32_t ticks[4],uint64_t *u,uint64_t *s) {
 Fake *f=p;++f->cycles;
 if (f->mode==10) return EACCES;
 ticks[0]=(uint32_t)(UINT32_MAX-2u+(unsigned)f->cycles);ticks[1]=(uint32_t)f->cycles;ticks[2]=10;ticks[3]=0;
 *u=100;*s=100;return 0;
}
static int fake_self(void *p,uint64_t *u,uint64_t *s) {
 Fake *f=p;*u=f->mode==11?100000:200;*s=200;return 0;
}
static void fake_sleep(void *p,uint64_t t) { Fake *f=p;f->now=t;if(f->mode==12) f->now+=750000000u; }
int main(int argc,char **argv) {
 if(argc!=2)return 3;
 Fake f={.now=1000000000u,.mode=atoi(argv[1])};
 f.root=(Process){.pid=101,.ppid=9,.uid=1000,.start_sec=100,.start_usec=1,.start_abs=999000000u};
 f.child=(Process){.pid=102,.ppid=101,.uid=1000,.start_sec=100,.start_usec=2,.start_abs=999500000u};
 f.parent=(Process){.pid=9,.ppid=8,.uid=1000,.start_sec=99,.start_usec=1,.start_abs=900000000u};
 strcpy(f.root.path,"/owned/root");strcpy(f.child.path,"/owned/child");f.root.uuid[0]=1;f.child.uuid[0]=1;
 strcpy(f.parent.path,"/owned/python-runtime");f.parent.uuid[0]=3;
 if(f.mode==19 || f.mode==25 || f.mode==27) { strcpy(f.root.path,f.parent.path);memcpy(f.root.uuid,f.parent.uuid,16); }
 if(f.mode==32) { strcpy(f.parent.path,f.root.path);memcpy(f.parent.uuid,f.root.uuid,16); }
 State *s=calloc(1,sizeof(*s));s->records=calloc(MAX_RECORDS,sizeof(Record));
 s->ok=true;s->reason="started";s->root_pid=101;s->parent_pid=9;s->sampler_pid=202;s->uid=1000;
 s->numer=1;s->denom=1;s->budget_ms=10000;s->logical_cpus=4;
 s->launch_before_us=100000000u;s->launch_after_us=100000010u;
 strcpy(s->root_path,"/owned/root");strcpy(s->phase,"fixture");memset(s->nonce,'a',64);
 if(f.mode==20 || f.mode==27 || f.mode==34) { strcpy(s->phase,"candidate");s->budget_ms=400000; }
 strcpy(s->kernel,"fixture");strcpy(s->machine,"fixture");
 s->ops=(Ops){fake_now,fake_read,fake_children,fake_host,fake_self,fake_sleep,&f};
 if(f.mode==1)strcpy(s->root_path,"/foreign/root");
 if(f.mode==2)s->launch_after_us=100000000u;
 if(f.mode==13)s->budget_ms=500;
 if(f.mode==14) { s->count=MAX_RECORDS; bool accepted=record(s,(Record){.kind=HOST}); printf("{\"accepted\":%s,\"ok\":%s,\"reason\":\"%s\"}\n",accepted?"true":"false",s->ok?"true":"false",s->reason);free(s->records);free(s);return 0; }
 if(f.mode==15) { s->owned_count=MAX_OWNED; int i=add_owned(s,&f.child,0,1,2);printf("{\"index\":%d,\"ok\":%s,\"reason\":\"%s\"}\n",i,s->ok?"true":"false",s->reason);free(s->records);free(s);return 0; }
 if(f.mode==16) { s->begin=1;s->end=24000001;s->numer=125;s->denom=3;s->self_user_us=10000;s->self_system_us=0;
   bool exact=self_cpu_within_limit(s);s->self_user_us=10001;bool over=self_cpu_within_limit(s);
   printf("{\"exactBoundary\":%s,\"oneMicrosecondOver\":%s}\n",exact?"true":"false",over?"true":"false");free(s->records);free(s);return 0; }
 if(f.mode==17) { printf("{\"empty\":%d,\"zeroWithPermission\":%d,\"negativeWithIO\":%d,\"threePids\":%d}\n",child_count_result(0,0),child_count_result(0,EPERM),child_count_result(-1,EIO),child_count_result(3,0));free(s->records);free(s);return 0; }
 observe(s);
 bool saved=dump(s,stdout);free(s->records);free(s);return saved?0:4;
}
'''


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='mouse-host-core-')
        cls.directory = Path(cls.temp.name)
        source = cls.directory / 'driver.c'
        source.write_text(DRIVER.replace('SOURCE', json.dumps(str(TOOLS / 'mouse637-host-observer.c'))))
        cls.binary = cls.directory / 'driver'
        compiler = shutil.which('cc')
        if not compiler:
            raise RuntimeError('A C compiler is required for the actual portable observer core')
        subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', str(source), '-o', str(cls.binary)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def core(self, mode):
        result = subprocess.run([str(self.binary), str(mode)], check=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=5)
        return result.stdout, [json.loads(line) for line in result.stdout.splitlines()]

    def test_actual_core_framing_ownership_and_cpu_units(self):
        raw, rows = self.core(0)
        header, eof = rows[0], rows[-1]
        self.assertTrue(eof['ok'])
        self.assertEqual(eof['reason'], 'root-exited')
        self.assertEqual([r['sequence'] for r in rows], list(range(len(rows))))
        self.assertEqual(eof['recordCount'], len(rows)-2)
        self.assertEqual(eof['payloadBytesBeforeEOF'], len(raw)-len(raw.splitlines(keepends=True)[-1]))
        self.assertEqual(header['intervalMs'], 250)
        identities = [r for r in rows if r['type'] == 'identity']
        self.assertEqual([(r['pid'], r['parentIndex']) for r in identities], [(101, -1), (102, 0)])
        self.assertTrue(any(r['runnableTime'] < r['userTime'] for r in rows if r['type'] == 'sample'))
        self.assertTrue(eof['withinSelfCpuLimit'])
        self.assertEqual(eof['selfCpuUs'], eof['selfUserUs'] + eof['selfSystemUs'])

    def test_wrong_root_path_birth_and_reused_parent_fail_before_adoption(self):
        for mode in (1, 2, 3):
            with self.subTest(mode=mode):
                _, rows = self.core(mode)
                self.assertFalse(rows[-1]['ok'])
                self.assertNotIn(102, [r['pid'] for r in rows if r['type'] == 'identity'])

    def test_known_reparent_retained_and_pid_reuse_is_explicit(self):
        _, moved = self.core(4)
        self.assertTrue(moved[-1]['ok'])
        self.assertTrue(any(r['type'] == 'reparent' and r['otherPid'] == 1 for r in moved))
        _, reused = self.core(5)
        self.assertTrue(any(r['type'] == 'reuse' for r in reused))
        ids = [r for r in reused if r['type'] == 'identity']
        self.assertEqual(len({(r['pid'], r['startAbstime']) for r in ids}), len(ids))

    def test_owned_exec_image_transition_keeps_birth_identity(self):
        _, rows = self.core(6)
        self.assertTrue(rows[-1]['ok'])
        image = next(r for r in rows if r['type'] == 'image')
        self.assertEqual(image['path'], '/owned/new-image')
        self.assertTrue(any(r['type'] == 'sample' and r['imageIndex'] == image['imageIndex'] for r in rows))

    def test_python_forward_handoff_and_already_runtime_use_exact_parent_image(self):
        for mode in (18,19):
            with self.subTest(mode=mode):
                _,rows=self.core(mode)
                header,eof=rows[0],rows[-1]
                self.assertTrue(eof['ok'])
                self.assertEqual(header['schema'],2)
                policy=header['rootImagePolicy']
                self.assertEqual(policy['kind'],'python-parent-runtime')
                parent=policy['parentInitial']
                self.assertEqual((parent['pid'],parent['uid'],parent['path'],parent['uuid']),
                                 (9,1000,'/owned/python-runtime','03'+'00'*15))
                root=next(r for r in rows if r['type']=='identity' and r['identityIndex']==0)
                self.assertGreaterEqual(parent['readStartMach'],root['readEndMach'])
                changes=[r for r in rows if r['type']=='image' and r['identityIndex']==0]
                self.assertEqual(len(changes),1 if mode==18 else 0)
                if mode==18:
                    check=policy['parentRecheck']
                    self.assertEqual({k:v for k,v in check.items() if not k.startswith('read')},
                                     {k:v for k,v in parent.items() if not k.startswith('read')})
                    self.assertGreaterEqual(check['readStartMach'],changes[0]['readEndMach'])
                    self.assertEqual(changes[0]['path'],parent['path'])
                    self.assertEqual(changes[0]['uuid'],parent['uuid'])
                else:
                    self.assertIsNone(policy['parentRecheck'])
                    self.assertEqual(root['path'],parent['path'])
                windows=[r['readEndMach']-r['readStartMach'] for r in rows[1:-1]]
                windows.extend(w['readEndMach']-w['readStartMach'] for w in
                               (parent,policy['parentRecheck']) if w is not None)
                self.assertEqual(eof['maxReadTicks'],max(windows))
                self.assertEqual(eof['deadlineMach'],root['startAbstime']+10000*1000000)

    def test_fixed_candidate_unknown_reverse_and_changed_parent_images_fail(self):
        for mode in (20,21,22,23,24,25,26,27,28,32,35,36):
            with self.subTest(mode=mode):
                _,rows=self.core(mode)
                self.assertFalse(rows[-1]['ok'])
                rejected=[r for r in rows if r['type']=='image-rejected']
                self.assertEqual(len(rejected),1)
                self.assertEqual(rejected[0]['identityIndex'],0)
                self.assertTrue(rejected[0]['path'])
                self.assertEqual(len(rejected[0]['uuid']),32)
                changes=[r for r in rows if r['type']=='image' and r['identityIndex']==0]
                self.assertEqual(len(changes),1 if mode==22 else 0)
                if mode in (20,27):
                    self.assertEqual(rows[0]['rootImagePolicy'],
                                     {'kind':'fixed','parentInitial':None,'parentRecheck':None})
                if mode in (28,35,36):
                    self.assertEqual(rows[-1]['reason'],'root-parent-changed')
                    self.assertTrue(any(r['type']=='reparent' and r['otherPid']==1 for r in rows))
        for mode in (29,30,31):
            _,rows=self.core(mode)
            self.assertFalse(rows[-1]['ok'])
            self.assertEqual(rows[-1]['reason'],'root-runtime-parent-read')
            self.assertFalse(any(r['type']=='identity' for r in rows))
        _,rows=self.core(34)
        self.assertTrue(rows[-1]['ok'])
        self.assertEqual(rows[0]['rootImagePolicy'],
                         {'kind':'fixed','parentInitial':None,'parentRecheck':None})

    def test_api_permission_caps_and_original_phase_budget_fail_closed(self):
        _, normalized=self.core(17)
        self.assertEqual(normalized[0]['empty'],0)
        self.assertLess(normalized[0]['zeroWithPermission'],0)
        self.assertLess(normalized[0]['negativeWithIO'],0)
        self.assertEqual(normalized[0]['threePids'],3)
        for mode in (7, 8, 9, 10, 13):
            with self.subTest(mode=mode):
                _, rows = self.core(mode)
                self.assertFalse(rows[-1]['ok'])
        for mode, reason in [(14, 'record-cap'), (15, 'owned-cap')]:
            _, rows = self.core(mode)
            self.assertFalse(rows[0]['ok'])
            self.assertEqual(rows[0]['reason'], reason)

    def test_self_cpu_limit_and_lag_are_not_native_success(self):
        _, boundary = self.core(16)
        self.assertEqual(boundary[0], {'exactBoundary':True,'oneMicrosecondOver':False})
        _, rows = self.core(11)
        eof = rows[-1]
        self.assertFalse(eof['ok'])
        self.assertEqual(eof['reason'], 'self-cpu-budget')
        self.assertFalse(eof['withinSelfCpuLimit'])
        _, lagged = self.core(12)
        self.assertTrue(lagged[-1]['ok'])
        self.assertGreater(lagged[-1]['missedIntervals'], 0)


class FakeProcess:
    def __init__(self, pid=7331):
        self.pid, self.returncode = pid, None
        self.killed = self.terminated = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired('fixture', timeout)
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9

    def terminate(self):
        self.terminated = True
        self.returncode = -15


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mouse-host-launch-')
        self.directory = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'RUNNER_TEMP': str(self.directory)})
        self.env.start()
        self.executable = self.directory / 'Mouse Browser'
        self.sampler = self.directory / 'sampler'
        self.sampler.write_bytes(b'fixture-only')

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def make(self, popen):
        return M.ObservingLaunches(self.executable, self.directory, self.sampler, 'a'*40, popen=popen)

    def test_real_popen_object_args_env_return_without_controller_wait(self):
        entered, release = threading.Event(), threading.Event()
        original = FakeProcess()
        calls = []
        def popen(args, *positional, **kwargs):
            calls.append((args, positional, kwargs))
            return original
        launches = self.make(popen)
        def blocked(*_):
            entered.set()
            release.wait(1)
        launches._observe = blocked
        argv = [sys.executable, str(self.directory/'mouse-637-baseline-performance.py'), '--output', str(self.directory)]
        env = {'CI':'true', 'UNCHANGED':'actual'}
        try:
            with (self.directory/'mouse-637-baseline-performance.log').open('w') as log:
                start = time.monotonic()
                result = launches(argv, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
                self.assertIs(result, original)
                self.assertLess(time.monotonic()-start, .2)
                self.assertTrue(entered.wait(.5))
                self.assertIs(calls[0][0], argv)
                self.assertIs(calls[0][2]['env'], env)
                self.assertIs(calls[0][2]['stdout'], log)
                self.assertFalse(original.killed or original.terminated)
        finally:
            release.set()
            launches.finish(failed=True)

    def test_unrelated_launch_passthrough_and_exact_phase_scope(self):
        sentinel = object(); calls=[]
        launches = self.make(lambda *a, **k: (calls.append((a,k)),sentinel)[1])
        self.assertIs(launches(['node','controller.cjs'],env={'A':'B'}),sentinel)
        self.assertIs(launches(['git','show','HEAD:tools/mouse-637-baseline-performance.py']),sentinel)
        self.assertIs(launches(['python','hash.py','mouse-637-baseline-performance.py']),sentinel)
        with self.assertRaisesRegex(ValueError,'Unexpected original'):
            launches([str(self.executable),'--mouse-631-smoke','extra'])
        with (self.directory/'mouse-631-native.log').open('w') as log:
            with self.assertRaisesRegex(ValueError,'phase order'):
                launches([str(self.executable),'--mouse-631-smoke'],env={'CI':'true'},stdout=log)
        self.assertEqual(len(calls),3)

    def test_unchanged_existing_wrapper_chain_preserves_both_phase_launches(self):
        calls=[]
        def actual(args,*a,**k):
            p=FakeProcess(7000+len(calls));calls.append((args,k,p));return p
        observer=self.make(actual);observer._observe=lambda *_:None
        guest=runpy.run_path(str(TOOLS/'mouse637-guest-input-observer.py'))
        feature=runpy.run_path(str(TOOLS/'mouse637-feature-readiness.py'))
        retained=guest['RetainedLaunch'](self.executable,self.directory,self.directory/'retained',
                                        self.directory/'retained.cjs','a'*40,popen=observer)
        outer=feature['FeatureLaunches'](self.executable,self.directory,self.directory/'features',
                                         self.directory/'features.cjs',popen=retained)
        baseline=[sys.executable,str(self.directory/'mouse-637-baseline-performance.py'),'--output',str(self.directory)]
        candidate=[str(self.executable),'--mouse-631-smoke']
        with (self.directory/'mouse-637-baseline-performance.log').open('w') as a, (self.directory/'mouse-631-native.log').open('w') as b:
            one=outer(baseline,env={'CI':'true'},stdout=a)
            two=outer(candidate,env={'CI':'true','MOUSE_TEST_PROFILE':str(observer.profile)},stdout=b)
        observer.finish(failed=True)
        self.assertIs(one,calls[0][2]);self.assertIs(two,calls[1][2])
        self.assertEqual([c[0] for c in calls],[baseline,candidate])
        self.assertEqual([r['phase'] for r in observer.records],['baseline','candidate'])
        self.assertEqual(retained.records,[]);self.assertEqual(outer.records,[])

    def test_observer_failure_never_kills_original_process(self):
        original = FakeProcess()
        launches = self.make(lambda *a,**k: (_ for _ in ()).throw(OSError('helper spawn failed')))
        row={'phase':'candidate','pid':original.pid,'parentPid':os.getpid(),'uid':os.geteuid(),
             'nonce':'b'*64,'budgetMs':400000,'expectedRootPath':str(self.executable),
             'launchBeforeEpochUs':1,'launchAfterEpochUs':2}
        launches._observe(original,row,time.monotonic_ns())
        self.assertIn('helper spawn failed',row['observerError'])
        self.assertFalse(original.killed or original.terminated)
        self.assertIn('config',row)

    def test_original_exception_identity_survives_summary_failure(self):
        original = subprocess.TimeoutExpired(['native'],400)
        with patch.object(M,'write_new',side_effect=OSError('disk failure')):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertIs(M.save_summary(self.directory/'summary.json',{},original),original)
                self.assertIsInstance(M.save_summary(self.directory/'summary.json',{},None),OSError)

    def test_owned_cleanup_races_are_recorded_without_touching_native(self):
        launches = self.make(lambda *a,**k:None)
        original = FakeProcess(7331)
        helper = FakeProcess(8442)
        def exited_while_terminating():
            helper.returncode=0
            raise ProcessLookupError('exited during terminate')
        helper.terminate=exited_while_terminating
        row={}
        launches._stop_helper(helper,row)
        self.assertEqual(row['helperExitCode'],0)
        self.assertIn('ProcessLookupError',row['helperCleanupErrors'][0])
        self.assertFalse(original.killed or original.terminated)
        broken=FakeProcess(8443)
        broken.terminate=lambda:None
        broken.kill=lambda:(_ for _ in ()).throw(OSError('owned kill failed'))
        second={}
        launches._stop_helper(broken,second)
        self.assertTrue(any('owned kill failed' in x for x in second['helperCleanupErrors']))
        self.assertTrue(any('did not observe exit' in x for x in second['helperCleanupErrors']))

    def test_final_original_exit_uses_actual_popen_after_concurrent_poll(self):
        launches=self.make(lambda *a,**k:None)
        one,two=FakeProcess(11),FakeProcess(12)
        one.returncode=two.returncode=0
        one.poll=two.poll=lambda:None
        launches.processes=[one,two]
        launches.records=[{'phase':phase,'completed':True,'helperExitCode':0,
                           'originalExitCodeAtSamplerExit':None} for phase in ('baseline','candidate')]
        launches.finish()
        self.assertEqual([r['originalExitCodeObserved'] for r in launches.records],[0,0])
        self.assertTrue(all(r['originalExitCodeAtSamplerExit'] is None for r in launches.records))

    def test_original_run_logged_clock_runs_while_async_observer_is_blocked(self):
        source = (TOOLS/'fixtures/mouse637-readiness-002-verifier.py').read_text()
        tree = ast.parse(source)
        funcs = [x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('run_logged','sample_native_exit')]
        self.assertEqual(len(funcs),2)
        namespace={'subprocess':subprocess,'time':time,'sys':sys}
        exec(compile(ast.Module(body=funcs,type_ignores=[]),'actual-original-run-logged','exec'),namespace)
        entered,release=threading.Event(),threading.Event()
        child=FakeProcess()
        launches=self.make(lambda *a,**k: child)
        launches._observe=lambda *_:(entered.set(),release.wait(1))
        argv=[sys.executable,str(self.directory/'mouse-637-baseline-performance.py'),'--output',str(self.directory)]
        try:
            with patch.object(subprocess,'Popen',launches):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        namespace['run_logged'](argv,{'CI':'true'},self.directory/'mouse-637-baseline-performance.log',.08)
            self.assertTrue(entered.is_set())
            self.assertTrue(child.killed)  # only original run_logged's own timeout
            self.assertFalse(child.terminated)
        finally:
            release.set();launches.finish(failed=True)


def native_contract(sampler):
    """Actual Mac API checks on an owned synthetic Python child, never Mouse."""
    if sys.platform != 'darwin':
        raise RuntimeError('The explicit native contract requires Mac')
    sampler=Path(sampler).resolve(strict=True)
    prefix='mouse-637-host-observer-native-contract'
    receipt=sampler.parent/(prefix+'.json')
    kept_raw=sampler.parent/(prefix+'.jsonl')
    kept_child=sampler.parent/(prefix+'-child.py')
    if receipt.exists():
        raise RuntimeError('Native contract receipt must be fresh')
    facts={'schema':1,'kind':'mouse637-host-observer-native-contract','ok':False,
           'assertionsPassed':False,'productLaunched':False,'platform':sys.platform,
           'parentPid':os.getpid(),'uid':os.geteuid(),'sampler':str(sampler),
           'samplerBinding':M.binding(sampler),'startedAtEpochUs':time.time_ns()//1000,
           'child':{'pid':None,'argv':None,'exitCode':None},
           'helper':{'pid':None,'argv':None,'exitCode':None},'cleanupErrors':[],'evidenceErrors':[]}
    error=None
    temporary=child=helper=raw=None
    captured={}
    def preserve_error(cause, field):
        nonlocal error
        facts[field].append(type(cause).__name__+': '+str(cause))
        if error is None:
            error=cause
    def stream_bytes(value):
        data=value.encode() if isinstance(value,str) else value or b''
        if len(data)>1048576:
            raise RuntimeError('Native fixture output exceeded one MiB')
        return {'encoding':'base64','data':base64.b64encode(data).decode('ascii'),
                'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    try:
        if kept_raw.exists() or kept_child.exists():
            raise RuntimeError('Native contract evidence must be fresh')
        temporary=tempfile.TemporaryDirectory(prefix='mouse-host-native-')
        root=Path(temporary.name)/'Установка sampler with spaces';root.mkdir()
        child_file=root/'owned child.py'
        source=('import subprocess,sys,time\n'
                'p=subprocess.Popen([sys.executable,"-c","import time; end=time.monotonic()+2; exec(\\\"while time.monotonic()<end: sum(range(1000))\\\")"])\n'
                'p.wait(timeout=4)\ntime.sleep(.4)\n').encode('utf-8')
        with kept_child.open('xb') as stream:stream.write(source)
        child_file.write_bytes(source)
        facts['fixture']={'filename':kept_child.name,'executedPath':str(child_file),**M.binding(kept_child)}
        facts['fixture']['executedBindingBeforeLaunch']=M.binding(child_file)
        if facts['fixture']['executedBindingBeforeLaunch'] != M.binding(kept_child):
            raise RuntimeError('Preserved child fixture differs from executed bytes')
        facts['child']['argv']=[sys.executable,str(child_file)]
        before=time.time_ns()//1000
        child=subprocess.Popen(facts['child']['argv'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        after=time.time_ns()//1000
        facts['child'].update(pid=child.pid,launchBeforeEpochUs=before,launchAfterEpochUs=after)
        raw=root/'native.jsonl'
        command=[str(sampler),'fixture',str(child.pid),str(os.getpid()),str(Path(sys.executable).resolve()),
                 str(before),str(after),'8000','c'*64,str(raw),str(os.geteuid())]
        facts['helper']['argv']=command
        helper=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        facts['helper']['pid']=helper.pid
        out,err=helper.communicate(timeout=10)
        captured['helper']=(out,err)
        if helper.returncode:
            raise RuntimeError(f'Owned helper fixture failed: helper={helper.returncode} {err!r}')
        child_out,child_err=child.communicate(timeout=2)
        captured['child']=(child_out,child_err)
        if child.returncode:
            raise RuntimeError(f'Owned helper fixture failed: helper={helper.returncode} child={child.returncode} {err!r} {child_err!r}')
        rows=[json.loads(line) for line in raw.read_text().splitlines()]
        identities=[r for r in rows if r['type']=='identity']
        if not (rows[-1]['ok'] is True and rows[-1]['rootGone'] is True and len(identities)>=2 and
                identities[0]['pid']==child.pid and identities[0]['parentIndex']==-1 and
                all(r['uid']==os.geteuid() for r in identities) and rows[-1]['withinSelfCpuLimit'] is True):
            raise RuntimeError('Owned Mac API/ancestry/counter/overhead contract failed')
        descendant_cpu=[]
        for identity in identities[1:]:
            samples=[r for r in rows if r['type']=='sample' and r['identityIndex']==identity['identityIndex']]
            if len(samples)>=2:
                descendant_cpu.append(samples[-1]['userTime']+samples[-1]['systemTime']-
                                      samples[0]['userTime']-samples[0]['systemTime'])
        if not any(delta>0 for delta in descendant_cpu):
            raise RuntimeError('Owned busy child cumulative CPU did not actually increase')
        facts.update(assertionsPassed=True,ownedCount=len(identities),descendantCpuDeltas=descendant_cpu,eof=rows[-1])
    except BaseException as cause:
        error=cause
        facts['error']=type(cause).__name__+': '+str(cause)
    finally:
        for name,process in [('helper',helper),('child',child)]:
            if process is None:continue
            try:
                if process.poll() is None:
                    process.kill();process.wait(timeout=2)
            except BaseException as cause:
                preserve_error(cause,'cleanupErrors')
            if name not in captured:
                try:
                    captured[name]=process.communicate(timeout=2)
                except subprocess.TimeoutExpired as cause:
                    captured[name]=(cause.output or b'',cause.stderr or b'')
                    facts[name]['outputIncomplete']=True
                    preserve_error(cause,'cleanupErrors')
                except BaseException as cause:
                    preserve_error(cause,'cleanupErrors')
            facts[name]['exitCode']=process.returncode
            if name in captured:
                try:
                    facts[name]['stdout']=stream_bytes(captured[name][0])
                    facts[name]['stderr']=stream_bytes(captured[name][1])
                except BaseException as cause:
                    preserve_error(cause,'evidenceErrors')
        try:
            if raw is not None and raw.exists():
                if not raw.is_file() or raw.is_symlink() or raw.stat().st_size>M.MAX_RAW_BYTES:
                    raise RuntimeError('Native contract raw output is unsafe or oversized')
                with kept_raw.open('xb') as stream:stream.write(raw.read_bytes())
                facts['raw']={'filename':kept_raw.name,**M.binding(kept_raw)}
        except BaseException as cause:
            preserve_error(cause,'evidenceErrors')
        if temporary is not None:
            try:temporary.cleanup()
            except BaseException as cause:preserve_error(cause,'cleanupErrors')
        facts['ok']=facts['assertionsPassed'] is True and error is None
        facts['finishedAtEpochUs']=time.time_ns()//1000
        try:M.write_new(receipt,facts)
        except BaseException as cause:
            if error is None:error=cause
            print('MOUSE_637_HOST_NATIVE_CONTRACT_SAVE_FAILED '+type(cause).__name__,file=sys.stderr,flush=True)
    if error is not None:raise error
    print(json.dumps({'marker':'MOUSE_637_HOST_OBSERVER_NATIVE_CONTRACT_PASS','rootPid':child.pid,
                      'helperPid':helper.pid,'ownedCount':facts['ownedCount'],'eof':facts['eof'],
                      'receipt':{'filename':receipt.name,**M.binding(receipt)}},sort_keys=True))


class NativeContractTests(unittest.TestCase):
    def test_helper_failure_precedes_child_wait_and_preserves_partial_raw(self):
        events=[]
        class FixtureProcess(FakeProcess):
            def __init__(self,pid,name,exit_code=None):
                super().__init__(pid);self.name=name;self.returncode=exit_code
            def communicate(self,timeout=None):
                events.append((self.name,'communicate',timeout))
                if self.returncode is None:
                    raise subprocess.TimeoutExpired(self.name,timeout)
                return b'',b'actual helper failure' if self.name=='helper' else b''
            def kill(self):
                events.append((self.name,'kill'))
                super().kill()
        child=FixtureProcess(8001,'child')
        helper=FixtureProcess(8002,'helper',1)
        with tempfile.TemporaryDirectory(prefix='mouse-host-contract-failure-') as directory:
            sampler=Path(directory)/'sampler';sampler.write_bytes(b'only a synthetic helper path')
            def launch(argv,**_):
                if argv[0]==str(sampler):
                    Path(argv[-2]).write_bytes(b'{"type":"partial","ok":false}\n')
                    return helper
                return child
            with patch.object(sys,'platform','darwin'),patch.object(subprocess,'Popen',launch):
                with self.assertRaisesRegex(RuntimeError,'Owned helper fixture failed: helper=1'):
                    native_contract(sampler)
            self.assertEqual(events,[('helper','communicate',10),('child','kill'),('child','communicate',2)])
            receipt=json.loads((sampler.parent/'mouse-637-host-observer-native-contract.json').read_text())
            self.assertFalse(receipt['ok'])
            self.assertFalse(receipt['assertionsPassed'])
            self.assertEqual(receipt['helper']['exitCode'],1)
            self.assertEqual(receipt['child']['exitCode'],-9)
            self.assertIn('helper=1',receipt['error'])
            raw=sampler.parent/receipt['raw']['filename']
            self.assertEqual(raw.read_bytes(),b'{"type":"partial","ok":false}\n')
            self.assertEqual(M.binding(raw),{k:receipt['raw'][k] for k in ('size','sha256')})
            self.assertEqual(base64.b64decode(receipt['helper']['stderr']['data']),b'actual helper failure')


if __name__=='__main__':
    if '--native-sampler' in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--native-sampler',required=True)
        native_contract(parser.parse_args().native_sampler)
    else:
        unittest.main()
