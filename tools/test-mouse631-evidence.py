#!/usr/bin/env python3
"""Synthetic unit fixtures for rejection rules; these are not native evidence."""
import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import struct
import unittest
import zlib
from unittest import mock

HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('mouse630_evidence', HERE/'mouse631-evidence.py')
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
ui_spec=importlib.util.spec_from_file_location('mouse630_ui_unit_fixtures',HERE/'test-mouse631-ui-evidence.py')
UI_FIXTURES=importlib.util.module_from_spec(ui_spec)
ui_spec.loader.exec_module(UI_FIXTURES)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def png(width, height, pixel):
    def chunk(kind, value):
        return struct.pack('>I', len(value))+kind+value+struct.pack('>I', zlib.crc32(kind+value)&0xffffffff)
    raw = b''.join(b'\0'+bytes(channel for x in range(width) for channel in pixel(x, y)) for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b'')


def rect(x, y, width, height):
    return dict(x=x, y=y, width=width, height=height, right=x+width, bottom=y+height)


def header_ui():
    panes = []
    for index in range(2):
        x = index*300
        panes.append({'pane':'p'+str(index), 'tabId':'tab'+str(index), 'roundBottom':12,
            'bounds':rect(x,40,300,300), 'header':rect(x,40,300,28), 'slot':rect(x,96,300,244),
            'dock':{'hidden':False, 'parentPane':'p'+str(index), 'bounds':rect(x,68,300,28)},
            'pill':{'id':'task'+str(index), 'tabId':'tab'+str(index), 'desk':'desk1',
                'dismiss':{'ready':True}, 'bounds':rect(x+8,70,284,24),
                'radius':999, 'borderWidth':'0px', 'shadow':'none'}})
    return {'viewport':{'width':600,'height':400}, 'globalRail':False, 'privateMode':False,
            'desk':'desk1', 'panes':panes}


def modal_header(ui):
    result=copy.deepcopy(ui)
    for pane in result['panes']:
        shape=pane['pill']['bounds']
        pane['pill']['dismiss']={'ready':False,'reason':'covered or clipped','lastHit':'dialog',
            'width':20,'height':20,'clip':{'left':shape['x'],'top':shape['y'],'right':shape['right'],'bottom':shape['bottom']},
            'fragments':[{'left':shape['right']-24,'top':shape['y']+2,'width':20,'height':20}]}
    return result


def static_fixture():
    raw = png(64,64,lambda x,y:(20+x%3,40,60,255))
    files = {name:raw for name in ('mouse-unit-crop.png','mouse-unit-display.png','mouse-unit-ref.png')}
    size = {'width':64,'height':64}
    capture = {'source':'globalCapture.acquire(display)', 'kind':'screen', 'backend':'synthetic-unit-backend',
        'contentBounds':rect(0,0,64,64), 'display':{'bounds':rect(0,0,64,64)},
        'filename':'mouse-unit-crop.png', 'screenCapture':'mouse-unit-display.png',
        'pixelSize':size, 'screenPixelSize':size, 'cropPixels':{'x':0,'y':0,**size},
        'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0},
        'readiness':{'source':'current static shell readback matched to native display pixels',
            'attempts':[{'sequence':1,'accepted':True,'reasons':[]}],
            'reference':{'source':'webContents.capturePage static shell UI only',
                'filename':'mouse-unit-ref.png','pixelSize':size}}}
    return files, capture, {'viewport':size}, rect(8,8,48,24)


def feedback_fixture():
    blobs = {}
    def picture(name, raw, width=64, height=128):
        blobs[name] = raw
        return {'file':name,'source':'BrowserWindow.capturePage','pixelSize':{'width':width,'height':height},'sha256':sha(raw)}
    def visual(state, reduced=False):
        return {'state':state,'hidden':state is None,'badgeBounds':{'x':20,'y':60,'width':24,'height':4},
                'reducedMotion':reduced,
                'animationName':'none' if reduced else 'mouse-capture-confirm',
                'bladeAnimationName':'mouse-capture-shutter',
                'bladeDisplay':'none' if reduced else 'block','bladeTransform':'matrix(1,0,0,1,0,0)'}
    def ui(tab, phase, percent):
        return {'viewport':{'width':64,'height':128},'footer':{'state':'downloading','count':1,'bounds':{'x':0,'y':104,'width':64,'height':24}},
            'pill':{'bounds':{'x':8,'y':30,'width':48,'height':24},'hidden':False,
                'ariaNow':None if percent is None else str(percent), 'value':'…' if percent is None else str(round(percent))+'%',
                'state':phase,'tabId':tab}, 'head':{'x':0,'y':0,'width':64,'height':28},
            'slot':{'x':0,'y':56,'width':64,'height':48}}
    native_events, events, activities = [], [], {}
    def group(case, identity, states, private=False, sampled=True):
        total = 0 if 'unknown' in case else 1048576
        tab = 'private-tab' if private else 'normal-tab'
        def activity(state, received):
            return {'id':identity,'filename':case+'.bin','tabId':tab,'desk':'desk1','state':state,
                    'received':received,'total':total,'createdAt':1,'updatedAt':2,'expiresAt':0}
        native_events.append({'case':case,'scope':'private' if private else 'normal','event':'will-download',
            'nativeState':'progressing','at':1,'received':0,'total':total,'activity':activity('started',0)})
        for index, (state, received) in enumerate(states):
            row = activity(state, received)
            terminal = state in ('completed','cancelled','error')
            native_events.append({'case':case,'scope':'private' if private else 'normal','event':'done' if terminal else 'updated',
                'nativeState':{'error':'interrupted'}.get(state,state) if terminal else 'progressing',
                'at':index+2,'received':received,'total':total,'activity':copy.deepcopy(row)})
            if sampled:
                percent = 100 if state=='completed' else received/total*100 if total else None
                phase = {'completed':'completed','cancelled':'stopped','error':'error'}.get(state,'running')
                task = {'id':'download:'+identity,'taskId':identity,'source':'download','kind':'download',
                    'privateMode':private,'tabId':tab,'desk':'desk1','phase':phase,'downloadState':state,
                    'percent':percent,'estimated':False}
                events.append({'case':case,'state':state,'at':index+2,'activity':copy.deepcopy(row),'task':task,
                    'ui':ui(tab,phase,percent),'native':{'tabId':tab,'bounds':ui(tab,phase,percent)['slot']}})
            activities[identity] = row
    group('known','known',[('paused',262144),('downloading',262144),('completed',1048576)])
    group('unknown','unknown',[('downloading',262144),('cancelled',262144)])
    group('retry','broken',[('error',0)])
    group('retry','retried',[('completed',1048576)])
    group('normal-unknown','background',[('paused',262144)],sampled=False)
    group('private-unknown','private',[('downloading',262144),('cancelled',262144)],private=True)
    # A real restart may clear the terminal counter. The earlier native update
    # and server response prove delivery independently of that terminal value.
    broken_first=next(row for row in native_events if row['activity']['id']=='broken')
    broken_first['at']=101
    partial=copy.deepcopy(broken_first);partial.update(event='updated',at=110,received=57344)
    partial['activity'].update(state='downloading',received=57344)
    native_events.insert(native_events.index(broken_first)+1,partial)
    for row in native_events:
        if row['activity']['id']=='broken' and row['event']=='done':row['at']=130
        if row['activity']['id']=='retried':row['at']=141 if row['event']=='will-download' else 180
    for row in events:
        if row['activity']['id']=='broken':row['at']=131
        if row['activity']['id']=='retried':row['at']=181
    http_requests=[{'case':'retry','at':100,'range':None,'status':200,'sentBytes':65536,'aborted':True},
        {'case':'retry','at':120,'range':'bytes=57344-','status':404,'sentBytes':0,'aborted':False},
        {'case':'retry','at':140,'range':None,'status':200,'sentBytes':1048576,'aborted':False}]
    known_event = next(e for e in events if e['case']=='known' and e['state']=='downloading')
    screenshot = png(64,128,lambda x,y:(20+x%3,40,60,255))
    screenshots = [{**picture('mouse-unit-download-'+theme+'.png', screenshot), 'theme':theme,'case':'known',
                    'ui':copy.deepcopy(known_event['ui']),'native':copy.deepcopy(known_event['native'])} for theme in ('light','dark')]
    before = png(64,128,lambda x,y:(10,10,10,255))
    after = png(64,128,lambda x,y:(20,20,20,255) if 20<=x<44 and 60<=y<64 else (10,10,10,255))
    canvas = png(32,16,lambda x,y:(30,40,50,255))
    for name in ('mouse-unit-canvas.png','mouse-unit-clipboard.png','mouse-unit-saved.png'):
        blobs[name] = canvas
    same_sha = sha(canvas)
    copied = {'result':{'ok':True},'canvasFile':'mouse-unit-canvas.png','clipboardFile':'mouse-unit-clipboard.png',
        'canvasSha256':same_sha,'clipboardSha256':same_sha,'canvasBitmapSha256':same_sha,'clipboardBitmapSha256':same_sha,
        'feedback':visual('copy'),'frame':picture('mouse-unit-feedback.png',after),'changedPixels':96,
        'changedRegion':{'x':20,'y':60,'width':24,'height':4},'changedRegionUnits':'pixels',
        'changedTolerance':0,'changedAlgorithm':'any RGB channel differs'}
    plateau_before={**visual('copy'),'viewport':{'width':64,'height':128},
        'sampledAt':800,'timeOrigin':100000,'badgeOpacity':'1',
        'badgeAnimations':[{'animationName':'mouse-capture-confirm','currentTime':300,
            'startTime':500,'playState':'running','timing':{'duration':1400}}]}
    plateau_after=copy.deepcopy(plateau_before);plateau_after['sampledAt']=910
    plateau_after['badgeAnimations'][0]['currentTime']=410
    copy_attempt={'source':'one actual copy export and one BrowserWindow.capturePage during the natural CSS visibility plateau',
        'mainTimeOrigin':100000,'copyStartedAt':500,'copyResolvedAt':510,'result':{'ok':True},
        'barrier':{'reason':'plateau','before':plateau_before,'samples':[copy.deepcopy(plateau_before)]},
        'requestedAt':810,'receivedAt':900,'after':plateau_after,'afterSampledAt':920,'encodedAt':930}
    copied['feedback']=copy.deepcopy(plateau_before)
    copied['frame'].update({key:copy_attempt[key] for key in
        ('mainTimeOrigin','requestedAt','receivedAt','encodedAt')})
    copy_attempt.update({key:copy.deepcopy(copied[key]) for key in
        ('frame','changedPixels','changedRegion','changedRegionUnits','changedTolerance','changedAlgorithm')})
    payload_sha = sha(bytes([71])*1048576)
    private_activity = copy.deepcopy(activities['private']);private_activity['state']='downloading'
    private_task = next(e['task'] for e in events if e['case']=='private-unknown' and e['state']=='downloading')
    facts = {'version':'6.0.31','platform':'darwin','arch':'arm64',
        'source':'actual Electron DownloadItem events and capture/export IPC','restored':True,
        'downloads':{'nativeEvents':native_events,'events':events,'screenshots':screenshots,'httpRequests':http_requests,
            'files':[{'case':case,'bytes':1048576,'expectedBytes':1048576,'sha256':payload_sha,'expectedSha256':payload_sha} for case in ('known','retry')]},
        'privacy':{'normalIds':['background'],'before':{'privateMode':False,'items':[activities['background']]},
            'privateDuring':{'privateMode':True,'items':[private_activity]},'privateTasks':[private_task],
            'normalAfter':{'privateMode':False,'items':[activities['background']]},'privateDisposed':{'privateMode':True,'items':[]}},
        'capture':{'motionMedia':{'before':True,'normal':False,'restored':True},
            'acquired':visual('capture'),'before':picture('mouse-unit-before.png',before),'copied':copied,
            'copyAttempt':copy_attempt,
            'saved':{'result':{'ok':True},'savedFile':'mouse-unit-saved.png','canvasSha256':same_sha,'fileSha256':same_sha,'feedback':visual('save')},
            'cancelled':{'result':{'canceled':True},'feedback':visual(None)},
            'failed':{'result':{'error':'Mouse630 deliberate export failure'},'feedback':visual(None)},
            'reducedMotion':{'matches':True,**visual('copy',True)},
            'global':{'source':'synthetic input frame, real native editor and export IPC',
                'motionMedia':{'before':True,'normal':False,'restored':True},
                'initialFeedback':visual('capture'),'saveFeedback':visual('save'),
                'reducedMotion':{'matches':True,**visual('copy',True)}}}}
    return facts, blobs


def wheel_dispatch(identity, surface, before, after, direction, axis='x', count=4, distance=128):
    return {'at':1000,'channel':'mouse:desktop-swipe','origin':E.WHEEL_PACKET_ORIGIN,
        'packet':{'id':identity,'source':'trusted-wheel','surface':surface,
            'tabId':('private-tab' if before.startswith('private') else 'normal-tab') if surface=='page' else '',
            'from':before,'to':after,'direction':direction,
            'gesture':{'axis':axis,'direction':direction,'count':count,'distance':distance,'startedAt':900}}}


def observations(amount=32, count=4, axis='x', trusted=True, prevented=False):
    return [{'isTrusted':trusted,'deltaX':amount if axis=='x' else 0,
             'deltaY':amount if axis=='y' else 0,'deltaMode':0,'defaultPrevented':prevented} for _ in range(count)]


def inputs(amount=32, count=4, axis='x', precise=True):
    return [{'type':'mouseWheel','x':24,'y':24,'deltaX':amount if axis=='x' else 0,
             'deltaY':amount if axis=='y' else 0,'hasPreciseScrollingDeltas':precise,
             'canScroll':True,'at':100+index*16} for index in range(count)]


def tutorial_shell(desk, learned, dispatch=None):
    packet = dispatch['packet'] if dispatch else None
    return {'desktopId':desk,'hintHidden':learned,
        'gesture':{'supported':True,'learned':learned,'running':False,'currentId':'',
            'hintVisible':not learned,'lastResult':{**{key:packet[key] for key in ('id','from','to')},
                'completed':True} if packet else None},
        'nora':{'open':True,'hidden':False,'modal':True,'phase':'open','inert':False,
                'x':0,'y':40,'width':64,'height':40}}


def tutorial_fixture():
    facts=UI_FIXTURES.fixture()
    picture=png(64,64,lambda x,y:(20+x%3,40,60,255))
    blobs={name:picture for name in ('mouse-629-swipe-first-use.png','mouse-629-swipe-restart.png')}
    slides={'version':'6.0.28',
        **{key:True for key in ('simultaneous','pngSurfaces','compositorOnly','nativeIdentityPreserved',
                              'viewportAndScrollPreserved','slowAckBounded','noraStayedOpen')},
        'transitions':[{**{key:copy.deepcopy(row[key]) for key in ('theme','direction','before','after')},
            'pageBefore':[{'scrollX':0,'scrollY':137}]*2,'pageAfter':[{'scrollX':0,'scrollY':137}]*2}
            for row in facts['records'] if row['kind']=='successful-native-switch']}
    return facts,slides,blobs


def wheel_fixture():
    def state(desk, learned=True, dispatch=None):
        gesture = tutorial_shell(desk,learned,dispatch)['gesture'];gesture['hintVisible']=False
        return {'desktopId':desk,'noraOpen':False,'switching':False,'gesture':gesture}
    packets = [wheel_dispatch('wheel1','page','normal0','normal1','left'),
        wheel_dispatch('wheel2','control','normal1','normal0','right','y',1,80),
        wheel_dispatch('wheel3','page','private0','private1','left')]
    facts = {'version':'6.0.31','electronVersion':'40.0.0','source':E.WHEEL_SOURCE,
        'recognizer':E.WHEEL_RECOGNIZER,'physicalTwoFingerDeviceVerified':False,'restored':True,
        'limits':{'horizontalThreshold':112,'controlThreshold':64,'quietMs':280,'cooldownMs':420},
        'inputs':[],'observed':[],'packets':packets,'cases':{},
        'privacy':{'normalBefore':{'completed':True},'normalAfter':{'completed':True},
            'privateDisposed':{'storeDestroyed':True,'tabCount':0,'webContentsDestroyed':True}},
        'capture':{'file':'mouse-630-wheel-desktops.png','source':'BrowserWindow.capturePage'}}
    rows = [('verticalPage','y',50,4,0,0,1),('horizontalScroller','x',55,4,0,0,1),
        ('pageHandledWheel','x',55,4,0,0,1),('contentEditable','x',55,4,0,0,1),
        ('closedPage','x',32,8,0,1,1),('shellControl','y',-80,1,1,2,2),
        ('boundary','x',-32,4,2,2,1),('privateClosedPage','x',32,4,2,3,3)]
    for name,axis,amount,count,start,end,wc in rows:
        if name=='shellControl':before,after=state('normal1',dispatch=packets[0]),state('normal0',dispatch=packets[1])
        elif name=='closedPage':before,after=state('normal0'),state('normal1',dispatch=packets[0])
        elif name=='boundary':before=after=state('normal0',dispatch=packets[1])
        elif name=='privateClosedPage':before,after=state('private0',False),state('private1',dispatch=packets[2])
        else:before=after=state('normal0')
        events = observations(amount,count,axis,prevented=name=='pageHandledWheel')
        facts['cases'][name]={'before':before,'after':after,'packetIndex':start,
                             'packetEndIndex':end,'packetCount':end-start,'observed':events}
        facts['observed'].append({'case':name,'webContentsId':wc,'events':events})
        facts['inputs'].extend({'case':name,'webContentsId':wc,**event} for event in inputs(amount,count,axis,axis=='x'))
    facts['cases']['verticalPage'].update(beforeScrollY=0,afterScrollY=200)
    facts['cases']['horizontalScroller'].update(beforeScrollLeft=0,afterScrollLeft=220)
    facts['cases']['privateClosedPage'].update(normalPersisted={'completed':True},privatePersisted=None)
    facts['cases']['forgedDOM']={'before':state('normal0'),'after':state('normal0'),
        'packetIndex':0,'packetEndIndex':0,'packetCount':0,'observed':observations(80,6,trusted=False)}
    closed = facts['cases']['closedPage']
    facts['cases']['duplicateBurst']={'before':closed['before'],'after':closed['after'],'packetCount':1,'inputCount':8}
    return facts, {'mouse-630-wheel-desktops.png':png(64,64,lambda x,y:(20+x%3,40,60,255))}


def add_nora_readiness(row, blobs, stale_first=False):
    """Synthetic, known pixel counts; no native verification is claimed here."""
    geometry, capture = row['geometry'], row['capture']
    panel = geometry['panel'];prefix=capture['capture'][:-4]
    geometry['opaque']={'x':panel['x']+panel['width']/2-10,'y':panel['y']+6,'width':20,'height':8}
    native=row['native'];roots=[None]*native[0]['rootsCount']
    for page in native:roots[page['rootIndex']]=page['rootId']
    roots=[100 if value is None else value for value in roots]
    owners=row.get('underlyingPages') or [row['underlyingPage']]
    proof={'source':'current static shell readback matched to native display pixels',
        'clock':'node performance.now() milliseconds','startedAt':100,'timeoutMs':4000,'maxFrames':20,
        'regions':copy.deepcopy(geometry['regions']),
        'background':{'bounds':geometry['opaque'],'css':geometry['fill'],'rgb':row['expected']},
        'desk':owners[0]['desk'],'holdId':sha(b'synthetic native hold'),'rootOrder':roots,'stability':[],'attempts':[]}
    shell=blobs[capture['capture']];decoded=E.decode_png(shell,'synthetic shell');pink=[227,31,173,255]
    background_pixels=152 if panel['width']%2 else 160
    for sequence,stale in enumerate(([True,False] if stale_first else [False]),1):
        offset=(sequence-1)*10
        display=png(capture['pixelSize']['width'],capture['pixelSize']['height'],lambda x,y:tuple(pink)) if stale else blobs[capture['source']]
        attempt={'sequence':sequence,'readbackStartedAt':101+offset,'readbackCompletedAt':102+offset,
            'captureStartedAt':103+offset,'captureCompletedAt':104+offset,'completedAt':105+offset,'elapsedMs':4.8+offset,
            'backend':capture['backend'],'accepted':not stale,'tolerance':2,'regions':[],
            'theme':{**proof['background'],'referencePixels':background_pixels,
                'mismatched':background_pixels if stale else 0,'minimum':background_pixels//4},
            'foregroundSamples':copy.deepcopy(row['samples']),'foregroundReady':not stale,'reasons':[]}
        for kind,raw in (('shell',shell),('display',display)):
            file=prefix+'-attempt-'+str(sequence).zfill(2)+'-'+kind+'.png';blobs[file]=raw
            attempt[kind]={'file':file,'sha256':sha(raw),
                'pixelSize':{'width':decoded['width'],'height':decoded['height']} if kind=='shell' else capture['pixelSize']}
        if stale:attempt['reasons'].append('native display does not match the current theme')
        for region in geometry['regions']:
            box=region['bounds'];compared=(box['width']-2)*(box['height']-2)
            item={'label':region['label'],'bounds':box,'compared':compared,'mismatched':compared if stale else 0,
                'referenceColors':3,'nativeColors':1 if stale else 3}
            if stale:
                x,y=box['x']+1,box['y']+1
                item['firstMismatch']={'reference':{'x':x,'y':y},'actual':{'x':x,'y':y},
                    'css':{'x':x+.5,'y':y+.5},'referenceRGBA':E.png_pixel(decoded,x,y),'nativeRGBA':pink}
                attempt['reasons'] += [region['label']+': native UI is not painted',
                    region['label']+': native pixels differ from the current static shell readback']
            attempt['regions'].append(item)
        if stale:
            for sample in attempt['foregroundSamples']:sample['rgba']=pink
            attempt['reasons'].append('native display has not reached the current Nora foreground')
        proof['attempts'].append(attempt)
        for stage,at in (('before-readback',100.5),('before-display',102.5),('after-display',104.5)):
            proof['stability'].append({'sequence':sequence,'stage':stage,'at':at+offset,
                'desk':proof['desk'],'holdId':proof['holdId'],'blocked':True,'rootOrder':roots.copy(),
                'native':copy.deepcopy(native),'geometry':copy.deepcopy(geometry),'contentBounds':capture['contentBounds'].copy()})
    proof.update(attemptCount=len(proof['attempts']),elapsedMs=5.1+offset,completedAt=105.5+offset)
    row['readiness']=proof


def nora_fixture():
    def native():
        return [{'id':'page'+str(index),'webContentsId':index+10,'cached':False,'view':False,'clip':False,
            'rootId':index+1,'rootIndex':index+1,'rootsCount':3,'attached':True} for index in range(2)]
    pages = [{'id':'page'+str(index),'webContentsId':index+10,
        'url':'http://127.0.0.1:3000/'+('left' if index==0 else 'right'),'epoch':1,
        'timeOrigin':1000+index,'width':64,'height':80,'scrollX':0,'scrollY':137,'marker':.1+index/10} for index in range(2)]
    facts = {'version':'6.0.31','platform':'darwin','arch':'arm64',
        'source':'actual Electron native views and globalCapture.acquire(display)',
        'physicalInput':False,'restored':True,'nativeSamples':500,'visibilityViolations':[],
        'motionMedia':{'before':True,'normal':False,'restored':True},
        'pagesBefore':pages,'pagesAfter':copy.deepcopy(pages),'rows':[],
        'resize':{'closedAfterInvalidation':True,'native':native()}}
    blobs = {}
    for theme in ('light','dark'):
        divergent=native();divergent[0]['view']=True;divergent[0]['clip']=True
        facts['rows'].append({'theme':theme,'phase':'cached-native-divergence','faultInjected':True,
            'rootOrderBefore':[100,1,2],'rootOrderAfter':[100,1,2],'divergent':divergent,'repaired':native()})
        facts['rows'].append({'theme':theme,'phase':'close-reopen','frames':[
            {'phase':'closing','open':True,'hidden':False,'duration':300,'at':1+index*16,'y':2+index*6} for index in range(3)]})
        for phase in ('open','reversed','desk-switch')+(('after-resize',) if theme=='dark' else ()):
            rgb = [240,242,246] if theme=='light' else [28,32,42]
            selected = 1 if phase in ('desk-switch','after-resize') else 0
            page_rgb = [227,31,173] if selected==0 else [23,171,213]
            regions=[{'label':'Nora title','selector':'.desk-title','bounds':{'x':12,'y':82,'width':12,'height':10}},
                     {'label':'Nora actions','selector':'.desk-actions','bounds':{'x':40,'y':82,'width':12,'height':10}}]
            def pixels(x,y):
                if any(r['bounds']['x']<=x<r['bounds']['x']+12 and 82<=y<92 for r in regions):return (20+(x+y)%3*20,30,40,255)
                return tuple(rgb+[255]) if 8<=x<56 and 60<=y<100 else tuple(page_rgb+[255])
            name = 'mouse-630-nora-'+theme+'-'+phase
            blobs[name+'.png']=png(64,128,pixels)
            blobs[name+'-display.png']=png(96,160,lambda x,y:pixels(x-16,y-16) if 16<=x<80 and 16<=y<144 else (0,0,0,255))
            points=[{'x':x,'y':70} for x in (20,32,44)]
            facts['rows'].append({'theme':theme,'phase':phase,
                'geometry':{'open':True,'hidden':False,'modal':True,'phase':'open','viewport':{'width':64,'height':128},
                    'fill':'rgb('+','.join(map(str,rgb))+')','panel':{'x':8,'y':60,'width':48,'height':40},'points':points,'regions':regions},
                'expected':rgb,'samples':[{'point':point,'x':point['x'],'y':point['y'],'rgba':rgb+[255]} for point in points],
                'native':native(),'underlyingPage':{'id':'page'+str(selected),'desk':'desk'+str(selected),'index':selected,
                    'bounds':{'x':0,'y':28,'width':64,'height':80},'rgb':page_rgb},
                'capture':{'display':{'bounds':{'x':0,'y':0,'width':96,'height':160}},
                    'contentBounds':{'x':16,'y':16,'width':64,'height':128},
                    'pixelSize':{'width':96,'height':160},'cropPixels':{'x':16,'y':16,'width':64,'height':128},
                    'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0},'backend':'synthetic-unit-backend',
                    'source':name+'-display.png','capture':name+'.png'}})
            add_nora_readiness(facts['rows'][-1],blobs)
    return facts, blobs


def fractional_fixture():
    facts,blobs=nora_fixture();pages=[];slots=[];snapshots=[];underlying=[]
    roots=[1,2,11,12,13,14,15,16]
    native=[{'id':'page1','webContentsId':11,'cached':False,'view':False,'clip':False,
             'rootId':2,'rootIndex':1,'rootsCount':8,'attached':True}]
    prefix='mouse-630-nora-light-fractional-seven';width=(971-6*6)/7;pink=[227,31,173]
    for index in range(7):
        identity='page0' if index==0 else 'dense'+str(index)
        slot={'id':identity,'x':index*(width+6),'y':28.25,'width':width,'height':80}
        box=E.native_endpoints(slot)
        page=copy.deepcopy(facts['pagesBefore'][0]) if index==0 else {
            'id':identity,'webContentsId':100+index,'url':'http://127.0.0.1:3000/fractional-'+str(index-1),
            'epoch':1,'timeOrigin':1000+index,'scrollX':0,'scrollY':137,'marker':.3+index/100}
        clipped=index%2==0
        page.update(bounds=box,cachedBounds=box.copy(),width=box['width'],height=box['height'],
            clipBounds=box.copy() if clipped else None,
            viewBounds={'x':0,'y':0,'width':box['width'],'height':box['height']} if clipped else box.copy())
        slots.append(slot);pages.append(page)
        raw=png(box['width'],box['height'],lambda x,y:tuple(pink+[255]))
        file=prefix+'-page-'+str(index)+'.png';blobs[file]=raw
        snapshots.append({'id':identity,'bounds':box.copy(),'complete':True,'naturalWidth':box['width'],
            'naturalHeight':box['height'],'file':file,'sha256':sha(raw)})
        underlying.append({'id':identity,'desk':'desk1','index':0,'bounds':box.copy(),'rgb':pink.copy()})
        root_id=1 if index==0 else 10+index
        native.append({'id':identity,'webContentsId':page['webContentsId'],'cached':False,'view':False,
            'clip':False if clipped else None,'rootId':root_id,'rootIndex':roots.index(root_id),
            'rootsCount':len(roots),'attached':True})
    before={'pages':pages,'slots':slots,'rootOrder':roots};points=[{'x':6+959*f,'y':70} for f in (.25,.5,.75)]
    regions=[{'label':'Nora title','selector':'.desk-title','bounds':{'x':14,'y':90,'width':20,'height':16}},
             {'label':'Nora actions','selector':'.desk-actions','bounds':{'x':930,'y':90,'width':20,'height':16}}]
    def pixels(x,y):
        if any(r['bounds']['x']<=x<r['bounds']['x']+20 and 90<=y<106 for r in regions):return (20+(x+y)%3*20,30,40,255)
        return (255,255,255,255) if 6<=x<965 and 60<=y<140 else tuple(pink+[255])
    blobs[prefix+'.png']=png(971,160,pixels)
    blobs[prefix+'-display.png']=png(1003,192,lambda x,y:pixels(x-16,y-16) if 16<=x<987 and 16<=y<176 else (0,0,0,255))
    samples=[]
    for point in points:
        owner=next(page['id'] for page in pages if page['bounds']['x']<point['x']<page['bounds']['x']+page['bounds']['width'])
        samples.append({'point':point,'x':int(point['x']),'y':70,'rgba':[255]*4,'pageId':owner})
    facts['fractionalLayouts']=[{'theme':'light','phase':'fractional-seven','before':before,
        'during':copy.deepcopy(before),'after':copy.deepcopy(before),'snapshots':snapshots,'native':native,
        'underlyingPages':underlying,'expected':[255]*3,'samples':samples,
        'geometry':{'open':True,'modal':True,'hidden':False,'phase':'open','viewport':{'width':971,'height':160},
            'fill':'rgb(255,255,255)','panel':{'x':6,'y':60,'width':959,'height':80},'points':points,'regions':regions},
        'capture':{'display':{'bounds':{'x':0,'y':0,'width':1003,'height':192}},
            'contentBounds':{'x':16,'y':16,'width':971,'height':160},
            'pixelSize':{'width':1003,'height':192},'cropPixels':{'x':16,'y':16,'width':971,'height':160},
            'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0},'backend':'synthetic-unit-backend',
            'source':prefix+'-display.png','capture':prefix+'.png'}}]
    add_nora_readiness(facts['fractionalLayouts'][0],blobs)
    return facts,blobs


EXPECTED_FROZEN_FEATURE_AST = {'require': '4486a1bdfeb1b14b10cf47ac571f7997fa631ab4c911bb26879271a2cf482ef1', 'finite': '16d3c51fc766ea0b1caebfd3923696183faf439848eeeb2df4e046b655920846', 'rectangle': 'b4146cb97656c630484d441422feb48e4d844f18dbdc24883d1152038473ba1c', 'viewport_size': '7529962effdc45174d8da91ad3246885cf61376f09facdc71b8e5fc80f615b37', 'exact_pane_map': 'eafc1552765f8b4bc32874bfe3fb18d7c809dd0e7bba90c554cd3a0e81249bae', 'header_panes': '71e7599fbe878870fa2fb4964d90a206690385363532c70a068c573c166b4eeb', 'static_native_pixels': '74205cb0e72787854fde46df2d97dc044439fe99b47d21b1471186fd6d25f87c', 'verify_headers': '2ff86d2d92532db6da58acf7982d6c268f2216a0591c3496906e234d848ea8fe', 'sha256_value': '791e4636c75f0054b0b4b223b3c19fef3b407e54b29c759b5d86276d35f5b4a7', 'recorded_image': '31d5fba25645bfb2a9a756190e85cb252ee23448846fac23bcf6eb2afc860d28', 'nonnegative_integer': '77cb1ad6bdf95661adca357de77530264a4619cca2cf6db847ba9d27ed9f86a0', 'download_geometry': '8dcc4b1688c689e6f0f6c4fa03de1f468d04efc48186fef2f72f52bba27e4e53', 'painted_region': 'eaaef873d5502692e6d38ba5adb4c7085ebfa8cf547bc82f573b62de0c6287bd', 'motion_media': 'beae125b3a6372fe4d923cbdefa4dbed7b2e51e279d82d7d5445faf91e38ebdc', 'feedback_state': '979de100482073466fb0d56fcb9184ef9fe7e32a81cf792f6726b32c6fe51834', 'copy_plateau_sample': '90cab22ae3a192423310979f64cb788bd538c1d5a62b7b1fb04c925774716867', 'verify_copy_attempt': '010a43c900581d4d184cd79280221e16d801d78af1e41e497d63a20c47978658', 'verify_retry_lifecycle': '22340b36895cb3a6da29006bda37364750fce61079ea885cfbc8b975a47b547f', 'verify_feedback': '6bc76783c84ab309c7c75785ab10d04db030211d241fadc1229346497e4322b3', 'wheel_observations': '59463ec7d06a0438741325e8eedbd27051f9a61972306cb092f80a09aea2be7a', 'wheel_inputs': 'c0717b590ae5ecc406cdb221313a6905ea9f1ed35754593a7ca4b46fa24e5655', 'wheel_packet': '3316bda73f3f0f54f7454ae3ec46c6d84cd28f85a0a54ffabf85c9d087ce28cb', 'verify_wheel_gestures': 'c40521b839ad9a109e6fc88760f3bc3b781d278028d890c0342f00863c7e8070', 'native_display_images': '0b98568c4a44a160567faf0e9d248a75b740f8c06e025d0803a3ea6543a654d5', 'opaque_css_rgb': 'e9b3c33fc3f09185f6698a9c6a743fc1b8a1611945b8bc4fa6b9d58bf4bb4cdc', 'native_views': 'fe4fa5041f9d210dc4dde5f804b29c894c42a0ad830d02a8cc0ddd2187ba5bbe', 'nora_static_pixels': '61a78382a40ffb594c2e74ec91e5c49d5275334d6d226adfa933f885a8afcc72', 'verify_nora_readiness': 'f40ab5889175f9056394d25ffd0881b5fc03d5d794b9ffae97b556758a2f6f6f', 'verify_nora_foreground': '64570bedf9fdcbcafa5bb3fd2653263452079991feda5e9468f30e72d8d5c6a1', 'native_endpoints': '7f2e48007fcae08f04ad00b363922f7b94599254bece9455166a4baee40c68d7', 'verify_fractional_layouts': '1e699a2b287149972e664826f9067e344d78d781bb257f2a39916754e5672723', 'bounded_reader': '851f8c6431f81ec7f4697bac12b93ed2874642c5e23c9192d1ed2fd3bd895d30'}

class Evidence630Tests(unittest.TestCase):
    def test_migrated_feature_algorithms_only_change_runtime_and_artifact_names(self):
        expected=EXPECTED_FROZEN_FEATURE_AST
        nodes={node.name:node for node in ast.parse((HERE/'mouse631-evidence.py').read_text()).body
               if isinstance(node,ast.FunctionDef)}
        class OriginalNames(ast.NodeTransformer):
            def visit_FunctionDef(self,node):
                if node.name=='verify_wheel_pages':node.name='verify_wheel_gestures'
                return self.generic_visit(node)
            def visit_Constant(self,node):
                if isinstance(node.value,str):
                    node.value=node.value.replace('6.0.31','6.0.29').replace('Mouse630','Mouse629').replace('mouse630','mouse629').replace('mouse-630-','mouse-629-').replace('MOUSE_630_','MOUSE_629_')
                return node
        for name,digest in expected.items():
            current='verify_wheel_pages' if name=='verify_wheel_gestures' else name
            with self.subTest(function=current):
                actual=hashlib.sha256(ast.dump(OriginalNames().visit(nodes[current])).encode()).hexdigest()
                self.assertEqual(actual,digest)

    def test_retained_core_only_changes_versions_and_superseded_tutorial(self):
        def function(path, name):
            return next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name==name)
        original = function(HERE/'mouse628-evidence.py','verify')
        class AllowedChanges(ast.NodeTransformer):
            def visit_Expr(self, node):
                literals = {part.value for part in ast.walk(node) if isinstance(part,ast.Constant) and isinstance(part.value,str)}
                if 'gesture first-use lifecycle or physical verification claim' in literals:
                    return ast.parse("ui_reviewed['verify_gesture'](swipe, read)").body[0]
                if 'mouse-628-swipe-first-use.png' in literals:return None
                return self.generic_visit(node)
            def visit_Name(self, node):
                if node.id=='JSON_NAMES':node.id='RETAINED_JSON_NAMES'
                return node
            def visit_Compare(self, node):
                self.generic_visit(node)
                if ast.dump(node.left)==ast.dump(ast.parse("doc.get('version')",mode='eval').body):
                    node.comparators=[ast.parse('EXPECTED_VERSIONS[name]',mode='eval').body]
                return node
        original.name='verify_retained'
        self.assertEqual(ast.dump(AllowedChanges().visit(original)),ast.dump(function(HERE/'mouse631-evidence.py','verify_retained')))

    def test_retained_versions_reject_old_runtime_and_relabelled_schema(self):
        docs={name:json.dumps({'version':version}).encode() for name,version in E.EXPECTED_VERSIONS.items()}
        docs['mouse-628-motion-trace.json']=b'{}'
        for name,expected in E.EXPECTED_VERSIONS.items():
            changed=docs.copy();changed[name]=json.dumps({'version':'6.0.29' if expected=='6.0.31' else '6.0.31'}).encode()
            with self.assertRaisesRegex(ValueError,'version mismatch',msg=name):
                E.verify_retained(changed.__getitem__)

    def test_new_wrapper_cannot_skip_retained_failure(self):
        with mock.patch.object(E,'verify_retained',side_effect=ValueError('retained failed')) as gate:
            with self.assertRaisesRegex(ValueError,'retained failed'):E.verify(lambda name:b'{}')
            gate.assert_called_once()

    def test_header_position_ownership_and_rounding_are_checked(self):
        ui=header_ui();self.assertEqual(len(E.header_panes(ui,'synthetic')),2)
        for mutate in (lambda p:p['dock'].update(bounds=rect(0,312,300,28)),
                       lambda p:p['pill'].update(tabId='other'),
                       lambda p:p['pill'].update(radius=0),
                       lambda p:p['pill'].update(borderWidth='1px'),
                       lambda p:p['header'].update(y=float('nan'))):
            changed=copy.deepcopy(ui);mutate(changed['panes'][0])
            with self.assertRaises(ValueError):E.header_panes(changed,'synthetic')

    def test_static_native_pill_pixels_are_independently_compared(self):
        files,capture,ui,region=static_fixture()
        self.assertGreater(E.static_native_pixels(files.__getitem__,capture,ui,[region],'synthetic'),20)
        changed=files.copy();changed['mouse-unit-display.png']=png(64,64,lambda x,y:(50,40,60,255))
        with self.assertRaisesRegex(ValueError,'crop differs'):E.static_native_pixels(changed.__getitem__,capture,ui,[region],'synthetic')
        altered=copy.deepcopy(capture);altered['mapping']['originX']=2
        with self.assertRaisesRegex(ValueError,'pixel mapping'):E.static_native_pixels(files.__getitem__,altered,ui,[region],'synthetic')

    def test_modal_nora_blocks_progress_clickthrough_without_losing_owners(self):
        normal=header_ui();held=modal_header(normal)
        self.assertEqual(len(E.header_panes(held,'held',modal_hold=True)),2)
        with self.assertRaisesRegex(ValueError,'modal Nora'):
            E.header_panes(normal,'held',modal_hold=True)
        with self.assertRaisesRegex(ValueError,'not clickable'):
            E.header_panes(held,'before or after')
        for mode in ('owner','overlay','clip'):
            bad=copy.deepcopy(held);pill=bad['panes'][0]['pill']
            if mode=='owner':pill['tabId']='foreign'
            if mode=='overlay':pill['dismiss']['lastHit']='div'
            if mode=='clip':pill['dismiss']['clip']['left']+=10
            with self.assertRaises(ValueError,msg=mode):E.header_panes(bad,'held',modal_hold=True)

    def test_header_fixture_preserves_zero_outer_corners_and_rounded_internal_corners(self):
        for radius in (0,12):
            known=header_ui();known.update(theme='light',footer=rect(0,372,600,28),bodyRows='40px 332px 28px')
            for pane in known['panes']:pane['roundBottom']=radius
            before=copy.deepcopy(known)
            for pane in before['panes']:
                pane['slot']=rect(pane['bounds']['x'],68,300,272)
                pane['pill']=None;pane['dock']['hidden']=True
            swap=copy.deepcopy(known)
            swap['panes'][0]['tabId'],swap['panes'][1]['tabId']=swap['panes'][1]['tabId'],swap['panes'][0]['tabId']
            swap['panes'][0]['pill'],swap['panes'][1]['pill']=swap['panes'][1]['pill'],swap['panes'][0]['pill']
            for pane in swap['panes']:pane['pill']['bounds']=rect(pane['bounds']['x']+8,70,284,24)
            facts={'rows':[{'theme':'light','before':before,'known':known,'unknown':known,'capture':{}} for _ in range(4)],
                'noraHold':{**{phase:modal_header(known) if phase in ('held','during') else known
                              for phase in ('before','held','during','after')},
                    'snapshots':[{'tabId':p['tabId'],'roundBottom':str(radius),'width':'300px','height':'244px'} for p in known['panes']]},
                'ownershipSwap':{'before':known,'after':swap,'capture':{}}}
            with mock.patch.object(E,'static_native_pixels',return_value=100):
                self.assertEqual(E.verify_headers(lambda name:b'',facts)['noraPaneCornersChecked'],2)
                broken=copy.deepcopy(facts);broken['noraHold']['snapshots'][0]['roundBottom']=str(12 if radius==0 else 0)
                with self.assertRaisesRegex(ValueError,'page corners'):E.verify_headers(lambda name:b'',broken)

    def test_feedback_positive_synthetic_lifecycle_and_pixels(self):
        facts,blobs=feedback_fixture();result=E.verify_feedback(blobs.__getitem__,facts)
        self.assertEqual(result['confirmationChangedPixels'],96)
        self.assertEqual(result['nativeDownloadItems'],6)

    def test_copy_readback_rejects_early_expired_or_invisible_animation(self):
        for mode in ('early','expired','duration','paused','opacity'):
            facts,blobs=feedback_fixture();attempt=facts['capture']['copyAttempt']
            sample=attempt['barrier']['before'] if mode=='early' else attempt['after']
            animation=sample['badgeAnimations'][0]
            if mode=='early':animation['currentTime']=223.999
            if mode=='expired':animation['currentTime']=1064.001
            if mode=='duration':animation['timing']['duration']=1050
            if mode=='paused':animation['playState']='paused'
            if mode=='opacity':sample['badgeOpacity']='0.98'
            with self.assertRaisesRegex(ValueError,'visibility plateau|not fully visible',msg=mode):
                E.verify_feedback(blobs.__getitem__,facts)

    def test_copy_readback_rejects_replay_or_renderer_clock_reversal(self):
        for mode in ('replayed','new-renderer','animation-clock','sample-clock'):
            facts,blobs=feedback_fixture();after=facts['capture']['copyAttempt']['after']
            if mode=='replayed':after['badgeAnimations'][0]['startTime']+=1
            if mode=='new-renderer':after['timeOrigin']+=1
            if mode=='animation-clock':after['badgeAnimations'][0]['currentTime']=299
            if mode=='sample-clock':after['sampledAt']=799
            with self.assertRaisesRegex(ValueError,'different renderer, restarted animation or reversed clock',msg=mode):
                E.verify_feedback(blobs.__getitem__,facts)

    def test_copy_readback_rejects_native_observation_encoding_order(self):
        keys=('copyStartedAt','copyResolvedAt','requestedAt','receivedAt','afterSampledAt','encodedAt')
        for left,right in zip(keys,keys[1:]):
            facts,blobs=feedback_fixture();attempt=facts['capture']['copyAttempt']
            attempt[left]=attempt[right]+1
            with self.assertRaisesRegex(ValueError,'ran out of order',msg=left):
                E.verify_feedback(blobs.__getitem__,facts)

    def test_copy_readback_binds_the_same_png_feedback_and_badge_pixels(self):
        for mode in ('frame-hash','frame-file','frame-clock','feedback','pixel-count','pixel-region','badge-region'):
            facts,blobs=feedback_fixture();capture=facts['capture'];attempt=capture['copyAttempt']
            if mode=='frame-hash':attempt['frame']['sha256']='0'*64
            if mode=='frame-file':attempt['frame']['file']='mouse-unit-before.png'
            if mode=='frame-clock':
                attempt['frame']['receivedAt']+=1;capture['copied']['frame']['receivedAt']+=1
            if mode=='feedback':capture['copied']['feedback']['sampledAt']-=1
            if mode=='pixel-count':attempt['changedPixels']+=1
            if mode=='pixel-region':attempt['changedRegion']['width']-=1
            if mode=='badge-region':
                attempt['changedRegion']['x']-=1;capture['copied']['changedRegion']['x']-=1
            with self.assertRaisesRegex(ValueError,'not bound to the same|actually observed confirmation badge',msg=mode):
                E.verify_feedback(blobs.__getitem__,facts)

    def test_retry_terminal_counters_can_reset_without_erasing_prior_delivery(self):
        for received,total in ((0,1048576),(0,0),(0,-1),(57344,1048576)):
            facts,blobs=feedback_fixture()
            native=next(row for row in facts['downloads']['nativeEvents']
                        if row['activity']['id']=='broken' and row['event']=='done')
            sample=next(row for row in facts['downloads']['events'] if row['activity']['id']=='broken')
            native.update(received=received,total=total)
            native['activity'].update(received=received,total=max(0,total))
            sample['activity'].update(received=received,total=max(0,total))
            percent=received/total*100 if total>0 else None
            sample['task']['percent']=percent
            sample['ui']['pill'].update(ariaNow=None if percent is None else str(percent),
                value='…' if percent is None else str(int(percent+.5))+'%')
            self.assertEqual(E.verify_feedback(blobs.__getitem__,facts)['nativeDownloadItems'],6)

    def test_retry_rejects_missing_delivery_fake_terminal_or_counter_mismatch(self):
        for mode in ('no-native-bytes','not-done','cancelled','counter-mismatch','not-aborted',
                     'no-http-bytes','no-404','incomplete-200','retry-before-error'):
            facts,blobs=feedback_fixture();downloads=facts['downloads']
            terminal=next(row for row in downloads['nativeEvents']
                          if row['activity']['id']=='broken' and row['event']=='done')
            if mode=='no-native-bytes':
                for row in downloads['nativeEvents']:
                    if row['activity']['id']=='broken' and row['event']=='updated':
                        row['received']=row['activity']['received']=0
            if mode=='not-done':terminal['event']='updated'
            if mode=='cancelled':terminal['nativeState']='cancelled'
            if mode=='counter-mismatch':terminal['received']=terminal['activity']['received']=1
            if mode=='not-aborted':downloads['httpRequests'][0]['aborted']=False
            if mode=='no-http-bytes':downloads['httpRequests'][0]['sentBytes']=0
            if mode=='no-404':downloads['httpRequests'][1]['status']=200
            if mode=='incomplete-200':downloads['httpRequests'][-1]['sentBytes']=65536
            if mode=='retry-before-error':downloads['httpRequests'][-1]['at']=125
            with self.assertRaises(ValueError,msg=mode):E.verify_feedback(blobs.__getitem__,facts)

    def test_feedback_rejects_fabricated_progress_privacy_or_missing_native_event(self):
        for mode in ('percent','scope','native','retry'):
            facts,blobs=feedback_fixture()
            if mode=='percent':facts['downloads']['events'][0]['task']['percent']=100
            if mode=='scope':facts['privacy']['privateTasks'][0]['privateMode']=False
            if mode=='native':facts['downloads']['nativeEvents']=[e for e in facts['downloads']['nativeEvents'] if not(e['case']=='known' and e['event']=='done')]
            if mode=='retry':facts['downloads']['files'][1]['sha256']='0'*64
            with self.assertRaises(ValueError,msg=mode):E.verify_feedback(blobs.__getitem__,facts)

    def test_feedback_rejects_relabelled_png_false_pixel_count_and_export_contamination(self):
        for mode in ('png','count','saved','cancelled','reduced'):
            facts,blobs=feedback_fixture()
            if mode=='png':blobs['mouse-unit-feedback.png']=blobs['mouse-unit-before.png']
            if mode=='count':facts['capture']['copied']['changedPixels']=97
            if mode=='saved':blobs['mouse-unit-saved.png']=blobs['mouse-unit-feedback.png']
            if mode=='cancelled':facts['capture']['cancelled']['feedback']['state']='save'
            if mode=='reduced':facts['capture']['reducedMotion']['bladeDisplay']='block'
            with self.assertRaises(ValueError,msg=mode):E.verify_feedback(blobs.__getitem__,facts)

    def test_new_schema_keeps_all_unrelated_native_markers(self):
        self.assertEqual(len(E.JSON_NAMES),11)
        self.assertEqual(len(set(E.JSON_NAMES)),11)
        self.assertNotIn('mouse-628-swipe-tutorial.json',E.JSON_NAMES)
        self.assertIn(E.TUTORIAL_JSON_NAME,E.JSON_NAMES)
        self.assertIn(E.WHEEL_JSON_NAME,E.JSON_NAMES)
        self.assertIn(E.NORA_JSON_NAME,E.JSON_NAMES)
        self.assertIn(E.UI_JSON_NAME,E.JSON_NAMES)
        self.assertEqual(E.TUTORIAL_JSON_NAME,'mouse-629-swipe-tutorial.json')
        self.assertEqual(E.WHEEL_JSON_NAME,'mouse-630-wheel-pages.json')
        self.assertEqual(len(E.NATIVE_MARKERS),17)
        self.assertEqual(set(E.reviewed['NATIVE_MARKERS'])-set(E.NATIVE_MARKERS),E.SUPERSEDED_MARKERS)
        self.assertIn('MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_WRITE_PASS',E.NATIVE_MARKERS)
        self.assertIn('MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_NATIVE_PASS',E.NATIVE_MARKERS)

    def test_accepted_tutorial_requires_native_restart_and_real_input_lifecycle(self):
        facts,slides,blobs=tutorial_fixture()
        report=E.ui_reviewed['verify_gesture'](facts,blobs.__getitem__)
        self.assertEqual(report['nativeWheelSwitches'],4)
        self.assertFalse(report['physicalTrackpadVerified'])
        E.verify_nora_transitions(slides,facts)
        for mode in ('physical','restart','learned','input','route','zero-input','persisted','png'):
            bad=copy.deepcopy(facts);files=blobs.copy()
            if mode=='physical':bad['physicalTrackpadVerified']=True
            if mode=='restart':bad['restart']['pid']=bad['writePid']
            if mode=='learned':bad['records'][2]['gesture']['learned']=True
            if mode=='input':bad['records'][3]['observedInput']['isTrusted']=False
            if mode=='route':bad['records'][3]['dispatch']['packet']['source']='native-swipe'
            if mode=='zero-input':bad['records'][3]['nativeInput']['deltaX']=0
            if mode=='persisted':bad['restart']['persisted']={'completed':False}
            if mode=='png':files['mouse-629-swipe-restart.png']=b'not a png'
            with self.assertRaises(ValueError,msg=mode):E.ui_reviewed['verify_gesture'](bad,files.__getitem__)

    def test_transition_cannot_reuse_page_route_other_input_or_lose_native_scroll(self):
        facts,slides,_=tutorial_fixture()
        for mode in ('relabelled-schema','page-route','mismatched-input','scroll','missing-transition'):
            bad=copy.deepcopy(slides);tutorial=copy.deepcopy(facts)
            if mode=='relabelled-schema':bad['version']='6.0.31'
            if mode=='page-route':tutorial['records'][3]['dispatch']['packet']['source']='trusted-wheel'
            if mode=='mismatched-input':bad['transitions'][0]['after']['desktopId']='other'
            if mode=='scroll':bad['transitions'][0]['pageAfter'][0]['scrollY']=0
            if mode=='missing-transition':bad['transitions'].pop()
            with self.assertRaises(ValueError,msg=mode):E.verify_nora_transitions(bad,tutorial)

    def test_wheel_routes_preserve_page_scroll_and_private_scope(self):
        facts,blobs=wheel_fixture()
        report=E.verify_wheel_pages(blobs.__getitem__,facts)
        self.assertEqual(report['nativeDispatches'],3)
        for mode in ('source','untrusted','vertical','horizontal','extra-dispatch','duplicate','forged','private','owner','distance'):
            bad=copy.deepcopy(facts)
            if mode=='source':bad['source']='synthetic DOM wheel'
            if mode=='untrusted':bad['cases']['closedPage']['observed'][0]['isTrusted']=False
            if mode=='vertical':bad['cases']['verticalPage']['afterScrollY']=0
            if mode=='horizontal':bad['cases']['horizontalScroller']['afterScrollLeft']=0
            if mode=='extra-dispatch':bad['cases']['contentEditable']['packetCount']=1
            if mode=='duplicate':bad['cases']['duplicateBurst']['packetCount']=2
            if mode=='forged':bad['cases']['forgedDOM']['observed'][0]['isTrusted']=True
            if mode=='private':bad['privacy']['privateDisposed']['webContentsDestroyed']=False
            if mode=='owner':bad['packets'][2]['packet']['tabId']=bad['packets'][0]['packet']['tabId']
            if mode=='distance':bad['packets'][0]['packet']['gesture']['count']=3
            with self.assertRaises(ValueError,msg=mode):E.verify_wheel_pages(blobs.__getitem__,bad)

    def test_nora_foreground_decodes_actual_display_crop_and_root_identity(self):
        facts,blobs=nora_fixture()
        report=E.verify_nora_foreground(blobs.__getitem__,facts)
        self.assertEqual(report['nativeForegroundPixels'],21)
        self.assertEqual(report['nativeRootRepairs'],2)
        for mode in ('visible','root-order','retained-document','overlap','mapping','native-pixels','reversal','resize'):
            bad=copy.deepcopy(facts);files=blobs.copy()
            foreground=next(row for row in bad['rows'] if row['phase']=='open')
            if mode=='visible':foreground['native'][0]['view']=True
            if mode=='root-order':bad['rows'][0]['rootOrderAfter']=[100,2,1]
            if mode=='retained-document':bad['pagesAfter'][0]['timeOrigin']+=1
            if mode=='overlap':foreground['underlyingPage']['bounds']['height']=10
            if mode=='mapping':foreground['capture']['mapping']['originX']=1
            if mode=='native-pixels':
                files[foreground['capture']['capture']]=png(64,128,lambda x,y:(227,31,173,255))
            if mode=='reversal':bad['rows'][1]['frames'][1]['y']=bad['rows'][1]['frames'][0]['y']
            if mode=='resize':bad['resize']['closedAfterInvalidation']=False
            with self.assertRaises(ValueError,msg=mode):E.verify_nora_foreground(files.__getitem__,bad)

    def test_motion_fixtures_require_normal_media_and_restore_actual_preference(self):
        for before in (False,True):E.motion_media({'before':before,'normal':False,'restored':before},'synthetic')
        for value in (None,{}, {'before':True,'normal':True,'restored':True},
                      {'before':True,'normal':False,'restored':False},
                      {'before':1,'normal':False,'restored':1}):
            with self.assertRaises(ValueError):E.motion_media(value,'synthetic')
        facts,blobs=nora_fixture();facts['motionMedia']['normal']=True
        with self.assertRaisesRegex(ValueError,'normal-motion'):E.verify_nora_foreground(blobs.__getitem__,facts)
        for mode in ('normal-baseline','sample-media','global-restoration','global-reduced','shutter','media-cleanup'):
            facts,blobs=feedback_fixture()
            if mode=='normal-baseline':facts['capture']['motionMedia']['normal']=True
            if mode=='sample-media':facts['capture']['acquired']['reducedMotion']=True
            if mode=='global-restoration':facts['capture']['global']['motionMedia']['restored']=False
            if mode=='global-reduced':facts['capture']['global']['reducedMotion']['reducedMotion']=False
            if mode=='shutter':facts['capture']['copied']['feedback']['bladeAnimationName']='none'
            if mode=='media-cleanup':facts['motionCleanupError']={'message':'failed media restoration'}
            with self.assertRaises(ValueError,msg=mode):E.verify_feedback(blobs.__getitem__,facts)

    def test_nora_freshness_keeps_rejected_raw_frames_and_binds_final_pixels_and_native_hold(self):
        facts,blobs=nora_fixture();row=next(row for row in facts['rows'] if row['phase']=='open')
        add_nora_readiness(row,blobs,stale_first=True)
        self.assertEqual(E.verify_nora_readiness(blobs.__getitem__,row,'synthetic readiness'),2)
        self.assertEqual(E.verify_nora_foreground(blobs.__getitem__,facts)['nativeForegroundPixels'],21)
        for mode in ('sha','stale-accepted','claimed-match','native-visible','hold','root-order',
                     'time','timeout','missing-stage','final-bytes','foreground','flat-reference'):
            bad=copy.deepcopy(row);files=blobs.copy();proof=bad['readiness'];first=proof['attempts'][0]
            if mode=='sha':first['display']['sha256']='0'*64
            if mode=='stale-accepted':first['accepted']=True
            if mode=='claimed-match':first['regions'][0]['mismatched']=0
            if mode=='native-visible':proof['stability'][1]['native'][0]['view']=True
            if mode=='hold':proof['stability'][2]['holdId']='0'*64
            if mode=='root-order':proof['rootOrder'].reverse()
            if mode=='time':first['captureStartedAt']=first['readbackStartedAt']-1
            if mode=='timeout':proof['elapsedMs']=4000
            if mode=='missing-stage':proof['stability'].pop()
            if mode=='final-bytes':files[bad['capture']['source']]=files[first['display']['file']]
            if mode=='foreground':first['foregroundReady']=True
            if mode=='flat-reference':
                raw=png(64,128,lambda x,y:(240,242,246,255))
                files[first['shell']['file']]=raw;first['shell']['sha256']=sha(raw)
            with self.assertRaises(ValueError,msg=mode):E.verify_nora_readiness(files.__getitem__,bad,'synthetic readiness')

    def test_fractional_seven_panes_use_native_endpoint_rounding_and_real_pngs(self):
        self.assertEqual(E.native_endpoints({'x':517.4375,'y':0.5,'width':183.484375,'height':1}),
                         {'x':517,'y':1,'width':184,'height':1})
        facts,blobs=fractional_fixture();report=E.verify_fractional_layouts(blobs.__getitem__,facts)
        self.assertGreater(report['endpointRoundingDifferences'],0)
        self.assertEqual(report['frozenNativePngs'],7)
        self.assertEqual(report['frozenNativePixels'],21)
        self.assertEqual(report['nativeForegroundPixels'],3)

    def test_fractional_gate_rejects_old_rounding_missing_images_and_native_replacement(self):
        facts,blobs=fractional_fixture()
        for mode in ('old-rounding','integer-only','missing-image','wrong-pixels','recreated','root-order','visible','wrong-probe'):
            bad=copy.deepcopy(facts);files=blobs.copy();row=bad['fractionalLayouts'][0]
            if mode=='old-rounding':
                for phase in ('before','during','after'):
                    row[phase]['pages'][1]['bounds']['width']=int(row[phase]['slots'][1]['width']+.5)
            if mode=='integer-only':
                for phase in ('before','during','after'):
                    for page,slot in zip(row[phase]['pages'],row[phase]['slots']):slot.update(page['bounds'])
            if mode=='missing-image':row['snapshots'].pop()
            if mode=='wrong-pixels':
                snapshot=row['snapshots'][0];raw=png(snapshot['naturalWidth'],snapshot['naturalHeight'],lambda x,y:(255,255,255,255))
                files[snapshot['file']]=raw;snapshot['sha256']=sha(raw)
            if mode=='recreated':
                for phase in ('before','during','after'):row[phase]['pages'][0]['timeOrigin']+=10
            if mode=='root-order':row['after']['rootOrder'].reverse()
            if mode=='visible':row['native'][0]['view']=True
            if mode=='wrong-probe':row['samples'][0]['pageId']=row['before']['pages'][-1]['id']
            with self.assertRaises(ValueError,msg=mode):E.verify_fractional_layouts(files.__getitem__,bad)

    def test_archived_reader_rejects_path_escape_and_oversized_bytes(self):
        with self.assertRaises(ValueError):E.bounded_reader(lambda name:b'{}')('../mouse-escape.json')
        with self.assertRaises(ValueError):E.bounded_reader(lambda name:b'x'*(16*1024**2+1))('mouse-large.png')


if __name__=='__main__':
    unittest.main()
