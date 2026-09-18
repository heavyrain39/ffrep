"""Offline checks for public copy, media, structure and locale compatibility."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build',ROOT/'scripts/build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class Elements(HTMLParser):
    def __init__(self,text):
        super().__init__();self.nodes=[];self.ids=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.nodes.append((tag,attrs))
        if 'id' in attrs:self.ids.append(attrs['id'])

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content,cls.locales=build.load();cls.html=build.render(cls.content,cls.locales);cls.dom=Elements(cls.html)
    def test_generated_site_is_current(self):
        self.assertEqual((ROOT/'index.html').read_text('utf-8'),self.html)
        self.assertEqual((ROOT/'_site/index.html').read_text('utf-8'),self.html)
    def test_15_questions_prerendered(self):
        self.assertEqual(len(self.content['faq']),15)
        self.assertEqual(sum(t=='details' for t,a in self.dom.nodes),15)
        self.assertEqual([q['id'] for q in self.content['faq'][-2:]],['shoki-name','blank-lobe'])
        for q in self.content['faq']:
            self.assertIn(q['question'],self.html)
            for p in q['answer']:self.assertIn(build.rich(p),self.html)
    def test_unique_ids(self):self.assertEqual(len(self.dom.ids),len(set(self.dom.ids)))
    def test_all_local_media_and_styles_exist(self):
        for tag,attrs in self.dom.nodes:
            for attr in ('href','src','poster'):
                value=attrs.get(attr,'')
                if value.startswith('./'):
                    value=urlparse(value).path
                    self.assertTrue((ROOT/value[2:]).is_file(),value)
                    self.assertTrue((ROOT/'_site'/value[2:]).is_file(),value)
                if value.startswith('#'):self.assertIn(value[1:],self.dom.ids)
    def test_video_not_autoplayed_or_preloaded(self):
        videos=[attrs for tag,attrs in self.dom.nodes if tag=='video']
        self.assertEqual(len(videos),3)
        for attrs in videos:
            self.assertIn('controls',attrs);self.assertIn('playsinline',attrs)
            self.assertNotIn('autoplay',attrs);self.assertEqual(attrs['preload'],'none')
            self.assertIn(attrs['aria-describedby'],self.dom.ids)
        self.assertFalse(any(tag=='iframe' for tag,_ in self.dom.nodes))
    def test_removed_interface_and_diagrams(self):
        for forbidden in ('질문 링크 복사','faq-search','share-page','copy-dialog','data-copy-question','<svg','<canvas','Same Brain, Different Bodies.'):
            self.assertNotIn(forbidden,self.html)
    def test_footer_exact_contacts(self):
        footer=self.html.split('<footer')[1].split('</footer>')[0]
        dom=Elements(footer)
        self.assertEqual([a['href'] for t,a in dom.nodes if t=='a'],['https://heavyrain39.github.io/portfolio/','mailto:ggolem@naver.com'])
        self.assertNotIn('github.com/heavyrain39/ffrep',self.html)
    def test_translations_and_links(self):
        for _,attrs in self.dom.nodes:
            for attribute in ('data-i18n','data-rich'):
                if attribute in attrs:self.assertIsInstance(build.lookup(self.content,attrs[attribute]),str)
            for binding in attrs.get('data-i18n-attr','').split(';'):
                if binding:self.assertIsInstance(build.lookup(self.content,binding.split(':')[1]),str)
            if attrs.get('target')=='_blank':self.assertIn('noopener',attrs['rel'])
    def test_english_disabled_until_available(self):
        en=next(a for t,a in self.dom.nodes if a.get('data-lang')=='en')
        enabled=next(l['enabled'] for l in self.locales['languages'] if l['code']=='en')
        self.assertEqual('disabled' in en,not enabled)
    def test_public_allowlist_and_no_private_recipe(self):
        allowed={'index.html','.nojekyll','assets/site.css','assets/typography.css','assets/site.js','assets/favicon.svg','content/locales.json'}
        allowed|={'content/'+l['code']+'.json' for l in self.locales['languages'] if l['enabled']}
        allowed|={'assets/media/'+name for name in build.MEDIA}
        allowed|={'assets/fonts/'+name for name in build.FONTS}
        actual={p.relative_to(ROOT/'_site').as_posix() for p in (ROOT/'_site').rglob('*') if p.is_file()}
        self.assertEqual(actual,allowed)
        for path in (ROOT/'_site').rglob('*'):
            if path.suffix in ('.html','.css','.js','.json'):
                data=path.read_text('utf-8')
                for secret in ('github_pat_','ghp_','BRMIPV','value_origin','fullcns_','runs/performance','actor_lr','critic_lr'):
                    self.assertNotIn(secret,data)
    def test_media_source_checksums(self):
        import hashlib
        records=json.loads((ROOT/'assets/media/sources.json').read_text('utf-8'))
        for item in records:
            path=ROOT/'assets/media'/item['file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])
    def test_no_network_runtime_dependencies(self):
        for tag,attrs in self.dom.nodes:
            if tag=='script':self.assertFalse(attrs.get('src','').startswith('http'))
        self.assertNotIn('@font-face',(ROOT/'assets/site.css').read_text('utf-8'))
        self.assertNotIn('border-radius:1',(ROOT/'assets/site.css').read_text('utf-8'))

if __name__=='__main__':unittest.main()
