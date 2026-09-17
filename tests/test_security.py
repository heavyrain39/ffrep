import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_security',ROOT/'scripts/build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class EscapingTests(unittest.TestCase):
    def test_prose_and_config_are_not_executable(self):
        data,manifest=build.load();data=copy.deepcopy(data)
        attack='</script><img src=x onerror=alert(1)>'
        data['ui']['videoTitle']=attack;data['intro']['question']=attack
        data['faq'][0]['answer']=[attack]
        result=build.render(data,manifest)
        self.assertNotIn(attack,result);self.assertIn('&lt;img',result)
        js=re.search(r'<script type="application/json" id="site-config">(.*?)</script>',result,re.S)[1]
        self.assertEqual(json.loads(js)['ui']['videoTitle'],attack)
    def test_links_only_allow_https(self):
        self.assertNotIn('<a ',build.rich('[click](javascript:alert(1))'))
        self.assertIn('rel="noopener noreferrer"',build.rich('[source](https://example.com/)'))
    def test_attribute_injection_is_escaped(self):
        text=build.rich('[source](https://example.com/"onmouseover="alert)')
        self.assertIn('&quot;',text);self.assertNotIn('"onmouseover="',text)

if __name__=='__main__':unittest.main()
