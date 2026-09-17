"""Offline checks for the public site. No experiment files or services required."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build',ROOT/'scripts/build.py')
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)

class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.tags=[]; self.ids=[]; self.links=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs); self.tags.append((tag,attrs))
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a':self.links.append(attrs.get('href',''))

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content,cls.locales=build.load()
        cls.html=build.render(cls.content,cls.locales)
        cls.dom=Elements(cls.html)
    def test_render_is_current(self):
        self.assertEqual((ROOT/'index.html').read_text('utf-8'),self.html)
    def test_unique_ids_and_fragment_targets(self):
        self.assertEqual(len(self.dom.ids),len(set(self.dom.ids)))
        for href in self.dom.links:
            if href.startswith('#'):self.assertIn(href[1:],self.dom.ids)
    def test_faqs_prerendered(self):
        for faq in self.content['faq']['items']:
            self.assertIn(faq['question'],self.html)
            for p in faq['answer']:self.assertIn(p,self.html)
        self.assertEqual(len([t for t,a in self.dom.tags if t=='details']),len(self.content['faq']['items']))
    def test_translatable_keys(self):
        for _,attrs in self.dom.tags:
            if 'data-i18n' in attrs:self.assertIsInstance(build.lookup(self.content,attrs['data-i18n']),str)
            for binding in attrs.get('data-i18n-attr','').split(';'):
                if binding:self.assertIsInstance(build.lookup(self.content,binding.split(':')[1]),str)
    def test_english_is_not_misrepresented(self):
        for language in self.locales['languages']:
            button=next(a for t,a in self.dom.tags if a.get('data-lang')==language['code'])
            self.assertEqual('disabled' in button,not language['enabled'])
    def test_links_are_public_and_assets_relative(self):
        for link in self.dom.links:
            self.assertNotIn('/quadruped',link)
        for tag,attrs in self.dom.tags:
            for key in ('src','href'):
                value=attrs.get(key,'')
                if value.startswith('./'):
                    self.assertTrue((ROOT/value[2:]).exists(),value)
            if tag=='script':self.assertFalse(attrs.get('src','').startswith('http'))
    def test_categories_exist(self):
        categories={c['id'] for c in self.content['faq']['categories']}
        for faq in self.content['faq']['items']:self.assertIn(faq['category'],categories)
    def test_public_bundle_allowlist(self):
        files=[p for p in (ROOT/'_site').rglob('*') if p.is_file()]
        self.assertTrue(files)
        for p in files:
            relative=p.relative_to(ROOT/'_site').as_posix()
            self.assertTrue(relative in ('index.html','.nojekyll') or relative.startswith(('assets/','content/')),relative)
            text=p.read_text('utf-8')
            for pattern in (r'ghp_[A-Za-z0-9]{20,}',r'github_pat_',r'BRMIPV[A-Z0-9]+',r'fullcns_',r'checkpoint_\d',r'value_origin',r'actor_lr',r'critic_lr',r'\.venv[/\\]',r'runs/performance'):
                self.assertNotRegex(text,pattern)
    def test_no_fake_live_data_or_external_fonts(self):
        self.assertNotIn('<video',self.html)
        self.assertNotIn('<iframe',self.html)
        self.assertNotIn('@font-face',(ROOT/'assets/site.css').read_text())
    def test_config_script_is_valid_json(self):
        script=re.search(r'<script type="application/json" id="site-config">(.*?)</script>',self.html,re.S)
        config=json.loads(script[1]);self.assertEqual(config['locales']['default'],'ko')

if __name__=='__main__':unittest.main()
