"""Identity lab regression tests; run with existing BETA QA workflow."""
import functools
import http.server
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright, expect
import os

ROOT = Path(__file__).resolve().parents[1]

class IdentityQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        try:
            opts = {}
            if os.getenv('CHROMIUM_PATH'):
                opts['executable_path'] = os.environ['CHROMIUM_PATH']
            cls.browser = cls.pw.chromium.launch(**opts)
        except Exception:
            cls.pw.stop()
            cls.server.shutdown()
            cls.server.server_close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':393,'height':852},has_touch=True,is_mobile=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto(self.base + '/app/identity.html')
        expect(self.page.locator('html')).to_have_attribute('data-beta-theme', 'metal')

    def tearDown(self):
        try:
            self.assertEqual(self.errors, [])
        finally:
            self.context.close()

    def test_theme_motion_and_reset_persist(self):
        p = self.page
        p.locator('[data-theme="deep"]').click()
        p.locator('#motion').click()
        expect(p.locator('html')).to_have_attribute('data-beta-theme', 'deep')
        expect(p.locator('#duration')).to_be_disabled()
        p.reload()
        expect(p.locator('html')).to_have_attribute('data-beta-theme', 'deep')
        expect(p.locator('#motion')).to_have_attribute('aria-checked','false')
        p.locator('#reset').click()
        expect(p.locator('html')).to_have_attribute('data-beta-theme','metal')
        expect(p.locator('#duration')).to_be_enabled()

    def test_search_navigation_and_scale(self):
        p = self.page
        p.locator('#search').fill('mercury')
        expect(p.locator('[data-item]:visible')).to_have_count(1)
        p.locator('#search').fill('no match')
        expect(p.locator('#empty')).to_be_visible()
        p.locator('#search').fill('')
        expect(p.locator('[data-item]:visible')).to_have_count(3)
        p.locator('[data-tab="Профиль"]').click()
        expect(p.locator('[data-tab][aria-pressed="true"]')).to_have_count(1)
        expect(p.locator('#tabNote')).to_contain_text('Профиль')
        p.locator('#scale').focus()
        p.keyboard.press('End')
        expect(p.locator('#scaleOut')).to_have_text('125%')
        self.assertTrue(p.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        p.reload()
        expect(p.locator('#scaleOut')).to_have_text('125%')

    def test_system_reduced_motion(self):
        p = self.page
        p.emulate_media(reduced_motion='reduce')
        expect(p.locator('#systemMotion')).to_be_visible()
        expect(p.locator('#duration')).to_be_disabled()
        self.assertEqual(p.locator('#sample').evaluate("e => getComputedStyle(e).transitionDuration"), '0s')
