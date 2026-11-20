"""Synthetic contract inputs only; these tests are not native release evidence.

Run the complete independent 632 verifier without mocks. The accepted 631
owned-page and capture fixture builders are reused with 632 screenshot names.
All bytes stay in memory; no fixture is published as an application result.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load('mouse632_feedback_contract', 'mouse632-feedback-evidence.py')
FIXTURE = load('accepted631_owned_fixture', 'test_mouse631_task_evidence.py')


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def solid_png(width, height, rgba=(238, 238, 238, 255)):
    """Small compressed parser fixture, never an observed app screenshot."""
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + bytes(rgba) * width) * height)) + chunk(b'IEND', b''))


def scope(budget):
    return {'version':'6.0.32', 'platform':'win32', 'arch':'x64', 'ok':True,
            'restored':True, 'budgetMs':budget, 'elapsedMs':budget/2,
            'cleanup':{'restored':True, 'desktopStateRestored':True}}


def typed(value):
    return {'before':value, 'after':value, 'nativeInputSource':'native pointer click + webContents.insertText'}


def fixtures():
    files = {}
    pages = [FIXTURE.owned(index) for index in range(4)]
    media = {**scope(55000), 'physicalMediaKeysVerified':False, 'externalMusicAccountVerified':False,
             'requests':{'pages':4, 'media':4}, 'scenarios':[], 'captures':[]}
    for theme in ('light', 'dark'):
        media['captures'].append({'theme':theme, **FIXTURE.capture(files, 'mouse-632-media-'+theme+'.png', pages)})
    native = media['captures'][0]['native']
    track = 0
    for index, (name, source) in enumerate([
            ('native site next-button', 'site-button'),
            ('automatic audio ended', 'automatic-ended'),
            ('registered MediaSession nexttrack callback', 'media-session-handler'),
            ('repeated title and media metadata burst', 'metadata-burst')]):
        before = copy.deepcopy(pages)
        pages = [{**page, 'ticks':page['ticks']+1} for page in pages]
        following = track + (20 if index == 3 else 1)
        media['scenarios'].append({'name':name, 'source':source,
            'mediaBefore':{'track':track, 'paused':False}, 'mediaAfter':{'track':following, 'paused':False},
            'titleEvents':1, 'operations':[], 'nativeBefore':copy.deepcopy(native), 'nativeAfter':copy.deepcopy(native),
            'identitiesBefore':before, 'identitiesAfter':copy.deepcopy(pages),
            'mutations':[{'pane':'p1', 'type':'characterData', 'attribute':None, 'tag':'#text'}],
            'typingFocused':None if index == 0 else True})
        track = following

    documents = {**scope(120000), 'physicalUserDeviceVerified':False,
        'entry':{'nora':True, 'settings':True, 'nativePicker':True, 'cancelPreserved':True,
                 'pickerSelection':'owned test dialog response'},
        'formats':['pdf', 'docx', 'xlsx', 'txt', 'md', 'csv', 'tsv', 'json'],
        'pdf':dict.fromkeys(('workerOffMainThread', 'canvasPainted', 'textSelected', 'pageNavigation',
                             'zoom', 'viewRotation', 'readOnly'), True),
        'docx':{**dict.fromkeys(('text', 'table', 'image', 'readOnly', 'typingBlocked'), True),
                'typing':typed('Mouse625 body original\nMouse625 table retained')},
        'xlsx':{**dict.fromkeys(('cells', 'formulaVisible', 'sheetNavigation', 'readOnly', 'typingBlocked'), True),
                'typing':typed('=SUM(A1,A2)'), 'secondSheet':'Second sheet retained'},
        'text':[{'extension':extension, 'readOnly':True, 'typingBlocked':True, 'typing':typed('synthetic '+extension+' original')}
                for extension in ('txt', 'md', 'csv', 'tsv', 'json')],
        'guards':{**dict.fromkeys(('draftRejected', 'saveRejected', 'noSaveDialogs', 'noUnsavedPrompts', 'originalHashesUnchanged'), True),
                  'dialogCalls':{'save':0, 'message':0}, 'originalFiles':[], 'rejections':[]},
        'privacy':{'normalIdsCleared':True, 'privateIdCleared':True, 'privateTextAbsentFromProfile':True,
                   'documentsAfter':0, 'normalProfileContainsPrivateText':False, 'normalProfileContainsPrivateId':False},
        'browser':{'layoutPreserved':True, 'pageIdentityPreserved':True,
                   'before':copy.deepcopy(pages[:2]), 'after':copy.deepcopy(pages[:2])}, 'captures':[]}
    documents['pdf']['selection'] = 'Mouse632 PDF page one'
    for name, page, width, height, rotation in [('first',1,360,240,0), ('second',2,360,240,0),
                                             ('zoomed',1,450,300,0), ('rotated',1,300,450,90)]:
        documents['pdf'][name] = {'workerOffMainThread':True, 'dark':240, 'width':width, 'height':height,
                                 'text':'Mouse632 PDF page '+('one' if page == 1 else 'two'),
                                 'view':{'page':page, 'rotation':rotation}}
    ids = ['doc-'+extension for extension in ('pdf', 'docx', 'xlsx', 'txt', 'md', 'csv', 'tsv', 'json', 'private')]
    for index, doc_id in enumerate(ids):
        kind = ('pdf', 'docx', 'xlsx')[index] if index < 3 else 'text'
        original_hash = digest(('owned unit document '+doc_id).encode())
        documents['guards']['originalFiles'].append({'name':doc_id, 'beforeSHA256':original_hash, 'afterSHA256':original_hash})
        for action in ('draft', 'save'):
            documents['guards']['rejections'].append({'id':doc_id, 'kind':kind, 'action':action,
                'native':{'rejected':True, 'code':'MOUSE_DOCUMENT_READ_ONLY'},
                'ipc':{'rejected':True, 'message':'Документ открыт только для просмотра'}})
    documents['twoPanes'] = {'ordinaryTabs':True, 'noExtraWebContents':True, 'simultaneous':True,
        'resizePreserved':True, 'nodeCount':2, 'documentIds':ids[1:3],
        'webContentsCountBefore':3, 'webContentsCountAfter':3,
        'webContentsIdsBefore':[7,100,101], 'webContentsIdsAfter':[7,100,101],
        'beforeBounds':[{'id':ids[1], 'x':0,'y':0,'width':100,'height':200},
                        {'id':ids[2], 'x':106,'y':0,'width':200,'height':200}],
        'afterBounds':[{'id':ids[1], 'x':0,'y':0,'width':148,'height':200},
                       {'id':ids[2], 'x':154,'y':0,'width':152,'height':200}]}
    for kind, theme in [(kind, theme) for kind in ('pdf','docx','xlsx','text') for theme in ('light','dark')] + [('two-panes','dark')]:
        name = 'mouse-632-documents-'+kind+'-'+theme+'.png'
        files[name] = solid_png(320,240)
        documents['captures'].append({'filename':name, 'sha256':digest(files[name]), 'kind':kind, 'theme':theme,
            'pixelSize':{'width':320, 'height':240}, 'bounds':{'x':10,'y':10,'width':300,'height':200},
            'source':'BrowserWindow.capturePage (shell document viewer)'})

    footer = {'version':'6.0.32', 'platform':'win32', 'arch':'x64',
        **dict.fromkeys(('screenshotOrder', 'balancedIconBoxes', 'groupsSeparated', 'narrowWindowFits',
                        'centerBurrowRetained', 'documentsInMenu'), True), 'cases':[],
        'websiteOffer':{'cancelledWithoutNavigation':True, 'settingsDistinct':True, 'confirmedAsNewTab':True,
                        'existingTabsPreserved':True, 'confirmedUrl':'https://mouse.black'},
        'manualHelper':dict.fromkeys(('singleEntry', 'noStartPromo', 'noProviderPromotion', 'openedExplicitly',
            'disabledUntilEnabled', 'closed', 'pagesPreserved', 'layoutPreserved', 'autoRestoreDisabled'), True)}
    for theme in ('light','dark'):
        for width in (800,1100,1440):
            controls = {'left':['website','theme','privacy','screenshot'],
                'right':['ai-toggle','version-button','language-select','quit'],
                'brand':{'width':19,'height':17}, 'source':'mouse-head-smooth.svg',
                'footerSettings':0,'footerDocuments':0,'footerFullscreen':0,'documentMenu':True,
                'groupGap':4,'groupSpace':8,'leftBox':{'right':200},
                'nora':{'x':width/2-18,'right':width/2+18},'rightBox':{'x':width/2+40},
                'icons':[{'icon':{'x':index*30+6.5,'y':6.5,'width':15,'height':15},
                          'button':{'x':index*30,'y':0,'width':28,'height':28}} for index in range(6)]}
            footer['cases'].append({'theme':theme,'width':width,'count':5,
                'actions':['emoji','zoom','history','bookmarks','downloads'], 'duplicate':False,
                'overflow':0,'gap':120,'space':20,'right':width-10,'controls':controls})
            files['mouse-632-footer-'+theme+'-'+str(width)+'.png'] = solid_png(width,500)
    return files, dict(zip(CHECK.JSON_NAMES, (media, documents, footer)))


class FeedbackContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_files, cls.original = fixtures()

    def setUp(self):
        self.files = dict(self.original_files)
        self.facts = copy.deepcopy(self.original)
        self.media, self.documents, self.footer = (self.facts[name] for name in CHECK.JSON_NAMES)

    def verify(self, platform='win32', arch='x64'):
        files = {**self.files, **{name:json.dumps(facts, allow_nan=False).encode() for name, facts in self.facts.items()}}
        return CHECK.verify(files.__getitem__, expected_platform=platform, expected_arch=arch)

    def reject(self, expression=None):
        with self.assertRaisesRegex(ValueError, expression) if expression else self.assertRaises(ValueError):
            self.verify()

    def test_complete_synthetic_contract_passes_on_both_supported_targets(self):
        for platform, arch in [('win32','x64'),('darwin','arm64')]:
            for value in self.facts.values():
                value.update(platform=platform, arch=arch)
            for row in self.footer['cases']:
                row['controls']['source'] = 'mouse-head-smooth.svg' if platform == 'win32' else 'mouse-head.svg'
            result = self.verify(platform, arch)
            self.assertTrue(result['ok'])
            self.assertEqual(result['media']['scenarios'],4)
            self.assertEqual(result['documents']['unchangedOriginalFiles'],9)
            self.assertEqual(result['documents']['writeRejections'],18)
            self.assertEqual(len(result['footer']['captures']),6)
            self.assertFalse(result['media']['physicalMediaKeysVerified'])
            self.assertEqual(result['inputs'], {name:digest(json.dumps(value, allow_nan=False).encode()) for name,value in self.facts.items()})

    def test_requested_target_and_each_document_runtime_are_bound(self):
        with self.assertRaisesRegex(ValueError,'requested target'):
            self.verify('darwin','arm64')
        for name in CHECK.JSON_NAMES:
            self.setUp();self.facts[name]['version']='6.0.31'
            self.reject('runtime')

    def test_cleanup_failure_and_unverified_hardware_claims_are_rejected(self):
        for name, key in [('media','physicalMediaKeysVerified'),('media','externalMusicAccountVerified'),('documents','physicalUserDeviceVerified')]:
            self.setUp();getattr(self,name)[key]=True
            self.reject()
        for name in ('media','documents'):
            self.setUp();getattr(self,name)['cleanup']['desktopStateRestored']=False
            self.reject('cleanup')

    def test_each_native_stage_must_finish_within_its_declared_budget(self):
        for target, maximum in [('media',55000),('documents',120000)]:
            self.setUp();getattr(self,target)['elapsedMs']=maximum+1;self.reject('budget')

    def test_oversized_json_is_refused_before_parsing(self):
        files={**self.files, **{name:json.dumps(value).encode() for name,value in self.facts.items()}}
        files[CHECK.JSON_NAMES[0]]=b' '*(4*1024**2+1)
        with self.assertRaisesRegex(ValueError,'missing or oversized'):
            CHECK.verify(files.__getitem__,expected_platform='win32',expected_arch='x64')

    def test_media_requires_every_real_input_route_and_focus(self):
        self.media['scenarios'][2]['source']='site-button';self.reject('input paths')
        self.setUp();self.media['scenarios'][1]['typingFocused']=False;self.reject('input focus')

    def test_playback_and_page_titles_must_really_advance(self):
        for field,value in [('track',0),('paused',True)]:
            self.setUp();self.media['scenarios'][0]['mediaAfter'][field]=value;self.reject()
        self.setUp();self.media['scenarios'][0]['titleEvents']=0;self.reject('title event')

    def test_track_switch_cannot_call_layout_capture_or_hide_views(self):
        self.media['scenarios'][0]['operations']=[{'method':'setBounds'}];self.reject('native view geometry')
        self.setUp();self.media['scenarios'][0]['nativeAfter'][0]['bounds']['width']+=1;self.reject('native view')

    def test_stationary_media_native_views_need_complete_owned_visible_geometry(self):
        for invalid in [None, {'visible':False}, {'tabId':'foreign'}]:
            self.setUp()
            for key in ('nativeBefore','nativeAfter'):
                self.media['scenarios'][0][key][0]=invalid
            self.reject()
        for flag in ('visible','parentVisible','cachedVisible','attached'):
            self.setUp()
            for key in ('nativeBefore','nativeAfter'):
                self.media['scenarios'][0][key][0][flag]=False
            self.reject()

    def test_stationary_native_ownership_and_hierarchy_are_checked_even_when_equal(self):
        for field,value in [('webContentsId',999),('desk','foreign-desk'),('index',99)]:
            self.setUp()
            for key in ('nativeBefore','nativeAfter'):
                self.media['scenarios'][0][key][0][field]=value
            self.reject('different page')
        self.setUp()
        for key in ('nativeBefore','nativeAfter'):
            for rectangle in ('bounds','viewBounds','actualBounds'):
                self.media['scenarios'][0][key][0][rectangle]['width']=0
        self.reject('rectangle')
        self.setUp()
        for key in ('nativeBefore','nativeAfter'):
            self.media['scenarios'][0][key][0]['viewBounds']['x']+=10
        self.reject('hierarchy')

    def test_titles_cannot_mutate_other_panes_or_reload_live_documents(self):
        self.media['scenarios'][0]['mutations'].append({'pane':'p2'});self.reject('unrelated pane')
        self.setUp();self.media['scenarios'][0]['identitiesAfter'][1]['timeOrigin']+=1;self.reject('live page')
        self.setUp();self.media['requests']['pages']=5;self.reject('reloaded a document')

    def test_media_os_display_crop_and_png_hashes_cannot_be_relabelled(self):
        self.media['captures'][0]['source']='BrowserWindow.capturePage';self.reject('actual OS display')
        self.setUp();self.media['captures'][0]['mapping']['scaleX']=2;self.reject('DPI')
        self.setUp();self.media['captures'][0]['sha256']='0'*64;self.reject('checksum')

    def test_rehashed_fake_pixels_still_fail_owned_content_probes(self):
        captured=self.media['captures'][0];probe=captured['probes'][0]
        image=CHECK.T.decode_png(self.files[captured['filename']]);pixels=image['pixels']
        at=(probe['y']*image['width']+probe['x'])*4;pixels[at:at+4]=b'\0\0\0\xff'
        blob=FIXTURE.png(image['width'],image['height'],pixels)
        for name in (captured['filename'],captured['displayFilename']):self.files[name]=blob
        captured['sha256']=captured['displaySha256']=digest(blob);probe['actualRGBA']=[0,0,0,255]
        self.reject('actual OS pixels')

    def test_pdf_success_flags_require_raw_canvas_worker_and_text_witnesses(self):
        for field,value in [('dark',0),('workerOffMainThread',False),('text','blank')]:
            self.setUp();self.documents['pdf']['first'][field]=value;self.reject('PDF')
        self.setUp();self.documents['pdf']['selection']='';self.reject('selection')
        self.setUp();self.documents['pdf']['second']['view']['page']=1;self.reject('page content')

    def test_pdf_zoom_rotation_and_each_theme_capture_are_required(self):
        self.documents['pdf']['zoomed']['width']=360;self.reject('zoom/rotation')
        self.setUp();self.documents['pdf']['rotated']['view']['rotation']=0;self.reject('zoom/rotation')
        self.setUp();self.documents['captures'].pop();self.reject('theme captures')

    def test_office_and_text_insertion_must_be_observed_unchanged(self):
        for target in ('docx','xlsx'):
            self.setUp();self.documents[target]['typing']['after']='changed';self.reject('insertion')
        self.setUp();self.documents['text'][0]['typing']['nativeInputSource']='synthetic DOM event';self.reject('insertion')
        self.setUp();self.documents['xlsx']['secondSheet']='missing';self.reject('second sheet')

    def test_all_formats_and_actual_two_pane_resize_are_required(self):
        self.documents['formats'].remove('tsv');self.reject('supported formats')
        self.setUp();self.documents['twoPanes']['afterBounds']=copy.deepcopy(self.documents['twoPanes']['beforeBounds']);self.reject('divider did not move')
        self.setUp();self.documents['twoPanes']['webContentsIdsAfter'].append(333);self.reject('native page processes')

    def test_host_and_ipc_must_reject_both_writes_for_every_document(self):
        for route in ('native','ipc'):
            self.setUp();self.documents['guards']['rejections'][0][route]['rejected']=False;self.reject('write was accepted')
        self.setUp();self.documents['guards']['rejections'][0]['native']['code']='OTHER';self.reject('write was accepted')
        self.setUp();self.documents['guards']['rejections'][1]=copy.deepcopy(self.documents['guards']['rejections'][0]);self.reject()

    def test_repeating_one_guarded_document_cannot_substitute_for_all_nine(self):
        rows=self.documents['guards']['rejections'];rows[-2:]=copy.deepcopy(rows[-4:-2]);self.reject()

    def test_original_files_no_save_dialogs_and_privacy_are_enforced(self):
        self.documents['guards']['originalFiles'][0]['afterSHA256']='0'*64;self.reject('original file')
        self.setUp();self.documents['guards']['dialogCalls']['save']=1;self.reject('offered saving')
        self.setUp();self.documents['privacy']['normalProfileContainsPrivateText']=True;self.reject('private document persisted')

    def test_document_images_are_hash_bound_and_cannot_claim_os_capture(self):
        self.documents['captures'][0]['sha256']='0'*64;self.reject('checksum')
        self.setUp();self.documents['captures'][0]['source']='globalCapture.acquire(display)';self.reject('viewer capture identity')
        self.setUp();self.documents['captures'][0]['filename']='../outside.png';self.reject('viewer capture identity')

    def test_footer_needs_all_six_width_theme_cases_and_requested_order(self):
        self.footer['cases'].pop();self.reject('width/theme')
        self.setUp();self.footer['cases'][0]['actions'].reverse();self.reject('overflow/order')
        self.setUp();self.footer['cases'][0]['controls']['left'][0]='settings';self.reject('footer order')

    def test_footer_mascot_and_icon_geometry_cannot_be_squashed_or_misaligned(self):
        self.footer['cases'][0]['controls']['brand']['width']=16;self.reject('mascot')
        self.setUp();self.footer['cases'][0]['controls']['source']='mouse-head.svg';self.reject('mascot')
        self.setUp();self.footer['cases'][0]['controls']['icons'][0]['icon']['x']+=3;self.reject('centering')

    def test_obsolete_footer_controls_and_overlapping_nora_are_rejected(self):
        self.footer['cases'][0]['controls']['footerDocuments']=1;self.reject('obsolete')
        self.setUp();self.footer['cases'][0]['controls']['leftBox']['right']=9999;self.reject('central Nora')
        self.setUp();self.footer['cases'][0]['overflow']=3;self.reject('overflow/order')

    def test_footer_capture_must_be_a_real_sized_decodable_png(self):
        self.files['mouse-632-footer-light-800.png']=solid_png(100,100);self.reject('actual viewport')
        self.setUp();self.files['mouse-632-footer-light-800.png']=b'not PNG';self.reject('bounded PNG')

    def test_website_confirmation_and_manual_helper_cannot_be_missing_or_truthy(self):
        for group in ('websiteOffer','manualHelper'):
            for field,value in self.original[CHECK.JSON_NAMES[2]][group].items():
                if type(value) is not bool:continue
                self.setUp();self.footer[group][field]=1;self.reject()
        self.setUp();self.footer['websiteOffer']['confirmedUrl']='https://example.com';self.reject('destination')


if __name__ == '__main__':
    unittest.main()
