"""Regression coverage for persistent profile name reset."""
import test_beta
from playwright.sync_api import expect


class IdentityNameResetQA(test_beta.BetaQA):
    # Reuse the existing browser fixture without rediscovering its tests.
    def test_identity_name_reset_survives_reload(self):
        self.page.goto(self.base + '/app/identity.html')
        self.debug("typeof window.__betaPlayerDebug==='function' && !!document.querySelector('#main [data-action]')")
        self.nav('settings')
        self.page.locator('#identity-name').fill('QA Reset')
        expect(self.page.locator('#identity-name-preview')).to_have_text('QA Reset')
        self.page.locator('#identity-name').fill('')
        expect(self.page.locator('#identity-name-preview')).to_have_text('Моя Beta')
        self.page.reload()
        self.debug("typeof window.__betaPlayerDebug==='function' && !!document.querySelector('#main [data-action]')")
        self.nav('settings')
        expect(self.page.locator('#identity-name')).to_have_value('')
        expect(self.page.locator('#identity-name-preview')).to_have_text('Моя Beta')
        self.assertEqual(self.errors, [])


# unittest discovers inherited test methods as well; disable only those inherited here.
for _name in dir(test_beta.BetaQA):
    if _name.startswith('test_'):
        setattr(IdentityNameResetQA, _name, None)
