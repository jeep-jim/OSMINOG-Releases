#!/usr/bin/env python3
"""Synthetic parser fixtures only; these images never represent native results."""
import copy
import json
import math
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
E = runpy.run_path(str(ROOT/'mouse633-workspace-evidence.py'))
HELP = runpy.run_path(str(ROOT/'test-mouse633-ui-evidence.py'))
LINE = {'light':[199,207,223], 'dark':[67,83,107]}
PANEL = {'light':[255,255,255], 'dark':[25,33,46]}
COLORS = [[171,43,158],[24,117,150],[158,75,32],[75,89,158],[35,130,77],[143,52,86],[83,100,41]]


def geometry(width, height, ai=False, fractional=False):
    stage_width = width-146 if ai else width
    stage_height = height-80
    result = {'viewport':{'width':width,'height':height},'toolbar':{'x':0,'y':0,'width':width,'height':40},
              'footer':{'x':0,'y':height-28,'width':width,'height':28},
              'workspace':{'x':0,'y':40,'width':width,'height':height-68},
              'stage':{'x':0,'y':46,'width':stage_width,'height':stage_height},
              'padding':{'top':6,'right':0,'bottom':6,'left':0},'panes':[],
              'dividers':[],'ai':None}
    pane_height = (stage_height-6)/2
    result['dividers'].append({'axis':'y','bounds':{'x':0,'y':46+pane_height,'width':stage_width,'height':6}})
    for row, count in ((0,4),(1,3)):
        pane_width = (stage_width-6*(count-1))/count
        y = 46+row*(pane_height+6)
        for i in range(count):
            x = i*(pane_width+6)
            result['panes'].append({'id':'page-'+str(len(result['panes'])),
                'bounds':{'x':x,'y':y,'width':pane_width,'height':pane_height},
                'slot':{'x':x,'y':y+28,'width':pane_width,'height':pane_height-28},
                'radii':[12]*4,'roundTop':12,'roundBottom':12})
            if i<count-1: result['dividers'].append({'axis':'x','bounds':{'x':x+pane_width,'y':y,'width':6,'height':pane_height}})
    if fractional:
        # A legitimate fractional split creates distinct CSS samples that
        # share a physical pixel at 1x. Keep the adjacent panes and gap joined.
        a,b=result['panes'][:2]
        shift=(math.floor(b['bounds']['x'])+.375)-b['bounds']['x']
        for key in ('bounds','slot'):
            a[key]['width']+=shift
            b[key]['x']+=shift
            b[key]['width']-=shift
        next(d for d in result['dividers'] if d['axis']=='x')['bounds']['x']+=shift
    if ai:
        result['ai']={'id':'ai','bounds':{'x':width-140,'y':46,'width':140,'height':stage_height},
                      'slot':{'x':width-140,'y':74,'width':140,'height':stage_height-28},'radii':[12]*4,
                      'divider':{'x':stage_width,'y':46,'width':6,'height':stage_height}}
    return result


def native(geometry):
    rows=[]
    for i,pane in enumerate(geometry['panes']+([geometry['ai']] if geometry['ai'] else [])):
        r=pane['slot'];rnd=lambda v:math.floor(v+.5)
        bounds={'x':rnd(r['x']),'y':rnd(r['y']),'width':rnd(r['x']+r['width'])-rnd(r['x']),
                'height':rnd(r['y']+r['height'])-rnd(r['y'])}
        rows.append({'id':pane['id'],'webContentsId':i+100,'bounds':bounds,'actualBounds':dict(bounds),
                     'visible':True,'viewVisible':True,'parentVisible':True,'attached':True})
    return rows


def identities(rows):
    return [{'id':p['id'],'webContentsId':p['webContentsId'],'url':'http://127.0.0.1:43125/'+str(i),
             'epoch':1,'timeOrigin':1000+i,'identity':.1+i/100,'field':'retained-'+str(i),
             'bounds':dict(p['bounds']),'clip':None,'width':p['bounds']['width'],'height':p['bounds']['height'],
             'scrollX':0,'scrollY':0} for i,p in enumerate(rows[:7])]


def points(geometry, theme, rows):
    out=[];w=geometry['workspace'];right=lambda r:r['x']+r['width'];bottom=lambda r:r['y']+r['height']
    for edge in ('top','bottom'):
        for fraction in (.2,.5,.8):out.append({'kind':'workspace-gap','edge':edge,'point':{'x':w['width']*fraction,'y':43 if edge=='top' else bottom(w)-3},'expected':LINE[theme]})
    for pane in geometry['panes']+([geometry['ai']] if geometry['ai'] else []):
        r=pane['bounds']
        for side in ('left','right'):
            for u in (.65,1.6,3):
                for v in (.65,1.6,3):
                    if math.hypot(12-u,12-v)>13.5:out.append({'kind':'pane-top-cutout','id':pane['id'],'side':side,'paneBounds':dict(r),'point':{'x':r['x']+u if side=='left' else right(r)-u,'y':r['y']+v},'expected':LINE[theme]})
            out.append({'kind':'pane-top-interior','id':pane['id'],'side':side,'paneBounds':dict(r),'point':{'x':math.ceil(r['x']+12)+.5 if side=='left' else math.floor(right(r)-12)-.5,'y':math.ceil(r['y'])+.5},'expected':PANEL[theme]})
    if geometry['ai']:
        r=rows[-1]['bounds']
        for side in ('left','right'):
            for u in (.65,1.6,3):
                for v in (.65,1.6,3):
                    if math.hypot(12-u,12-v)>13.5:out.append({'kind':'ai-bottom-cutout','id':'ai','side':side,'guestBounds':dict(r),'point':{'x':r['x']+u if side=='left' else right(r)-u,'y':bottom(r)-v},'expected':LINE[theme]})
            out.append({'kind':'ai-bottom-interior','id':'ai','side':side,'guestBounds':dict(r),'point':{'x':r['x']+20 if side=='left' else right(r)-20,'y':bottom(r)-3},'expected':[211,92,53]})
    return out


def bottom_points(geometry, rows, theme):
    probes=[]
    for divider in geometry['dividers']:
        r=divider['bounds']
        for fraction in (.2,.5,.8):probes.append({'kind':'divider','point':{'x':r['x']+r['width']*(fraction if divider['axis']=='y' else .5),'y':r['y']+r['height']*(fraction if divider['axis']=='x' else .5)},'expected':LINE[theme]})
    for i,page in enumerate(rows):
        r=page['bounds']
        for side in ('left','right'):
            for u in (.65,1.6,3):
                for v in (.65,1.6,3):
                    if math.hypot(12-u,12-v)>13.5:probes.append({'kind':'corner-cutout','id':page['id'],'side':side,'guestBounds':dict(r),'point':{'x':r['x']+u if side=='left' else r['x']+r['width']-u,'y':r['y']+r['height']-v},'expected':LINE[theme]})
            probes.append({'kind':'page-interior','id':page['id'],'side':side,'guestBounds':dict(r),'point':{'x':r['x']+20 if side=='left' else r['x']+r['width']-20,'y':r['y']+r['height']-3},'expected':COLORS[i]})
    return probes


def fixture(platform='darwin', fractional=False):
    images={};facts={'version':'6.0.33','baselineVersion':'6.0.27','platform':platform,'arch':'arm64' if platform=='darwin' else 'x64',
                     'paneCount':7,'restored':True,'separators':[],'workspace633':{'schema':1,'gap':6,'radius':12,'aiScenes':[]}}
    for theme in ('light','dark'):
        for variant,width,height in (('initial',480,360),('resized',443,337)):
            g=geometry(width,height,fractional=fractional);rows=native(g);current={'geometry':g,'nativePanels':rows,'identityBefore':identities(rows),'identityAfter':identities(rows),'probes':points(g,theme,rows)}
            old=bottom_points(g,rows,theme);capture=HELP['native_fixture_capture'](images,'mouse-synthetic-'+theme+'-'+variant,g['viewport'],LINE[theme],old+current['probes'])
            facts['separators'].append({'theme':theme,'variant':variant,'expectedHex':'#c7cfdf' if theme=='light' else '#43536b','expectedRGB':LINE[theme],
                'actualToken':'#c7cfdf' if theme=='light' else '#43536b','stageColor':LINE[theme],'dividerColors':[LINE[theme]]*6,'paneCount':7,
                'viewport':g['viewport'],'nativePanels':[{'id':p['id'],'bounds':p['bounds']} for p in rows],'probes':old,'nativeCapture':capture,'workspace633':current})
        g=geometry(443,337,True,fractional);rows=native(g);before=identities(native(geometry(443,337,fractional=fractional)));probes=points(g,theme,rows)
        capture=HELP['native_fixture_capture'](images,'mouse-synthetic-ai-'+theme,g['viewport'],LINE[theme],probes)
        ai_identity={'id':'ai','webContentsId':107,'url':'http://127.0.0.1:43125/ai','timeOrigin':2000,'identity':.2,'field':'retained-7'}
        row={'theme':theme,'variant':'ai','geometry':g,'nativePanels':rows,'identityBefore':identities(rows),'identityAfter':identities(rows),'probes':probes,'nativeCapture':capture,
             'beforePages':before,'afterPages':copy.deepcopy(before),'closed':True,'restored':True,'url':ai_identity['url'],'aiIdentityBefore':ai_identity,'aiIdentityAfter':dict(ai_identity),
             'windowBefore':capture['contentBounds'],'windowAfter':dict(capture['contentBounds']),'input':[]}
        for page,side in ((rows[0],'right'),(rows[-1],'left')):
            b=page['bounds'];point={'x':20+b['x']+(2 if side=='left' else b['width']-2),'y':30+b['y']+b['height']-2};client={'x':point['x']-20-b['x'],'y':point['y']-30-b['y']}
            row['input'].append({'id':page['id'],'webContentsId':page['webContentsId'],'side':side,'source':{'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform],
                'point':point,'contentBounds':dict(capture['contentBounds']),'guestBounds':dict(b),'factor':1,'expectedClient':client,'event':{**client,'trusted':True,'at':100}})
        facts['workspace633']['aiScenes'].append(row)
    if platform=='linux':
        for row in facts['separators']+facts['workspace633']['aiScenes']:
            capture=row['nativeCapture'];count=8 if row['variant']=='ai' else 7
            state={'backend':'X11 Shape','supported':True,'ownedParent':True,'reason':'ready','error':0,'queryError':0,
                   'paneCount':count,'cornerCount':count*2,'scaleX':1,'scaleY':1,'logicalWidth':capture['contentBounds']['width'],'logicalHeight':capture['contentBounds']['height'],
                   'corners':[{'window':i+1,'exists':True,'mapped':True,'overrideRedirect':True,'inputRectangles':0} for i in range(count*2)]}
            capture['nativePaneCorners']={'before':{'native':copy.deepcopy(state)},'after':{'native':copy.deepcopy(state)}}
    return images,facts


class WorkspaceEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.original_images,cls.original=fixture()
    def setUp(self): self.images=dict(self.original_images);self.facts=copy.deepcopy(self.original)
    def verify(self,platform='darwin'):
        files={**self.images,'mouse-629-ui-regressions.json':json.dumps(self.facts).encode()}
        return E['verify'](files.__getitem__,expected_platform=platform,expected_arch='arm64' if platform=='darwin' else 'x64')
    def test_all_three_platforms_accept_complete_synthetic_geometry_and_real_format_png_bindings(self):
        for platform in ('darwin','win32','linux'):
            self.images,self.facts=fixture(platform);result=self.verify(platform)
            self.assertEqual(result['scenes'],6);self.assertEqual(result['nativeCornerInputs'],4);self.assertGreater(result['decodedPixelProbes'],600)
    def test_missing_supplement_or_theme_is_rejected(self):
        for mutate in (lambda f:f.pop('workspace633'),lambda f:f['workspace633']['aiScenes'].pop(),lambda f:f['separators'].pop()):
            self.setUp();mutate(self.facts)
            with self.assertRaises(ValueError):self.verify()
    def test_distinct_fractional_css_points_may_share_a_pixel_without_losing_raw_colour_checks(self):
        self.images,self.facts=fixture('win32',fractional=True)
        probes=self.facts['separators'][0]['workspace633']['probes']
        self.assertLess(len({(p['x'],p['y']) for p in probes}),len(probes))
        self.assertEqual(len({(p['point']['x'],p['point']['y']) for p in probes}),len(probes))
        self.assertTrue(self.verify('win32')['ok'])
        probes[7]['point']=dict(probes[6]['point'])
        with self.assertRaisesRegex(ValueError,'sample location'):self.verify('win32')
    def test_old_external_corners_gutters_and_incorrect_gap_are_rejected(self):
        for mutate in (lambda g:g['padding'].update(top=0),lambda g:g['padding'].update(left=6),lambda g:g['stage'].update(x=1),
                       lambda g:g['panes'][0].update(radii=[0,0,12,12]),lambda g:g['dividers'][0]['bounds'].update(height=5)):
            self.setUp();mutate(self.facts['separators'][0]['workspace633']['geometry'])
            with self.assertRaises(ValueError):self.verify()
    def test_measured_outer_css_quantization_keeps_exact_native_edges_and_rejects_real_gaps(self):
        def inset_right(g,amount):
            for pane in g['panes']:
                if abs(pane['bounds']['x']+pane['bounds']['width']-g['stage']['width'])<1e-6:
                    for key in ('bounds','slot'):pane[key]['width']-=amount
        actual=geometry(1443,917);inset_right(actual,1/32)
        for key in ('bounds','slot'):actual['panes'][-1][key].update(x=1048.046875,width=394.921875)
        panes=E['geometry'](actual,False);views=native(actual)
        checked=E['native_panels']({'nativePanels':views},panes)
        self.assertEqual(checked['page-6']['bounds']['x']+checked['page-6']['bounds']['width'],1443)
        for width,inset in ((1443,1),(1443.5,1/32)):
            bad=geometry(width,917);inset_right(bad,inset)
            with self.subTest(width=width,inset=inset),self.assertRaisesRegex(ValueError,'stage edge'):
                E['geometry'](bad,False)
    def test_top_interior_pixel_is_wholly_inside_the_straight_header_span_at_1x_and_2x(self):
        for fraction in (0,1/64,.046875,.375,.609375,.96875):
            g=geometry(1443,917);b={'x':767+fraction,'y':46+fraction,'width':274.4375,'height':565.078125};g['panes'][0]['bounds']=b
            samples=[p for p in E['expected_points'](g,'light',{}) if p.get('id')=='page-0' and p['kind']=='pane-top-interior']
            for sample in samples:
                for scale in (1,2):
                    x=math.floor(sample['point']['x']*scale)/scale;y=math.floor(sample['point']['y']*scale)/scale
                    self.assertGreaterEqual(x,b['x']+12);self.assertLessEqual(x+1/scale,b['x']+b['width']-12)
                    self.assertGreaterEqual(y,b['y']);self.assertLess(sample['point']['y'],b['y']+2)
        g=geometry(1443,917);g['panes'][0]['bounds']={'x':767.609375,'y':46,'width':274.4375,'height':565.078125}
        measured=next(p for p in E['expected_points'](g,'light',{}) if p.get('id')=='page-0' and p['kind']=='pane-top-interior' and p['side']=='right')
        self.assertEqual(measured['point'],{'x':1029.5,'y':46.5})
    def test_actual_view_and_identity_substitution_is_rejected(self):
        for mutate in (lambda r:r['nativePanels'][0].update(attached=False),lambda r:r['nativePanels'][0]['actualBounds'].update(width=1),
                       lambda r:r['identityAfter'][0].update(webContentsId=999),lambda r:r['identityAfter'][0].update(identity=.99)):
            self.setUp();mutate(self.facts['separators'][0]['workspace633'])
            with self.assertRaises(ValueError):self.verify()
    def test_missing_relabelled_or_self_reported_pixels_do_not_pass(self):
        for mutate in (lambda p:p.pop(),lambda p:p[0].update(rgba=[1,2,3,255]),lambda p:p[0].update(expected=[1,2,3]),lambda p:p[6].update(id='different')):
            self.setUp();mutate(self.facts['separators'][0]['workspace633']['probes'])
            with self.assertRaises(ValueError):self.verify()
    def test_changed_archived_pixels_fail_even_when_reported_rgba_matches_them(self):
        row=self.facts['separators'][0];probe=row['workspace633']['probes'][0];probe['rgba']=[1,2,3,255]
        decoder=runpy.run_path(str(ROOT/'mouse633-task-evidence.py'))['decode_png']
        for filename,x,y in ((row['nativeCapture']['capture'],probe['x'],probe['y']),
                             (row['nativeCapture']['screenCapture'],probe['x']+20,probe['y']+30)):
            decoded=decoder(self.images[filename],filename);pixels=bytearray(decoded['pixels']);at=(y*decoded['width']+x)*4;pixels[at:at+4]=bytes(probe['rgba']);self.images[filename]=HELP['png'](decoded['width'],decoded['height'],pixels)
        with self.assertRaisesRegex(ValueError,'expected colour'):self.verify()
    def test_ai_square_bottom_missing_scene_or_unrestored_page_fails(self):
        for mutate in (lambda r:r['geometry']['ai'].update(radii=[12,12,0,0]),lambda r:r.update(closed=False),
                       lambda r:r['afterPages'][0].update(field='lost'),lambda r:r['aiIdentityAfter'].update(timeOrigin=9999)):
            self.setUp();mutate(self.facts['workspace633']['aiScenes'][0])
            with self.assertRaises(ValueError):self.verify()
    def test_native_inputs_must_be_trusted_and_cross_the_internal_painted_corner(self):
        for mutate in (lambda i:i['event'].update(trusted=False),lambda i:i.update(side='left'),lambda i:i['point'].update(x=i['point']['x']-10),
                       lambda i:i.update(webContentsId=999),lambda i:i['event'].update(y=1)):
            self.setUp();mutate(self.facts['workspace633']['aiScenes'][0]['input'][0])
            with self.assertRaises(ValueError):self.verify()
    def test_x11_actual_input_shape_and_owned_mapped_window_query_are_required(self):
        for mutate in (lambda s:s.update(ownedParent=False),lambda s:s.update(queryError=1),lambda s:s['corners'][0].update(inputRectangles=1),
                       lambda s:s['corners'][0].update(mapped=False),lambda s:s.update(cornerCount=0)):
            self.images,self.facts=fixture('linux');mutate(self.facts['separators'][0]['nativeCapture']['nativePaneCorners']['after']['native'])
            with self.assertRaises(ValueError):self.verify('linux')


if __name__=='__main__':unittest.main()
