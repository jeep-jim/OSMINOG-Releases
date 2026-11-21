#!/usr/bin/env python3
"""Synthetic parser adversaries only; no generated PNG is native acceptance.

Reuse the immutable634 synthetic scene generator, then explicitly replace only
635 contract fields. Retained native, wheel, pixels and restoration tests remain.
"""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest

S=runpy.run_path(str(Path(__file__).with_name('mouse635-search-evidence.py')))
OLD=runpy.run_path(str(Path(__file__).with_name('test_mouse634_search_evidence.py')))
png,PALETTE=OLD['png'],OLD['PALETTE']
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def fixture(platform='win32',owners=None,original_native=None):
 old_files,old_facts,_=OLD['fixture'](platform,owners,original_native)
 def text(value):return value.replace('mouse-634-search','mouse-635-search').replace('MOUSE_634_SEARCH_NATIVE_PASS','MOUSE_635_SEARCH_NATIVE_PASS').replace('mouse634','mouse635').replace('6.0.34','6.0.35')
 def convert(value):
  if isinstance(value,str):return text(value)
  if isinstance(value,list):return [convert(v) for v in value]
  if isinstance(value,dict):return {k:(16 if k=='radius' and v==12 else v+4 if k=='revision' and type(v) is int else convert(v)) for k,v in value.items()}
  return value
 files={text(name):(text(raw.decode()).encode() if name.endswith('.json') or name.endswith('.log') else raw) for name,raw in old_files.items()};facts=convert(old_facts)
 def design(ui):
  bg='rgb(25, 33, 46)' if ui['theme']=='dark' else 'rgb(240, 240, 240)';font=lambda size:{'fontSize':size,'textTransform':'none'}
  ui.pop('trackpad',None);ui['design']={'grid':{'display':'grid','columnGap':'12px','rowGap':'0px'},'bodyBackground':bg,'resultsBackground':bg,'assistantBackground':bg,'accent':'#b99aee' if ui['theme']=='dark' else '#7540c8','action':'rgb(133, 84, 210)' if ui['theme']=='dark' else 'rgb(117, 64, 200)','heading':font(20),'query':font(14),'labels':[font(13) for _ in range(6)],'visionControls':0,'screenText':False,'cards':[{'id':c['id'],'position':'relative','gridColumn':'1','gridRowStart':'1','gridRowEnd':'3','radius':'16px','slotRadius':'16px','background':bg,'title':font(13),'domain':font(12)} for c in ui['cards']]};ui['request']={'state':'results','errorVisible':False};return ui
 def decorate(value):
  if isinstance(value,list):
   for v in value:decorate(v)
  elif isinstance(value,dict):
   if all(k in value for k in ('theme','cards','footerButtons','viewport')):design(value)
   for v in list(value.values()):decorate(v)
 decorate(facts)
 facts['stages']=[{'name':name,'elapsedMs':(i+1)*900} for i,name in enumerate(S['STAGES'])]
 facts['inputs']=[row for row in facts['inputs'] if row['selector']!='.mouse-search-vision-toggle']
 for selector in ('#mouse-search-button','.mouse-search-error button','.mouse-search-error button','.mouse-search-back'):
  event=copy.deepcopy(next(row for row in facts['inputs'] if row['selector']=='#mouse-search-button'));event['selector']=selector;facts['inputs'].append(event)
 for number,model in enumerate(facts['models']):
  prompt=model['payload']['messages'][-1]['content'].split('\nТЕКУЩАЯ СТРУКТУРА СТРАНИЦЫ')[0].replace('Describe only the explicitly shared selected page','Compare the selected site using only search metadata');model['payload']['messages'][-1]['content']=prompt
 facts['answers']=convert(facts['answers'])
 for answer in facts['answers']:
  answer['message']=answer['message'].replace('Describe only the explicitly shared selected page','Compare the selected site using only search metadata')
  for turn in answer['messages']:turn['text']=turn['text'].replace('Describe only the explicitly shared selected page','Compare the selected site using only search metadata')
 def stopped(revision):return {'active':False,'phase':'stopped','targetId':'','url':'','title':'','reason':'Screen sharing removed from search','revision':revision,'receivedAt':None,'context':None,'lastAction':None}
 facts['privacy']={'selectedId':facts['initialResults'][0]['id'],'click':copy.deepcopy(next(row for row in facts['inputs'] if row['selector']=='#site-action')),'vision':stopped(facts['visionNative']['revision']),'ui':facts.pop('visionUI'),'native':facts.pop('visionNative'),'actualViews':facts.pop('visionActualViews'),'contentSize':[1000,700],'modelIndex':1,'metadataOnly':True};facts.pop('vision')
 facts['cleared']['before']['vision']=stopped(facts['cleared']['before']['pages']['revision'])
 facts['actions']=[{'action':name,'requestId':None,'revision':None} for name in ('open','query','chat','clear','close','prepare-overlay')];facts['noVisionActions']=True;facts['requestStates']=[]
 def state_image(name):
  shot=copy.deepcopy(facts['nora']['capture']);raw=files[shot['filename']];display=name[:-4]+'-display.png';files[name]=raw;files[display]=raw;shot.update(filename=name,displayFilename=display);return shot
 for number,theme in enumerate(('light','dark')):
  query='mouse635 unavailable '+theme;request=copy.deepcopy(next(row for row in facts['requests'] if row['kind']=='query'));request['form']['q']=query;request['form']['pageno']='1';request.update(controlled=True,responseStatus=503,released=True);retry=copy.deepcopy(request)
  for key in ('controlled','responseStatus','released'):retry.pop(key)
  facts['requests'].extend([request,retry]);retried=copy.deepcopy(facts['initialScene']);retried['ui']['theme']=theme;design(retried['ui']);retried['native']['revision']=2+number*2;proof={'theme':theme,'query':query,'request':copy.deepcopy(request),'retried':retried}
  for phase in ('loading','error'):
   ui=copy.deepcopy(retried['ui']);ui['cards']=[];design(ui);ui['request']={'state':phase,'busy':'true' if phase=='loading' else 'false','progressVisible':phase=='loading','spinnerVisible':phase=='loading','submitDisabled':phase=='loading','submitBusy':'true' if phase=='loading' else 'false','errorVisible':phase=='error','retryVisible':phase=='error','stopVisible':phase=='loading','errorText':'' if phase=='loading' else 'Сервер поиска временно недоступен. Повторите запрос.'};proof[phase]=ui;proof[phase+'Capture']=state_image('mouse-635-search-'+phase+'-'+theme+'.png')
  facts['requestStates'].append(proof)
 def refresh():
  raw=json.dumps({k:v for k,v in facts.items() if k not in ('reportFile','reportSha256')}).encode();files['mouse-635-search.json']=raw;facts['reportSha256']=sha(raw)
 refresh();return files,facts,refresh


class SearchEvidence635(unittest.TestCase):
 def setUp(self):self.files,self.facts,self.refresh=fixture()
 def verify(self):
  self.refresh();return S['verify'](S['N']['Evidence'](self.files.__getitem__),self.facts,self.facts['platform'],self.facts['arch'],self.facts['pid'],self.facts['original']['before']['identities'])
 def reject(self):
  with self.assertRaises((ValueError,KeyError,TypeError)):self.verify()
 def verify_wheel(self):
  item=self.facts['wheelInputs'][0];group=self.facts['captures'][-1]
  return S['wheel_preparation'](item,self.facts['initialResults'][0],group['native']['revision'],group['attempts'][-1]['contentBounds'],item['receipt'])
 def reject_wheel(self):
  with self.assertRaises(ValueError):self.verify_wheel()
 def rewrite_screen(self,group_index,probe_index,rgba):
  shot=self.facts['captures'][group_index]['attempts'][0];points={(p['pixel']['x'],p['pixel']['y']):p['pixel']['rgba'] for p in shot['probes']};probe=shot['probes'][probe_index];probe['pixel']['rgba']=rgba;points[(probe['pixel']['x'],probe['pixel']['y'])]=rgba
  raw=png(shot['pixelSize']['width'],shot['pixelSize']['height'],points);self.files[shot['filename']]=raw;self.files[shot['displayFilename']]=raw;shot.update(sha256=sha(raw),displaySha256=sha(raw),bytes=len(raw));return probe
 def test_three_platform_contracts_accept_only_labelled_synthetic_fixtures(self):
  for platform in ('darwin','win32','linux'):
   self.files,self.facts,self.refresh=fixture(platform);result=self.verify();self.assertEqual(result['decodedProbes'],36);self.assertEqual(result['originalOwnersRestored'],4);self.assertFalse(result['livePublicSearchVerified'])
 def test_raw_nested_report_and_process_binding_are_required(self):
  self.facts['pid']=92
  self.refresh()
  with self.assertRaises(ValueError):S['verify'](S['N']['Evidence'](self.files.__getitem__),self.facts,'win32','x64',91,self.facts['original']['before']['identities'])
  self.setUp();self.refresh();self.facts['ok']=False
  with self.assertRaises(ValueError):S['verify'](S['N']['Evidence'](self.files.__getitem__),self.facts,'win32','x64',91,self.facts['original']['before']['identities'])
 def test_fixtures_cannot_be_counted_as_public_backend_or_model_evidence(self):
  for key in ('livePublicSearchVerified','livePublicModelVerified','physicalUserDeviceVerified'):
   self.setUp();self.facts[key]=True;self.reject()
 def test_wrong_origin_result_and_forged_og_price_are_rejected(self):
  self.facts['initialResults'][0]['url']=self.facts['fixtureOrigins'][1]+'/site/0';self.reject()
  self.setUp();self.facts['filteredResults'][0]['price']='999 RUB';self.reject()
 def test_infinite_pagination_requires_actual_second_http_request_and_unique_append(self):
  self.facts['requests']=[r for r in self.facts['requests'] if r.get('form',{}).get('pageno')!='2'];self.reject()
  self.setUp();self.facts['pagedResults'][-1]=copy.deepcopy(self.facts['pagedResults'][0]);self.reject()
  self.setUp();self.facts['wheel'][0]['revision']+=1;self.reject()
 def test_footer_magnifier_and_left_right_regions_are_measured(self):
  self.facts['captures'][0]['ui']['footerButtons']['immediatelyBefore']=False;self.reject()
  self.setUp();self.facts['captures'][0]['ui']['right']['x']=600;self.reject()
  self.setUp();self.facts['captures'][0]['ui']['footerButtons']['searchStyle']['backgroundColor']='rgb(255, 0, 0)';self.reject()
 def test_cached_view_bounds_cannot_replace_actual_native_view_geometry(self):
  self.facts['captures'][0]['actualViews'][0]['actualBounds']['width']+=1;self.reject()
  self.setUp();self.facts['captures'][0]['actualViews'][0]['attached']=False;self.reject()
 def test_clipping_and_native_view_cap_are_independently_derived(self):
  group=self.facts['captures'][0]
  for state in (group['native'],group['nativeAfter']):
   state['pages'][2]['bounds']['height']+=10;state['pages'][2]['clip']['height']+=10
  for actual in (group['actualViews'],group['actualViewsAfter']):actual[2]['actualBounds']['height']+=10
  self.reject()
  self.setUp();self.facts['captures'][0]['native']['liveCount']=9;self.reject()
  self.setUp();self.facts['captures'][0]['native']['maxLive']=9;self.reject()
 def test_live_site_color_is_recomputed_from_png_even_with_resealed_hashes(self):
  p=self.rewrite_screen(0,0,[255,255,255,255]);p.update(expectedRGB=[255,255,255],delta=0);p['pass']=True;self.reject()
 def test_square_native_corner_cannot_be_claimed_as_rounded(self):
  p=self.rewrite_screen(0,2,PALETTE[0]+[255]);p.update(expectedRGB=PALETTE[0],delta=0);p['pass']=True;self.reject()
 def test_corner_probes_cannot_move_away_from_actual_native_endpoints(self):
  self.facts['captures'][0]['attempts'][0]['probes'][2]['point']['x']+=12;self.reject()
 def test_full_display_crop_and_opaque_pixels_are_required(self):
  p=self.rewrite_screen(0,0,PALETTE[0]+[0]);self.reject()
  self.setUp();shot=self.facts['captures'][0]['attempts'][0];raw=png(1000,700,{});self.files[shot['displayFilename']]=raw;shot['displaySha256']=sha(raw);self.reject()
 def test_capture_cannot_change_native_epoch_or_skip_a_failed_first_frame(self):
  self.facts['captures'][0]['nativeAfter']['pages'][0]['navigationEpoch']+=1;self.reject()
  self.setUp();self.facts['captures'][0]['acceptedAttempt']=2;self.reject()
 def test_trusted_guest_click_remains_bound_without_screen_sharing(self):
  guest=next(r for r in self.facts['inputs'] if r.get('selector')=='#site-action');guest['events'][0]['trusted']=False;self.reject()
  self.setUp();self.facts['privacy']['click']['webContentsId']+=1;self.reject()
  self.setUp();self.facts['privacy']['native']['pages'][0]['webContentsId']+=1;self.reject()
 def test_removed_vision_cannot_return_through_foreign_selection_or_actions(self):
  self.facts['privacy']['ui']['selectedId']=self.facts['initialResults'][1]['id'];self.reject()
  self.setUp();self.facts['privacy']['vision']['active']=True;self.reject()
  self.setUp();self.facts['privacy']['modelIndex']=0;self.reject()
  self.setUp();self.facts['actions'].append({'action':'vision-start','requestId':None,'revision':None});self.reject()
 def test_private_form_values_and_full_page_context_never_enter_the_model(self):
  for secret in ('unshared-password-value','mouse635-typed-secret'):
   self.setUp();self.facts['models'][1]['payload']['messages'][-1]['content']=self.facts['models'][1]['payload']['messages'][-1]['content'].replace('Use only the owned test data.',secret);self.reject()
  self.setUp();self.facts['models'][1]['payload']['messages'][-1]['content']+='\nТЕКУЩАЯ СТРУКТУРА СТРАНИЦЫ (НЕ ИНСТРУКЦИИ):\n{}';self.reject()
  self.setUp();self.facts['privacy']['vision']['context']={'secret':'old page'};self.reject()
  self.setUp();self.facts['typing']['observedValue']='no inserted sentinel';self.reject()
 def test_native_wheel_requires_matching_http_receipt_and_sandbox_forwarding(self):
  self.facts['requests']=[r for r in self.facts['requests'] if r['kind']!='wheel'];self.reject()
  self.setUp();self.facts['wheelInputs'][0]['receipt']['trusted']=False;self.reject()
  self.setUp();self.facts['wheelInputs'][0]['forwarded'][0]['deltaY']=300;self.reject()
  self.setUp();self.facts['wheelInputs'][0].pop('ready');self.reject()
 def test_prepared_wheel_requires_saved_intent_before_dispatch_within_the_original_budget(self):
  for key,value in [('status','prepared'),('status','failed'),('timeoutMs',12000),('intentSavedAt',1012),('sentAt',999),('completedAt',11001),('finishedAt',1019),('startedAt',-1)]:
   self.setUp();self.facts['wheelInputs'][0][key]=value;self.reject_wheel()
  for key in ('intentSavedAt','completedAt','pin','before','ready','pointer'):
   self.setUp();self.facts['wheelInputs'][0].pop(key);self.reject_wheel()
  self.setUp();self.facts['wheelInputs'][0]['error']={'message':'receipt timed out'};self.reject_wheel()
 def test_prepared_wheel_rejects_recycled_native_owners_geometry_and_zoom(self):
  for key,value in [('current',False),('destroyed',True),('webContentsId',301),('revision',3),('navigationEpoch',2),('url','http://127.0.0.1:43112/site/1'),('zoom',2),('zoom',True),('focused',False),('visible',False),('viewVisible',False),('attached',False),('blocked',True),('loading',True)]:
   self.setUp();item=self.facts['wheelInputs'][0];item['ready']['native'][key]=value;item['readiness']=copy.deepcopy(item['ready']);self.reject_wheel()
  for key,value in [('focused',False),('visible',False),('minimized',True)]:
   self.setUp();item=self.facts['wheelInputs'][0];item['ready']['native']['window'][key]=value;item['readiness']=copy.deepcopy(item['ready']);self.reject_wheel()
  for key in ('before','native'):
   self.setUp();item=self.facts['wheelInputs'][0];item['ready'][key]['bounds']['x']+=1;item['readiness']=copy.deepcopy(item['ready']);self.reject_wheel()
  self.setUp();item=self.facts['wheelInputs'][0];item['ready']['before']['zoom']=2;item['readiness']=copy.deepcopy(item['ready']);self.reject_wheel()
 def test_prepared_wheel_requires_the_same_ready_document_and_real_pointer_coordinates(self):
  for key,value in [('identity','another document'),('timeOrigin',1001),('url','https://outside.invalid/'),('focused',False),('readyState','interactive'),('visibilityState','hidden'),('hit',False),('point',{'x':39,'y':40}),('pointer',None),('pointer',{'trusted':False,'x':40,'y':40}),('pointer',{'trusted':True,'x':40,'y':38})]:
   self.setUp();item=self.facts['wheelInputs'][0];item['ready']['dom'][key]=value;item['readiness']=copy.deepcopy(item['ready']);self.reject_wheel()
  for key,value in [('point',{'x':56,'y':191}),('pointer',{'warpResult':1,'postAccess':True}),('pointer',{'warpResult':0,'postAccess':False}),('waitingFor',['native-pointer-not-observed'])]:
   self.setUp();self.facts['wheelInputs'][0][key]=value;self.reject_wheel()
  self.setUp();self.facts['wheelInputs'][0]['receipt']['identity']='foreign HTTP document';self.reject_wheel()
 def test_prepared_wheel_requires_actual_masonry_scroll_and_matching_readback(self):
  for key,value in [('scrollBefore',1200),('scrollAfter',0),('scrollAfter',3000)]:
   self.setUp();self.facts['wheelInputs'][0][key]=value;self.reject_wheel()
  self.setUp();self.facts['wheelInputs'][0]['uiAfter']['scrollTop']=1199;self.reject_wheel()
  self.setUp();self.facts['wheelInputs'][0]['uiAfter']['open']=False;self.reject_wheel()
 def test_prepared_wheel_accepts_live_scaled_coordinates_and_separate_final_cleanup(self):
  item=self.facts['wheelInputs'][0];item['pin']['zoom']=2
  for key in ('before','ready'):
   snapshot=item[key];snapshot['pin']['zoom']=2
   for name in ('before','native'):snapshot[name]['zoom']=2
   snapshot['dom']['point']={'x':20,'y':20};snapshot['dom']['viewport']={'width':146,'height':210}
  item['ready']['dom']['pointer']={'trusted':True,'x':20,'y':20};item['readiness']=copy.deepcopy(item['ready'])
  item['completedAt']=10999;item['finishedAt']=11050
  self.assertEqual(self.verify_wheel(),[1000,1010,1011,10999,11050])
 def test_guest_http_click_cannot_be_replaced_with_a_claimed_input_flag(self):
  self.facts['requests']=[r for r in self.facts['requests'] if r['kind']!='click'];self.reject()
  self.setUp();event=next(r for r in self.facts['inputs'] if r['selector']=='#site-next');event['events'][0]['identity']='another document';self.reject()
 def test_model_must_receive_actual_result_urls_and_newly_render_its_response(self):
  self.facts['models'][0]['groundedResults'][0]['url']='https://invented.invalid/';self.reject()
  self.setUp();self.facts['answers'][0]['beforeAssistantCount']=20;self.reject()
  self.setUp();self.facts['models'][1]['payload']['messages'][-1]['content']+='mouse635-typed-secret';self.reject()
 def test_nora_close_and_overlay_revoke_context_and_hide_actual_views(self):
  self.facts['nora']['vision']['context']={'old':'page'};self.reject()
  self.setUp();self.facts['captureModal']['actualViews'][0]['viewVisible']=True;self.reject()
  self.setUp();self.facts['captureModal']['decodedSnapshots'].pop();self.reject()
  self.setUp();self.facts['captureRestored']['native']['pages'][0]['navigationEpoch']+=1;self.reject()
 def test_empty_query_revokes_native_views_but_keeps_ordinary_pages_hidden(self):
  self.facts['cleared']['ordinaryNative'][0]['visible']=True;self.reject()
  self.setUp();self.facts['cleared']['vision']['context']={'stale':'page'};self.reject()
  self.setUp();self.facts['cleared']['pages']['revision']=self.facts['cleared']['before']['pages']['revision'];self.reject()
 def test_ephemeral_cookie_cleanup_requires_an_actual_cookie_before(self):
  self.facts['previewCookiesBefore']=[];self.reject()
  self.setUp();self.facts['nora']['previewCookiesAfter']=[{'name':'mouse635_search_only'}];self.reject()
 def test_navigation_and_close_cannot_retain_document_or_context(self):
  self.facts['navigation']['after']['identity']=self.facts['navigation']['before']['identity'];self.reject()
  self.setUp();self.facts['closed']['vision']['lastAction']={'type':'click'};self.reject()
  self.setUp();self.facts['closed']['cookies']['normal']=[{'name':'mouse635_search_only'}];self.reject()
 def test_profile_restore_is_proved_by_raw_bank_prefs_tabs_and_native_identity(self):
  for key in ('bank','prefs','tabIds','native','identities'):
   self.setUp()
   if key in ('bank','prefs'):self.facts['original']['after'][key]['changed']=True
   else:self.facts['original']['after'][key].pop()
   self.reject()
 def test_purple_browser_background_and_readable_labels_are_required(self):
  for field,value in (('action','rgb(23, 108, 72)'),('accent','#176c48'),('resultsBackground','rgb(220, 220, 220)'),('visionControls',1),('screenText',True)):
   self.setUp();self.facts['initialScene']['ui']['design'][field]=value;self.reject()
  self.setUp();self.facts['captures'][0]['ui']['design']['labels'][0]['textTransform']='uppercase';self.reject()
  self.setUp();self.facts['captures'][1]['ui']['design']['cards'][0]['domain']['fontSize']=10;self.reject()
 def test_sixteen_pixel_corners_and_actual_css_grid_cannot_be_legacy_absolute_layout(self):
  self.facts['initialScene']['native']['pages'][0]['radius']=12;self.reject()
  self.setUp();self.facts['initialScene']['ui']['design']['cards'][0]['slotRadius']='12px';self.reject()
  self.setUp();self.facts['initialScene']['ui']['design']['grid']['display']='block';self.reject()
  self.setUp();self.facts['initialScene']['ui']['design']['cards'][0]['position']='absolute';self.reject()
  self.setUp();self.facts['initialScene']['ui']['design']['cards'][0]['gridRowEnd']='auto';self.reject()
 def test_spinner_safe_error_and_real_http_retry_require_both_themes(self):
  self.facts['requestStates'].pop();self.reject()
  self.setUp();self.facts['requestStates'][0]['loading']['request']['spinnerVisible']=False;self.reject()
  self.setUp();self.facts['requestStates'][0]['error']['request']['errorText']='Error invoking remote method mouse:tile-search';self.reject()
  self.setUp();self.facts['requestStates'][1]['error']['request']['retryVisible']=False;self.reject()
  self.setUp();self.facts['requestStates'][0]['request']['responseStatus']=200;self.reject()
  self.setUp();self.facts['requests']=[r for r in self.facts['requests'] if r.get('form',{}).get('q')!='mouse635 unavailable light' or r.get('controlled')];self.reject()
 def test_request_state_os_images_are_bound_to_their_exact_bytes_and_new_generation(self):
  name=self.facts['requestStates'][0]['loadingCapture']['filename'];self.files[name]=b'not a PNG';self.reject()
  self.setUp();self.facts['requestStates'][0]['retried']['native']['revision']=self.facts['initialScene']['native']['revision'];self.reject()
  self.setUp();self.facts['requestStates'][1]['errorCapture']['filename']='mouse-635-library-page.png';self.reject()



if __name__=='__main__':unittest.main()
