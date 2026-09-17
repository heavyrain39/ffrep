"""Font files must remain identical to the author's uploads, not substitutes."""
import hashlib
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'MuseoModerno-Variable-latin.woff2': '8df17b9c94983ee6490a8004e422123c5503a40ad59cc32d39e02d202561382e',
    'SUIT-Variable.woff2': 'aa894a204d5a6fbae259dac6868d350cbd373a390caee0313f92946af741df23',
}

class TypographyTests(unittest.TestCase):
    def test_exact_supplied_webfonts_and_deployed_copies(self):
        for name, expected in EXPECTED.items():
            for folder in (ROOT / 'assets/fonts', ROOT / '_site/assets/fonts'):
                data = (folder / name).read_bytes()
                self.assertEqual(data[:4], b'wOF2')
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
    def test_licenses_shipped(self):
        for name in ('MuseoModerno-OFL.txt', 'SUIT-OFL.txt'):
            self.assertIn('SIL OPEN FONT LICENSE', (ROOT / '_site/assets/fonts' / name).read_text())
    def test_font_sources_local_and_variable(self):
        css = (ROOT / 'assets/typography.css').read_text()
        self.assertEqual(css.count('@font-face'), 2)
        self.assertEqual(css.count('font-weight: 100 900'), 2)
        for path in re.findall(r'url\("([^"]+)"\)', css):
            self.assertTrue(path.startswith('./fonts/'))
            self.assertTrue((ROOT / 'assets' / path).is_file())
        self.assertNotIn('https:', css)
    def test_preloads_and_stylesheet_order(self):
        html = (ROOT / '_site/index.html').read_text()
        self.assertLess(html.index('./assets/site.css'), html.index('./assets/typography.css'))
        self.assertEqual(html.count('as="font"'), 2)
        self.assertIn('./assets/favicon.svg?v=2', html)
    def test_supplied_favicon_geometry(self):
        doc = ET.parse(ROOT / 'assets/favicon.svg').getroot()
        ns = '{http://www.w3.org/2000/svg}'
        self.assertEqual(doc.attrib['viewBox'], '0 0 64 64')
        self.assertEqual(doc.find(ns + 'title').text, 'FFREP')
        self.assertEqual(doc.find(ns + 'path').attrib, {
            'd': 'M13 25V13h12M39 13h12v12M51 39v12H39M25 51H13V39',
            'fill': 'none', 'stroke': '#1f211f', 'stroke-linecap': 'round',
            'stroke-linejoin': 'round', 'stroke-width': '5'})
        self.assertEqual((ROOT / 'assets/favicon.svg').read_bytes(), (ROOT / '_site/assets/favicon.svg').read_bytes())

if __name__ == '__main__':
    unittest.main()
