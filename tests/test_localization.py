"""Translation coverage without browser or network dependencies."""
import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('localization_build', ROOT/'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Bindings(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ko, cls.manifest = build.load()
        cls.en = json.loads((ROOT/'content/en.json').read_text('utf-8'))
        cls.html = build.render(cls.ko, cls.manifest)
        cls.dom = Bindings(cls.html)

    def test_both_languages_enabled(self):
        self.assertEqual({l['code'] for l in self.manifest['languages'] if l['enabled']}, {'ko', 'en'})
        for tag, attrs in self.dom.nodes:
            if 'data-lang' in attrs:
                self.assertNotIn('disabled', attrs)

    def test_complete_schema_and_paragraph_structure(self):
        self.assertEqual(build.flatten(self.ko).keys(), build.flatten(self.en).keys())
        self.assertEqual(len(self.en['faq']), 15)
        for ko, en in zip(self.ko['faq'], self.en['faq']):
            self.assertEqual(ko['id'], en['id'])
            self.assertEqual(ko.get('media'), en.get('media'))
            self.assertEqual(len(ko['answer']), len(en['answer']))
            self.assertTrue(en['question'].strip())
            self.assertTrue(all(p.strip() for p in en['answer']))

    def test_every_display_binding_has_english(self):
        for _, attrs in self.dom.nodes:
            for attribute in ('data-i18n', 'data-rich'):
                if attribute in attrs:
                    self.assertIsInstance(build.lookup(self.en, attrs[attribute]), str)
            for binding in attrs.get('data-i18n-attr', '').split(';'):
                if binding:
                    self.assertIsInstance(build.lookup(self.en, binding.split(':')[1]), str)

    def test_english_has_no_untranslated_korean_prose(self):
        for key, value in build.flatten(self.en).items():
            self.assertNotRegex(value, r'[가-힣]', key)

    def test_author_links_unchanged(self):
        def links(data):
            return [m[2] for q in data['faq'] for p in q['answer'] for m in build.LINK.finditer(p)]
        self.assertEqual(links(self.ko), links(self.en))

    def test_translations_embedded_without_extra_request(self):
        match = re.search(r'<script type="application/json" id="site-config">(.*?)</script>', self.html, re.S)
        config = json.loads(match[1])
        self.assertEqual(config['translations']['ko'], self.ko)
        self.assertEqual(config['translations']['en'], self.en)
        self.assertEqual(config['ui'], self.ko['ui'])

    def test_both_public_files_are_built(self):
        for code, data in [('ko', self.ko), ('en', self.en)]:
            self.assertEqual(json.loads((ROOT/f'_site/content/{code}.json').read_text('utf-8')), data)

    def test_distinctive_author_details_preserved(self):
        text = json.dumps(self.en, ensure_ascii=False)
        for phrase in ('20 trillion', 'GPT 6 Astra', '1,024', 'neocortex', 'rubber hammer', '猩機零式', 'しょうき', '正気'):
            self.assertIn(phrase, text)


if __name__ == '__main__':
    unittest.main()
