import base64
import functools
import http.server
import io
import json
import os
from pathlib import Path
import struct
import threading
import unittest
import wave
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
TRACK = {'id':'QaTrack1','title':'QA Full Song','user':{'name':'QA Artist'},'duration':185,'is_streamable':True,'is_stream_gated':False,'is_available':True,'genre':'Electronic','mood':'Peaceful'}
LOCKED = {**TRACK,'id':'QaLocked','title':'QA Locked Song','is_stream_gated':True}
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5WQAAAAASUVORK5CYII=')

def wav_bytes():
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setparams((1,2,8000,0,'NONE','not compressed'))
        f.writeframes(struct.pack('<h',0)*8000*15)
    return out.getvalue()

class BetaQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start()
        try:
            args=['--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']
            opts={'args':args}
            if os.getenv('CHROMIUM_PATH'): opts['executable_path']=os.environ['CHROMIUM_PATH']
            cls.browser=cls.pw.chromium.launch(**opts)
        except Exception:
            cls.pw.stop(); cls.server.shutdown(); cls.server.server_close(); raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close()

    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':393,'height':852},device_scale_factor=1,has_touch=True,is_mobile=True)
        self.page=self.context.new_page()
        self.page.set_default_timeout(12000)
        self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.offline_catalog=False
        self.context.route('**/*',self.route)

    def route(self,r):
        u=r.request.url
        if u.startswith(self.base+'/'): return r.continue_()
        if 'api.audius.co/v1/tracks/search?' in u:
            if self.offline_catalog: return r.fulfill(status=503,headers={'access-control-allow-origin':'*'},json={'error':'unavailable'})
            return r.fulfill(status=200,headers={'access-control-allow-origin':'*'},json={'data':[TRACK,LOCKED]})
        return r.abort()

    def tearDown(self):
        try:
            ARTIFACTS.mkdir(exist_ok=True)
            try: self.page.screenshot(path=str(ARTIFACTS/(self._testMethodName+'.png')),timeout=5000,animations='disabled')
            except Exception as exc: (ARTIFACTS/(self._testMethodName+'.screenshot-error.txt')).write_text(str(exc))
            (ARTIFACTS/(self._testMethodName+'.json')).write_text(json.dumps(self.errors,ensure_ascii=False))
        finally: self.context.close()

    def open_player(self):
        self.page.goto(self.base+'/app/player.html')
        self.page.wait_for_function("typeof window.__betaPlayerDebug==='function' && !!document.querySelector('#main [data-action]')")

    def debug(self,expression):
        self.page.wait_for_function(expression)

    def nav(self,view):
        self.page.locator(f'[data-action="nav"][data-view="{view}"]:visible').first.click()
        self.debug(f"window.__betaPlayerDebug().view === '{view}'")

    def test_player_displays_liquid_preferences_without_importing_audio(self):
        self.page.goto(self.base+'/app/index.html')
        seed={'v':1,'mood':'Ночь','tracks':[{'title':'After Dark','artist':'Mr.Kitty'},{'title':'<img src=x>','artist':'QA'}],'artists':['Mr.Kitty']}
        self.page.evaluate('(data) => localStorage.setItem("beta.liquid.selection.v1", JSON.stringify(data))',seed)
        self.open_player()
        panel=self.page.locator('#liquid-selection')
        expect(panel).to_contain_text('Ночь')
        expect(panel).to_contain_text('After Dark — Mr.Kitty')
        expect(panel).to_contain_text('<img src=x>')
        expect(panel.locator('img')).to_have_count(0)
        self.assertEqual(self.page.evaluate('window.__betaPlayerDebug().imported'),0)
        self.assertEqual(self.page.evaluate('window.__betaPlayerDebug().liked'),0)
        self.assertEqual(self.page.evaluate('JSON.parse(localStorage.getItem("beta.liquid.selection.v1"))'),seed)
        self.assertEqual(self.errors,[])

    def test_home_mood_is_exclusive(self):
        self.open_player()
        moods=self.page.locator('#main [data-action="mood"]')
        expect(moods.first).to_be_visible()
        moods.nth(0).click(); expect(self.page.locator('#main .mood.active')).to_have_count(1)
        moods.nth(1).click(); expect(self.page.locator('#main .mood.active')).to_have_count(1)
        expect(moods.nth(1)).to_have_class(__import__('re').compile(r'\bactive\b'))
        self.assertEqual(self.errors,[])

    def test_catalog_filters_gated_track(self):
        self.open_player(); self.nav('search')
        self.page.locator('#searchInput').fill('QA Full Song')
        expect(self.page.locator('#search-results').get_by_text('QA Full Song',exact=True).first).to_be_visible()
        expect(self.page.locator('#search-results').get_by_text('QA Locked Song',exact=True)).to_have_count(0)
        self.assertEqual(self.errors,[])

    def test_catalog_failure_keeps_search_usable(self):
        self.offline_catalog=True; self.open_player(); self.nav('search')
        self.page.locator('#searchInput').fill('Offline QA')
        self.page.wait_for_function("!document.querySelector('#search-results').textContent.includes('Ищем') && document.querySelector('#search-results').textContent.trim().length>0")
        expect(self.page.locator('#searchInput')).to_be_editable()
        self.assertEqual(self.errors,[])

    def test_theme_survives_reload(self):
        self.open_player(); self.nav('settings')
        self.page.locator('[data-action="theme"][data-theme-id="deep"]').click()
        expect(self.page.locator('html')).to_have_attribute('data-theme','deep')
        self.debug("JSON.parse(localStorage.getItem('beta.player.settings')||'{}').theme==='deep'")
        self.page.reload(); expect(self.page.locator('html')).to_have_attribute('data-theme','deep')
        self.assertEqual(self.errors,[])

    def test_wallpaper_upload_reset(self):
        self.open_player(); self.nav('settings')
        self.page.locator('#wallpaperinput').set_input_files({'name':'qa.png','mimeType':'image/png','buffer':PNG})
        self.debug("document.documentElement.classList.contains('has-wallpaper') && !!localStorage.getItem('beta.signature.wallpaper')")
        self.page.locator('[data-action="wallpaper-reset"]').click()
        self.debug("!document.documentElement.classList.contains('has-wallpaper') && !localStorage.getItem('beta.signature.wallpaper')")
        self.assertEqual(self.errors,[])

    def test_local_audio_play_pause_and_eq(self):
        self.open_player()
        self.page.locator('#fileinput').set_input_files({'name':'QA Local.wav','mimeType':'audio/wav','buffer':wav_bytes()})
        self.debug('window.__betaPlayerDebug().imported >= 1')
        self.nav('library')
        self.page.locator('#main [data-action="play"]').filter(has_text='QA Local').first.click()
        self.debug("window.__betaPlayerDebug().playing && !document.querySelector('#audioLocal').paused")
        self.page.locator('#player [data-action="toggle-play"]:visible').first.click()
        self.debug("!window.__betaPlayerDebug().playing && document.querySelector('#audioLocal').paused")
        self.nav('settings'); self.page.locator('[data-action="open-eq"]').click()
        self.debug('window.__betaPlayerDebug().nowOpen')
        self.page.locator('[data-action="eq-preset"][data-value="bass"]').click()
        expect(self.page.locator('[data-eq="0"]')).to_have_value('7')
        self.assertEqual(self.errors,[])

    def test_liquid_selection_restores_and_persists_edits(self):
        # Verify Liquid's persisted selection contract.
        self.page.goto(self.base+'/app/index.html')
        seed={'v':1,'mood':'Ночь','songs':[0,999999,-1,'bad'],'artists':['Mr.Kitty','Unknown Artist']}
        self.page.evaluate('(data) => localStorage.setItem("beta.liquid.selection.v1", JSON.stringify(data))',seed)
        self.page.goto(self.base+'/app/liquid.html')
        self.page.wait_for_function("typeof window.__betaV40==='function'")
        self.assertEqual(self.page.evaluate('window.__betaV40().activeMood'),'Ночь')
        self.assertEqual(self.page.evaluate('window.__betaV40().selectedSongs'),['After Dark'])
        self.assertEqual(self.page.evaluate('window.__betaV40().selectedArtists'),['Mr.Kitty'])
        self.page.reload()
        self.page.wait_for_function("typeof window.__betaV40==='function'")
        self.assertEqual(self.page.evaluate('window.__betaV40().activeMood'),'Ночь')
        self.assertEqual(self.page.evaluate('window.__betaV40().selectedSongs'),['After Dark'])
        # Open the mood core, remove the mood and confirm the edit is persisted.
        box=self.page.locator('#betaTrios canvas').bounding_box()
        portrait=box['width']<box['height']*.9
        x=box['x']+box['width']*(.52 if portrait else .27)
        y=box['y']+box['height']*(.30 if portrait else .50)
        self.page.mouse.click(x,y); self.page.mouse.click(x,y)
        self.debug('window.__betaV40().opened.includes(0)')
        self.page.locator('.saved-remove[aria-label="Удалить из выбранного: Настроение: Ночь"]').click()
        self.debug("window.__betaV40().activeMood===null")
        stored=self.page.evaluate("JSON.parse(localStorage.getItem('beta.liquid.selection.v1'))")
        self.assertIsNone(stored['mood'])
        self.assertEqual(stored['songs'],[0])
        self.assertEqual(stored['tracks'],[{'title':'After Dark','artist':'Mr.Kitty'}])
        self.assertEqual(stored['artists'],['Mr.Kitty'])
        self.assertEqual(self.errors,[])

    def test_liquid_mood_core_opens_only_its_world(self):
        self.page.goto(self.base+'/app/liquid.html')
        self.page.wait_for_function("typeof window.__betaV40==='function'")
        expect(self.page.locator('#betaTrios canvas')).to_be_visible()
        self.assertEqual(self.page.evaluate('window.__betaV40().opened'),[])
        box=self.page.locator('#betaTrios canvas').bounding_box()
        portrait=box['width']<box['height']*.9
        x=box['x']+box['width']*(.52 if portrait else .27)
        y=box['y']+box['height']*(.30 if portrait else .50)
        self.page.mouse.click(x,y); self.page.mouse.click(x,y)
        self.debug('window.__betaV40().opened.includes(0)')
        self.assertEqual(self.page.evaluate('window.__betaV40().opened'),[0])
        self.assertEqual(self.page.locator('.tag[data-type="track"]').count(),0)
        self.assertEqual(self.page.locator('.tag[data-type="artist"]').count(),0)
        self.assertEqual(self.errors,[])

if __name__=='__main__': unittest.main()
