"""Optional Chromium integration checks. Run after build.py; requires Playwright.

Serves only _site on loopback. Third-party requests are stubbed, not loaded.
Produces screenshots and a machine-readable report in test-results/.
"""
import json, threading, functools, re, time
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT=Path(__file__).resolve().parents[1]
root=PROJECT/'_site'
output=PROJECT/'test-results'
output.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
ko=json.loads((root/'content/ko.json').read_text());en=json.loads((root/'content/en.json').read_text())
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    def test(name,fn):
        try:fn();results.append({'test':name,'passed':True});print('PASS',name,flush=True)
        except Exception as exc:results.append({'test':name,'passed':False,'error':str(exc)});print('FAIL',name,str(exc),flush=True);(output/'browser-tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));raise
    def context(locale='en-US',saved=None,script=None,js=True):
        c=browser.new_context(locale=locale,java_script_enabled=js,viewport={'width':1360,'height':1000})
        if saved is not None:c.add_init_script(f"localStorage.setItem('ffrep-language',{json.dumps(saved)});")
        if script:c.add_init_script(script)
        c.route('https://**/*',lambda route:route.fulfill(status=200,content_type='text/html',body='<html></html>'))
        return c
    def assert_lang(page,lang):
        page.wait_for_function('(lang)=>document.documentElement.lang===lang && !document.querySelector(".language").hasAttribute("aria-busy")',arg=lang)
        expected={'ko':ko,'en':en}[lang]
        assert page.locator('#question').inner_text()==expected['intro']['question']
        assert page.locator(f'[data-lang={lang}]').get_attribute('aria-pressed')=='true'
    def initial(locale,wanted,query='',saved=None,script=None):
        c=context(locale,saved,script);pg=c.new_page();err=[];pg.on('pageerror',lambda e:err.append(str(e)))
        requests=[];pg.on('request',lambda req:requests.append(req.url))
        pg.goto(base+query);assert_lang(pg,wanted)
        assert not err,err
        assert not any('/content/' in x for x in requests),requests
        if saved is None:assert pg.evaluate("localStorage.getItem('ffrep-language')") is None
        c.close()
    for locale,wanted in [('ko-KR','ko'),('ko','ko'),('ko-KP','ko'),('en-US','en'),('ja-JP','en'),('de-DE','en'),('zh-CN','en')]:
        test('initial '+locale,lambda l=locale,w=wanted:initial(l,w))
    test('browser first preference only',lambda:initial('en-US','en',script="Object.defineProperty(navigator,'languages',{get:()=>['en-US','ko-KR']});"))
    test('navigator.language fallback',lambda:initial('ko-KR','ko',script="Object.defineProperty(navigator,'languages',{get:()=>[]});"))
    test('no browser language defaults EN',lambda:initial('en-US','en',script="Object.defineProperty(navigator,'languages',{get:()=>[]});Object.defineProperty(navigator,'language',{get:()=>''});"))
    test('URL KO overrides saved EN',lambda:initial('en-US','ko','?lang=ko',saved='en'))
    test('URL EN overrides saved KO',lambda:initial('ko-KR','en','?lang=en',saved='ko'))
    test('saved EN overrides Korean browser',lambda:initial('ko-KR','en',saved='en'))
    test('saved KO overrides Japanese browser',lambda:initial('ja-JP','ko',saved='ko'))
    test('invalid URL uses saved selection',lambda:initial('en-US','ko','?lang=fr',saved='ko'))
    test('invalid saved selection uses browser',lambda:initial('ja-JP','en',saved='invalid'))

    def check_dom():
        c=context('ko-KR');pg=c.new_page();pg.goto(base);assert_lang(pg,'ko')
        pg.locator('#blank-lobe summary').click();pg.evaluate("window.keptDetails=document.querySelector('#blank-lobe');window.keptVideo=document.querySelector('video')")
        pg.locator('[data-lang=en]').click();assert_lang(pg,'en')
        assert pg.locator('#blank-lobe').get_attribute('open') is not None
        assert pg.evaluate("keptDetails===document.querySelector('#blank-lobe') && keptVideo===document.querySelector('video')")
        for binding,expected in [('data-i18n',en),('data-rich',en)]:
            for node in pg.locator(f'[{binding}]').all():
                key=node.get_attribute(binding);v=expected
                for part in key.split('.'):v=v[int(part)] if isinstance(v,list) else v[part]
                if binding=='data-rich':v=re.sub(r'\[([^\]]+)\]\(https://[^)]+\)',r'\1',v)
                assert node.text_content()==v,(key,node.text_content(),v)
        assert pg.locator('meta[name=description]').get_attribute('content')==en['meta']['description']
        assert pg.locator('meta[property="og:locale"]').get_attribute('content')=='en_US'
        assert pg.locator('.model-figure img').get_attribute('alt')==en['ui']['modelAlt']
        assert pg.locator('#avatar .answer > p a').get_attribute('href')=='https://x.com/Arka_X_'
        assert pg.evaluate("localStorage.getItem('ffrep-language')")=='en'
        pg.goto(base);assert_lang(pg,'en')
        for i in range(6):
            for code in ('ko','en'):pg.locator(f'[data-lang={code}]').click();assert_lang(pg,code)
        pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko')
        for i,q in enumerate(ko['faq']):
            ps=pg.locator('#'+q['id']+' .answer > p').all()
            assert len(ps)==len(q['answer'])
            for pn,v in zip(ps,q['answer']):assert pn.text_content()==re.sub(r'\[([^\]]+)\]\(https://[^)]+\)',r'\1',v)
        c.close()
    test('whole-page toggle, preserved DOM, links, metadata, saved selection',check_dom)

    def same_choice():
        c=context('ko-KR');pg=c.new_page();pg.goto(base);assert_lang(pg,'ko');pg.locator('[data-lang=ko]').click()
        assert pg.evaluate("localStorage.getItem('ffrep-language')")=='ko'
        assert '?lang=ko' in pg.url
        c.close()
    test('same-language click still remembers choice',same_choice)

    def restricted():
        c=context('en-US',script="Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}});")
        pg=c.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base);assert_lang(pg,'en')
        pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko');pg.reload();assert_lang(pg,'ko')
        assert not errors; c.close()
    test('blocked storage and URL persistence',restricted)

    def video_state():
        c=context('en-US');pg=c.new_page();pg.goto(base);assert_lang(pg,'en')
        pg.evaluate("async()=>{window.v=document.querySelector('video');v.muted=true;await v.play();}")
        pg.wait_for_function('v.currentTime>0.5');t=pg.evaluate('v.currentTime')
        pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko')
        assert pg.evaluate('v===document.querySelector("video") && !v.paused')
        assert pg.evaluate('v.currentTime')>=t
        pg.evaluate('v.pause()')
        pg.locator('#shoki summary').click()
        pg.evaluate("async()=>{window.v2=document.querySelector('#shoki video');v2.muted=true;await v2.play();}")
        pg.wait_for_function('v2.currentTime>0.3');pg.locator('[data-lang=en]').click();assert_lang(pg,'en')
        assert pg.evaluate('v2===document.querySelector("#shoki video") && !v2.paused')
        pg.locator('#shoki summary').click();pg.wait_for_function('v2.paused')
        c.close()
    test('both real MP4s keep playback on language switch',video_state)

    def iframe_state():
        c=context('en-US');pg=c.new_page();pg.goto(base);assert_lang(pg,'en');pg.locator('#neural-network summary').click()
        pg.locator('[data-video]').click();pg.wait_for_selector('iframe');pg.evaluate("window.frame=document.querySelector('iframe')")
        assert pg.locator('iframe').get_attribute('title')==en['ui']['videoTitle']
        src=pg.locator('iframe').get_attribute('src');pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko')
        assert pg.locator('iframe').get_attribute('title')==ko['ui']['videoTitle']
        assert pg.locator('iframe').get_attribute('src')==src
        assert pg.evaluate('frame===document.querySelector("iframe")')
        c.close()
    test('loaded source iframe keeps state and translates accessible title',iframe_state)

    def nojs():
        c=context('en-US',js=False);pg=c.new_page();pg.goto(base)
        assert pg.locator('html').get_attribute('lang')=='ko'
        assert pg.locator('details').count()==15
        pg.locator('#blank-lobe summary').click();assert pg.locator('#blank-lobe .answer').is_visible()
        c.close()
    test('no-JavaScript Korean fallback remains readable',nojs)

    def layout():
        c=context('en-US');pg=c.new_page();pg.goto(base);assert_lang(pg,'en')
        for width in (320,375,768,1360):
            pg.set_viewport_size({'width':width,'height':950})
            for code in ('en','ko'):
                pg.locator(f'[data-lang={code}]').click();assert_lang(pg,code)
                pg.evaluate('document.querySelectorAll("details").forEach(d=>d.open=true)')
                assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,code)
                assert all(v['width']<=width for v in pg.locator('video').evaluate_all('(els)=>els.map(e=>({width:e.getBoundingClientRect().width}))'))
        pg.set_viewport_size({'width':1360,'height':1000});pg.locator('[data-lang=en]').click();assert_lang(pg,'en')
        pg.evaluate('document.querySelectorAll("details").forEach(d=>d.open=false);scrollTo(0,0)')
        pg.screenshot(path=str(output/'english-desktop.png'),full_page=True)
        pg.screenshot(path=str(output/'english-first-screen.png'))
        pg.set_viewport_size({'width':375,'height':850});pg.evaluate('scrollTo(0,0)')
        pg.screenshot(path=str(output/'english-mobile.png'),full_page=True)
        c.close()
    test('KO/EN at 320, 375, 768, 1360px; screenshots',layout)

    def failure_and_race():
        html=(root/'index.html').read_text()
        def strip(m):
            cfg=json.loads(m[1]);cfg.pop('translations',None)
            return '<script type="application/json" id="site-config">'+json.dumps(cfg,ensure_ascii=False)+'</script>'
        fallback=re.sub(r'<script type="application/json" id="site-config">(.*?)</script>',strip,html,flags=re.S)
        c=context('ko-KR');pg=c.new_page()
        pg.route(base,lambda route:route.fulfill(status=200,body=fallback,content_type='text/html'))
        pg.route('**/content/en.json',lambda route:route.fulfill(status=503,body='Unavailable'))
        pg.goto(base);assert_lang(pg,'ko');pg.locator('[data-lang=en]').click()
        pg.wait_for_function('document.querySelector(".language [role=status]").textContent.length>0')
        assert pg.locator('#question').inner_text()==ko['intro']['question']
        assert pg.evaluate("localStorage.getItem('ffrep-language')") is None
        pg.unroute('**/content/en.json');pg.locator('[data-lang=en]').click();assert_lang(pg,'en')
        pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko')
        c.close()
        c=context('en-US');pg=c.new_page();pending=[]
        pg.route(base,lambda route:route.fulfill(status=200,body=fallback,content_type='text/html'))
        pg.route('**/content/en.json',lambda route:pending.append(route))
        pg.goto(base);pg.wait_for_function('document.querySelector(".language").getAttribute("aria-busy")==="true"')
        pg.locator('[data-lang=ko]').click();assert_lang(pg,'ko')
        for route in pending:route.fulfill(status=200,content_type='application/json',body=json.dumps(en))
        pg.wait_for_timeout(100)
        assert pg.locator('html').get_attribute('lang')=='ko'
        assert pg.evaluate("localStorage.getItem('ffrep-language')")=='ko'
        c.close()
    test('failed fallback fetch is retryable; stale response cannot override choice',failure_and_race)
    browser.close()
server.shutdown()
(output/'browser-tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(f'ALL {len(results)} browser scenarios passed.')
