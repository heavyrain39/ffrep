"""Verify the supplied fonts, restrained weights and KO/EN layout in Chromium."""
from __future__ import annotations
import functools
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT / '_site')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    report = {'passed': False, 'cases': []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=os.environ.get('BROWSER_EXECUTABLE_PATH') or None)
            for lang in ('ko', 'en'):
                context = browser.new_context(locale='ko-KR' if lang == 'ko' else 'en-US')
                context.route('https://**/*', lambda route: route.abort())
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda err: errors.append(str(err)))
                fonts_requested = []
                page.on('request', lambda req: fonts_requested.append(req.url) if '.woff2' in req.url else None)
                page.goto(base + '?lang=' + lang)
                page.wait_for_function('(lang) => document.documentElement.lang === lang', arg=lang)
                page.evaluate('async () => { await document.fonts.ready; }')
                assert page.evaluate('document.fonts.check(\'400 24px "MuseoModerno"\')')
                assert page.evaluate('document.fonts.check(\'400 15px "SUIT"\')')
                assert len(fonts_requested) == 2, fonts_requested
                assert all(url.startswith(base + 'assets/fonts/') for url in fonts_requested)
                client = context.new_cdp_session(page)
                client.send('DOM.enable'); client.send('CSS.enable')
                root = client.send('DOM.getDocument')['root']['nodeId']
                rendered = {}
                for selector, expected in (('.masthead h1', 'MuseoModerno'), ('.intro p', 'SUIT')):
                    node = client.send('DOM.querySelector', {'nodeId': root, 'selector': selector})['nodeId']
                    faces = client.send('CSS.getPlatformFontsForNode', {'nodeId': node})['fonts']
                    assert any(expected in f['familyName'] and f['isCustomFont'] and f['glyphCount'] > 0 for f in faces), faces
                    rendered[selector] = faces
                for width in (320, 375, 768, 1360):
                    page.set_viewport_size({'width': width, 'height': 950})
                    page.evaluate('document.querySelectorAll("details").forEach(d => d.open = true)')
                    page.evaluate('async () => { await document.fonts.ready; }')
                    result = page.evaluate('''() => {
                        const h = document.querySelector('.masthead h1'), l = document.querySelector('.language');
                        const a=h.getBoundingClientRect(), b=l.getBoundingClientRect();
                        return {
                            overflow: document.documentElement.scrollWidth > innerWidth,
                            headerOverlap: a.right > b.left - 8,
                            titleFamily: getComputedStyle(h).fontFamily,
                            titleWeight: getComputedStyle(h).fontWeight,
                            bodyFamily: getComputedStyle(document.body).fontFamily,
                            bodyWeight: getComputedStyle(document.body).fontWeight,
                            questionWeight: getComputedStyle(document.querySelector('summary')).fontWeight,
                            titleLines: h.innerText.split('\\n').length
                        };
                    }''')
                    assert not result['overflow'], (lang, width, result)
                    assert not result['headerOverlap'], (lang, width, result)
                    assert result['titleLines'] == 3
                    assert result['titleWeight'] == result['bodyWeight'] == '400'
                    assert result['questionWeight'] == '450'
                    report['cases'].append({'lang': lang, 'width': width, **result})
                report[lang + '_rendered_fonts'] = rendered
                page.set_viewport_size({'width': 1360, 'height': 1000})
                page.evaluate('document.querySelectorAll("details").forEach(d => d.open = false); scrollTo(0, 0)')
                page.screenshot(path=str(OUT / f'typography-{lang}-desktop.png'), full_page=True)
                page.screenshot(path=str(OUT / f'typography-{lang}-first-screen.png'))
                page.locator('#neural-network summary').click()
                page.screenshot(path=str(OUT / f'typography-{lang}-faq.png'), full_page=True)
                page.set_viewport_size({'width': 375, 'height': 850})
                page.evaluate('document.querySelectorAll("details").forEach(d => d.open = false); scrollTo(0, 0)')
                page.screenshot(path=str(OUT / f'typography-{lang}-mobile.png'), full_page=True)
                assert not errors, errors
                context.close()
            browser.close()
        report['passed'] = True
        print('PASS: supplied fonts actually rendered; eight KO/EN viewport cases, weights and title spacing.')
    finally:
        server.shutdown()
        (OUT / 'typography.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
