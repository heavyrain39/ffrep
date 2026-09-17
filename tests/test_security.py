"""Prose is editable text, never executable HTML or JavaScript."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_security',ROOT/'scripts/build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class EscapingTests(unittest.TestCase):
    def test_prose_cannot_close_script_or_create_markup(self):
        data,manifest=build.load()
        data=copy.deepcopy(data)
        payload='</script><img src=x onerror=alert(1)>'
        data['ui']['copied']=payload
        data['hero']['lead']=payload
        result=build.render(data,manifest)
        self.assertNotIn(payload,result)
        self.assertIn('&lt;/script&gt;&lt;img',result)
        self.assertIn(chr(92)+'u003c/script'+chr(92)+'u003e',result)
