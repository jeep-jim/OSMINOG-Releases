#!/usr/bin/env python3
import hashlib,json,os,pathlib,subprocess,sys,time
exe=pathlib.Path(sys.argv[1]).resolve()
if not exe.is_file():raise SystemExit('Packaged Mouse executable missing')
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'mouse-profiles';root.mkdir(exist_ok=True)
def sample_native_exit(process,log_path,deadline):
 # Sample only this verifier's still-running child. Each command is bounded
 # inside the existing deadline; failures are diagnostic and cannot pass a gate.
 if sys.platform!='darwin':return
 state_path=log_path.with_name(log_path.stem+'-process.log')
 sample_path=log_path.with_name(log_path.stem+'-sample.log')
 # The previous 4 s command cap killed sample while it symbolicated its already
 # collected stacks. Keep the same 30 s process deadline, but let that report
 # finish within it so another native teardown failure has usable evidence.
 commands=[(['/bin/ps','-p',str(process.pid),'-o','pid,ppid,state,etime,command'],2),(['/usr/bin/sample',str(process.pid),'2','1','-file',str(sample_path)],12)]
 try:
  with state_path.open('w') as state:
   for command,limit in commands:
    remaining=deadline-time.monotonic()
    if remaining<=0 or process.poll() is not None:break
    print('COMMAND',command,flush=True,file=state)
    try:
     result=subprocess.run(command,stdout=state,stderr=subprocess.STDOUT,timeout=min(limit,remaining),check=False)
     print('DIAGNOSTIC_RETURN',result.returncode,flush=True,file=state)
    except (OSError,subprocess.TimeoutExpired) as error:print(type(error).__name__,str(error),flush=True,file=state)
 except OSError:return
def run_logged(args,env,log_path,timeout,*,completion_timeout=30,sample_after=5):
 # Keep failure output even when a native process times out. A regular file
 # also avoids waiting for inherited stdout pipes after the main app exits.
 with log_path.open('w') as log:
  process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,text=True)
  started=time.monotonic();deadline=started+timeout;exit_requested=None;sampled=False;tail=''
  try:
   with log_path.open(errors='replace') as observed:
    while process.poll() is None:
     chunk=observed.read();scan=tail+chunk;tail=scan[-64:]
     if exit_requested is None and 'MOUSE_SMOKE_EXIT_REQUESTED ' in scan:
      exit_requested=time.monotonic();deadline=min(deadline,exit_requested+completion_timeout)
     if exit_requested is not None and not sampled and time.monotonic()-exit_requested>=sample_after:
      sampled=True;sample_native_exit(process,log_path,deadline)
     if process.poll() is not None:break
     remaining=deadline-time.monotonic()
     if remaining<=0:
      print(f'MOUSE_NATIVE_PROCESS_TIMEOUT pid={process.pid} exitRequested={exit_requested is not None} elapsedMs={round((time.monotonic()-started)*1000)}',file=log,flush=True)
      process.kill();process.wait()
      if exit_requested is not None and time.monotonic()-exit_requested>=completion_timeout:raise RuntimeError(f'Native smoke did not exit within {completion_timeout:g} seconds after its exit request (pid {process.pid})')
      raise subprocess.TimeoutExpired(args,timeout)
     time.sleep(min(.1,remaining))
   result=subprocess.CompletedProcess(args,process.returncode)
   result.pid=process.pid;result.elapsedMs=round((time.monotonic()-started)*1000)
   print(f'MOUSE_NATIVE_PROCESS_RETURN pid={process.pid} code={process.returncode} elapsedMs={round((time.monotonic()-started)*1000)}',file=log,flush=True)
  finally:
   if process.poll() is None:process.kill();process.wait()
   log.flush();output=log_path.read_text(errors='replace');print(output,flush=True)
 return result,output
baseline_env={**os.environ,'CI':'true'}
baseline,baseline_output=run_logged([sys.executable,str(pathlib.Path(__file__).with_name('mouse-637-baseline-performance.py')),'--output',str(pathlib.Path.cwd())],baseline_env,pathlib.Path('mouse-637-baseline-performance.log'),900)
if baseline.returncode or 'MOUSE_637_BASELINE_PERFORMANCE_PASS' not in baseline_output.splitlines():raise SystemExit('Published predecessor native performance baseline failed')
retained636_env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'retained636')}
retained636,retained636_output=run_logged([str(exe),'--mouse-636-retained-smoke'],retained636_env,pathlib.Path('mouse-636-retained-owner-feedback.log'),270)
if retained636.returncode or 'MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS' not in retained636_output.splitlines():raise SystemExit('Mouse636 retained pane downloads, AI preview and capture verification failed')
owner_env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'owner633')}
owner,owner_output=run_logged([str(exe),'--mouse-633-smoke'],owner_env,pathlib.Path('mouse-633-owner-feedback.log'),270)
if owner.returncode or 'MOUSE_633_OWNER_FEEDBACK_PASS' not in owner_output.splitlines():raise SystemExit('Mouse633 owner feedback native verification failed')
# New owner regressions use their own profile and bounded process, not the
# persistent profile or timing budget of the retained suites below.
regression_env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'task-stress-631')}
regression,regression_output=run_logged([str(exe),'--mouse-631-smoke'],regression_env,pathlib.Path('mouse-631-native.log'),400)
required631=['MOUSE_631_TASK_ONLY_NATIVE_PASS','MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS','MOUSE_631_INSTALLED_TASK_STRESS_PASS','MOUSE_632_STATIONARY_MEDIA_PASS']
if regression.returncode or not all(marker in regression_output.splitlines() for marker in required631):raise SystemExit('Mouse631 task/stress native verification failed')
subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('mouse-631-acceptance.py')),'--directory','.', '--platform','darwin','--arch','arm64'],check=True)
owner636_env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'owner636')}
owner636,owner636_output=run_logged([str(exe),'--mouse-637-smoke'],owner636_env,pathlib.Path('mouse-636-owner-feedback.log'),270)
required636=['MOUSE_635_LIBRARY_STABLE_PASS', 'MOUSE_637_AGENT_REMOVAL_PASS', 'MOUSE_636_PINNED_PANES_PASS', 'MOUSE_636_SEARCH_REMOVAL_PASS', 'MOUSE_637_PERFORMANCE_PASS', 'MOUSE_636_OWNER_FEEDBACK_PASS']
if owner636.returncode or not all(marker in owner636_output.splitlines() for marker in required636):raise SystemExit('Mouse636 removed search, removed Agent, live performance, pinned panes or stable library verification failed')
features_env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'features637')}
feature_processes={}
for phase,flag,marker,budget in [('write','--mouse-637-features-smoke','MOUSE_637_FEATURES_WRITE_PASS',270),('read','--mouse-637-features-restore-read','MOUSE_637_FEATURES_NATIVE_PASS',120)]:
 log_path=pathlib.Path('mouse-637-features-'+phase+'.log')
 result,output=run_logged([str(exe),flag],features_env,log_path,budget)
 if result.returncode or marker not in output.splitlines():raise SystemExit('Mouse637 native features '+phase+' failed')
 feature_processes[phase]={'pid':result.pid,'exitCode':result.returncode,'elapsedMs':result.elapsedMs,'log':log_path.name,'logSha256':hashlib.sha256(log_path.read_bytes()).hexdigest(),'requiredMarkers':[marker]}
 receipt=pathlib.Path('mouse-637-features.json')
 if phase=='write':
  retained=pathlib.Path('mouse-637-features-write.json');retained.write_bytes(receipt.read_bytes());receipt=retained
 feature_processes[phase].update(report=receipt.name,reportSha256=hashlib.sha256(receipt.read_bytes()).hexdigest())
feature_file=pathlib.Path('mouse-637-features.json');features=json.loads(feature_file.read_text(encoding='utf-8'))
if not (features.get('ok') is True and features.get('restored') is True and features.get('version')=='6.0.37' and features.get('pid')==feature_processes['write']['pid'] and features.get('restart',{}).get('pid')==feature_processes['read']['pid'] and features['pid']!=features['restart']['pid']):raise SystemExit('Mouse637 feature restoration did not use two actual processes')
feature_processes['reportSha256']=hashlib.sha256(feature_file.read_bytes()).hexdigest()
pathlib.Path('mouse-637-features-processes.json').write_text(json.dumps(feature_processes,indent=2)+'\n',encoding='utf-8')
for mode,markers in [('--mouse-smoke-write',['MOUSE_REAL_HORIZONTAL_VERTICAL_DRAG_PASS','MOUSE_629_UI_REGRESSIONS_NATIVE_PASS','MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_WRITE_PASS','MOUSE_630_DOWNLOAD_ACTIVITY_PASS','MOUSE_630_CAPTURE_FEEDBACK_PASS','MOUSE_630_NORA_NATIVE_FOREGROUND_PASS','MOUSE_630_NATIVE_WHEEL_DESKTOPS_PASS','MOUSE_630_PAGE_SCROLL_PRESERVED_PASS']),('--mouse-smoke-read',['MOUSE_PROFILE_COOKIE_RESTART_PASS','MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_NATIVE_PASS'])]:
 env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'persistent')}
 # The accepted 6.0.28 write suite took 413850 ms. Three new native suites
 # add download/capture, foreground and wheel interactions; retain all existing
 # per-scenario/frame/exit limits and bound the expanded whole write process.
 result,output=run_logged([str(exe),mode,'--mouse-init-race'],env,pathlib.Path(mode.lstrip('-')+'.log'),600 if mode=='--mouse-smoke-write' else 480)
 if result.returncode or not all(marker in output for marker in markers) or 'MOUSE_ARM64_SMOKE_PASS' not in output:raise SystemExit('Packaged verification failed: '+mode)
env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(root/'ordinary')}
with open('mouse-normal-launch.log','w') as log:
 p=subprocess.Popen([str(exe)],env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  for _ in range(300):
   if p.poll() is not None:raise RuntimeError('Ordinary launch exited')
   f=root/'ordinary'/'mouse-startup.log'
   if f.exists() and 'MOUSE_READY 6.0.37' in f.read_text():break
   time.sleep(.1)
  else:raise RuntimeError('Ordinary launch timed out')
  time.sleep(2)
  if p.poll() is not None:raise RuntimeError('Ordinary app terminated')
  print('MOUSE_NORMAL_LAUNCH_PASS',flush=True)
 finally:
  p.terminate()
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.kill();p.wait()
import json
for mode in ['normal','fullscreen','quit','fullscreen-quit']:
 profile=root/('close-'+mode)
 env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(profile)}
 r=subprocess.run([str(exe),'--mouse-close-test='+mode],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
 pathlib.Path('mouse-close-'+mode+'.log').write_text(r.stdout);print(r.stdout,flush=True)
 required=['MOUSE_CLOSE_TEST_READY '+mode,'MOUSE_EXIT_SAVED','MOUSE_WINDOW_CLOSED','MOUSE_APP_QUIT']
 if mode.startswith('fullscreen'):required+=['MOUSE_NATIVE_FULLSCREEN_ENTERED','MOUSE_LEFT_FULLSCREEN']
 if r.returncode or not all(s in r.stdout for s in required) or 'MOUSE_UNEXPECTED_HIDE' in r.stdout or 'MOUSE_FULLSCREEN_EXIT_WARNING' in r.stdout:raise SystemExit('Actual close lifecycle failed: '+mode)
 saved=json.loads((profile/'workspace.json').read_text())['quadroPreferences']
 if saved['aiWidth']!=419 or saved['theme']!='light':raise SystemExit('Last preference not flushed on close')
 print('MOUSE_CLOSE_'+mode.upper().replace('-','_')+'_PASS',flush=True)
for mode,marker in [('--mouse-private-smoke','MOUSE_PRIVATE_MEMORY_ISOLATION_CLEANUP_NORMAL_UNCHANGED_PASS'),('--mouse-private-close','MOUSE_APP_QUIT')]:
 profile=root/('private-'+mode.lstrip('-'))
 env={**os.environ,'CI':'true','MOUSE_TEST_PROFILE':str(profile)}
 r,output=run_logged([str(exe),mode],env,pathlib.Path('mouse-'+mode.lstrip('-')+'.log'),120)
 if r.returncode or marker not in output:raise SystemExit('Private session verification failed: '+mode)
 if 'PRIVATE_SENTINEL_606_6f532' in (profile/'workspace.json').read_text():raise SystemExit('Private data leaked to profile')
 print('MOUSE_PRIVATE_PROCESS_EXIT_DISK_SCAN_PASS '+mode,flush=True)
# Actual older app replacement, verified new startup and a preserved runner profile.
candidates=[pathlib.Path('dist-mouse/Mouse-Browser-6.0.37-mac-arm64.dmg'),pathlib.Path('Mouse-Browser-6.0.37-mac-arm64.dmg')]
dmg=next((p.resolve() for p in candidates if p.is_file()),None)
installer=pathlib.Path('mouse-install-update.cjs').resolve()
if not dmg or not installer.is_file():raise SystemExit('Native updater test inputs missing')
button,button_output=run_logged([sys.executable,str(pathlib.Path(__file__).with_name('mouse-637-update-button.py')),str(dmg)],baseline_env,pathlib.Path('mouse-637-update-button.log'),720)
if button.returncode or 'MOUSE_637_REAL_636_TO_637_UPDATE_BUTTON_PASS' not in button_output.splitlines():raise SystemExit('Actual published636 update buttons did not preserve the profile')
subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('mouse-update-verify.py')),str(dmg),str(installer)],check=True,timeout=360)

# Also preserve the actual current published636 profile with a narrow old/new
# package probe; the full native629 updater gate above remains mandatory.
upgrade_log=pathlib.Path('mouse-637-upgrade.log')
with upgrade_log.open('w') as stream:
 upgrade=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('mouse-637-upgrade.py')),str(dmg)],stdout=stream,stderr=subprocess.STDOUT,text=True,timeout=480)
upgrade_output=upgrade_log.read_text(errors='replace');print(upgrade_output,flush=True)
if upgrade.returncode or 'MOUSE_637_REAL_636_TO_637_PROFILE_PASS' not in upgrade_output.splitlines():raise SystemExit('Real published636 profile upgrade failed')
