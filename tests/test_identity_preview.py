"""Regression checks for the published Identity 0.6 preview."""
import functools
import http.server
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright, expect
import os

class IdentityPreviewQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parents[1]))
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start()
        cls.browser=cls.pw.chromium.launch(**({'executable_path':os.environ['CHROMIUM_PATH']} if os.getenv('CHROMIUM_PATH') else {}))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':393,'height':852},has_touch=True,is_mobile=True)
        self.page=self.context.new_page()
        self.page.set_default_timeout(12000)
        self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.base+'/') else r.abort())
        self.page.goto(self.base+'/docs/index.html')
        self.page.locator('[data-action="nav"][data-view="settings"]:visible').first.click()
        self.page.locator('[data-action="id-profile-tab"][data-tab="personal"]').click()

    def tearDown(self):
        try:
            self.assertEqual(self.errors,[])
        finally:
            self.context.close()

    def test_font_sheet_selection_and_persistence(self):
        p=self.page
        p.locator('[data-studio-category=type]').first.wait_for(state='attached')
        p.locator('[data-action="id-studio-category"][data-category="type"]').click()
        trigger=p.get_by_role('button',name='Шрифт: Beta',exact=True)
        trigger.click()
        sheet=p.locator('#id-choice-sheet')
        expect(sheet).to_be_visible()
        sheet.get_by_role('button',name='Serif — Выразительные засечки').click()
        expect(sheet).not_to_be_visible()
        expect(p.get_by_role('button',name='Шрифт: Serif',exact=True)).to_be_visible()
        p.wait_for_function("document.documentElement.style.fontFamily.includes('Georgia')")
        p.wait_for_function("JSON.parse(localStorage.getItem('beta.player.settings')||'{}').idFont==='serif'")
        p.reload()
        p.wait_for_function("document.documentElement.style.fontFamily.includes('Georgia')")

    def test_range_continuity_and_motion_toggle(self):
        p=self.page
        p.locator('[data-action="id-studio-category"][data-category="type"]').click()
        slider=p.locator('[data-id-setting="idScale"]')
        expect(slider).to_have_attribute('step','1')
        slider.focus()
        slider.press('ArrowRight')
        expect(p.locator('[data-id-output="idScale"]')).to_have_text('101%')
        p.wait_for_function("document.documentElement.style.getPropertyValue('--id-font')==='1.01'")
        p.locator('[data-action="id-studio-category"][data-category="motion"]').click()
        motion=p.locator('[data-action="toggle-motion"]')
        motion.click()
        expect(motion).to_have_attribute('aria-checked','false')
        expect(p.locator('html')).to_have_attribute('data-id-motion','off')
        motion.click()
        expect(motion).to_have_attribute('aria-checked','true')
        expect(p.locator('html')).to_have_attribute('data-id-motion','on')

    def test_tab_indicator_and_reduced_motion(self):
        p=self.page
        expect(p.locator('.id-tab-indicator')).to_be_visible()
        p.emulate_media(reduced_motion='reduce')
        p.locator('[data-action="id-profile-tab"][data-tab="import"]').click()
        expect(p.locator('.id-tabs')).to_have_attribute('style','--tab-index:2')
        expect(p.locator('.id-import')).to_be_visible()

    def test_studio_presets_and_groups(self):
        p=self.page
        expect(p.locator('.id-stage')).to_be_visible()
        expect(p.locator('[data-action="id-studio-category"]')).to_have_count(6)
        p.locator('[data-action="id-studio-preset"][data-preset="deep"]').click()
        expect(p.locator('html')).to_have_attribute('data-theme','deep')
        p.wait_for_function("document.documentElement.style.getPropertyValue('--id-glass')==='0.96'")
        p.locator('[data-action="id-studio-category"][data-category="nav"]').click()
        expect(p.locator('[data-action="id-studio-category"][aria-pressed=true]')).to_have_count(1)
        expect(p.locator('[data-id-setting="idNav"]')).to_be_attached()
        expect(p.locator('[data-studio-category="material"]').first).to_be_hidden()

    def test_slider_pointer_commit_and_vertical_cancel(self):
        p=self.page
        p.locator('[data-action="id-studio-category"][data-category="type"]').click()
        slider=p.locator('[data-id-setting="idScale"]')
        shell=slider.locator('..')
        shell.scroll_into_view_if_needed()
        rail=shell.locator('.id-rail')
        box=rail.bounding_box()
        x=box['x']+box['width']*.3
        y=box['y']+box['height']/2
        initial=slider.input_value()
        p.mouse.move(x,y)
        p.mouse.down()
        expect(slider).to_have_value(initial)
        p.mouse.move(x,y+30)
        p.mouse.up()
        expect(slider).to_have_value(initial)
        p.mouse.move(x,y)
        p.mouse.down()
        p.mouse.move(box['x']+box['width']*.8,y,steps=8)
        expect(slider).to_have_value(initial)
        p.mouse.up()
        expect(slider).to_have_value('118')
        p.wait_for_function("document.documentElement.style.getPropertyValue('--id-font')==='1.18'")
