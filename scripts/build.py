#!/usr/bin/env python3
"""Build the minimal public FAQ; prose and links are escaped, media allowlisted."""
from __future__ import annotations
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\{\{([A-Za-z0-9_.]+)\}\}')
LINK = re.compile(r'\[([^\]\n]+)\]\((https://[^\s)]+)\)')
MEDIA = ('yumeka-training.mp4', 'yumeka-training.webp', 'shoki-training.mp4',
         'shoki-training.webp', 'yumeka-model.webp', 'malecns-poster.webp')
POSTS = {'main': 'https://x.com/yakshawan/status/2099806286468849665',
         'shoki': 'https://x.com/yakshawan/status/2099813850426245440'}


def lookup(data, path):
    value = data
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value, list) else value[part]
    if not isinstance(value, str):
        raise ValueError(f'Expected text: {path}')
    return value


def rich(value):
    """Only explicit HTTPS markdown links are allowed; raw HTML is never trusted."""
    parts, end = [], 0
    for match in LINK.finditer(value):
        url = match[2]
        if not urlparse(url).hostname or '<' in url or '>' in url:
            continue
        parts.append(html.escape(value[end:match.start()]))
        parts.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(match[1])}</a>')
        end = match.end()
    parts.append(html.escape(value[end:]))
    return ''.join(parts)


def flatten(value, prefix=''):
    if isinstance(value, dict):
        return {k: v for key, child in value.items() for k, v in flatten(child, f'{prefix}.{key}' if prefix else key).items()}
    if isinstance(value, list):
        return {k: v for i, child in enumerate(value) for k, v in flatten(child, f'{prefix}.{i}').items()}
    return {prefix: value}


def load():
    manifest = json.loads((ROOT/'content/locales.json').read_text('utf-8'))
    if manifest['default'] != 'ko':
        raise ValueError('Korean is the static fallback.')
    data = json.loads((ROOT/'content/ko.json').read_text('utf-8'))
    ids = [q['id'] for q in data['faq']]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[a-z0-9-]+', i) for i in ids):
        raise ValueError('FAQ IDs must be unique and URL safe.')
    base = flatten(data)
    if not all(isinstance(v, str) for v in base.values()):
        raise ValueError('Content leaf values must be text.')
    languages = manifest['languages']
    if len({l['code'] for l in languages}) != len(languages):
        raise ValueError('Duplicate locale.')
    for language in languages:
        code = language['code']
        if not re.fullmatch(r'[a-z]{2}', code):
            raise ValueError('Invalid locale code.')
        if not language['enabled']:
            continue
        other = json.loads((ROOT/f'content/{code}.json').read_text('utf-8'))
        target = flatten(other)
        if target.keys() != base.keys() or other['meta']['lang'] != code:
            raise ValueError('Translation is incomplete: '+code)
        for key, value in base.items():
            if not isinstance(target[key], str):
                raise ValueError('Translation value must be text: '+key)
            if key.endswith(('.id','.media')) and target[key] != value:
                raise ValueError('Translation changed a stable ID: '+key)
    return data, manifest


def tag(name, key, attrs=''):
    return f'<{name} data-i18n="{key}"{(" "+attrs) if attrs else ""}>{{{{{key}}}}}</{name}>'


def video(which, main=False):
    basename = 'yumeka-training' if main else 'shoki-training'
    prefix = 'main' if main else 'shoki'
    cls = 'main-film' if main else 'training-film'
    return (f'<figure class="{cls}"><video controls playsinline preload="none" width="1280" height="670" '
            f'poster="./assets/media/{basename}.webp" aria-describedby="{prefix}-description">'
            f'<source src="./assets/media/{basename}.mp4" type="video/mp4">'
            +tag('span','ui.videoUnsupported')+'</video>'
            +tag('p',f'ui.{prefix}Description',f'id="{prefix}-description" class="sr-only"')
            +f'<figcaption class="caption">'+tag('span',f'ui.{prefix}Caption')
            +f'<a href="{POSTS[which]}" target="_blank" rel="noopener noreferrer" data-i18n="ui.originalPost">{{{{ui.originalPost}}}}</a></figcaption>'
            +tag('p','ui.loadError','class="media-error" role="status" hidden')+'</figure>')


def media(name):
    if name == 'shoki-training':
        return video('shoki')
    if name == 'yumeka-model':
        return ('<figure class="model-figure"><a href="https://booth.pm/en/items/8672657" target="_blank" rel="noopener noreferrer">'
                '<img src="./assets/media/yumeka-model.webp" width="800" height="800" loading="lazy" decoding="async" alt="{{ui.modelAlt}}" data-i18n-attr="alt:ui.modelAlt"></a>'
                +tag('figcaption','ui.modelCaption')+'</figure>')
    if name == 'malecns':
        return ('<figure class="reference-film"><div class="reference-player">'
                '<button class="reference-cover js-only" type="button" data-video="NFeNxwjzueg" aria-label="{{ui.videoTitle}}" data-i18n-attr="aria-label:ui.videoTitle">'
                '<img src="./assets/media/malecns-poster.webp" width="480" height="360" loading="lazy" decoding="async" alt="">'
                +tag('span','ui.playReference')+'</button>'
                '<noscript><a href="https://www.youtube.com/watch?v=NFeNxwjzueg" target="_blank" rel="noopener noreferrer">'
                '<img src="./assets/media/malecns-poster.webp" width="480" height="360" alt="{{ui.videoTitle}}" loading="lazy">'
                '{{ui.playReference}}</a></noscript></div><figcaption>'
                +tag('span','ui.referenceCaption')
                +'<a href="https://male-cns.janelia.org/media/" target="_blank" rel="noopener noreferrer" data-i18n="ui.referenceSource">{{ui.referenceSource}}</a></figcaption></figure>')
    raise ValueError('Media not allowlisted: '+name)


def render(data, manifest):
    languages = ''.join(f'<button type="button" data-lang="{l["code"]}" aria-label="{html.escape(l["label"],quote=True)}" aria-pressed="{str(l["code"]==manifest["default"]).lower()}"'
        +('' if l['enabled'] else ' disabled title="{{ui.englishSoon}}"')+f'>{l["code"].upper()}</button>' for l in manifest['languages'])
    questions = []
    for i, question in enumerate(data['faq']):
        answers = ''.join(f'<p data-rich="faq.{i}.answer.{j}">{rich(p)}</p>' for j,p in enumerate(question['answer']))
        picture = media(question['media']) if question.get('media') else ''
        questions.append(f'<details class="faq-item" id="{question["id"]}"><summary><span class="question-number">{i+1:02d}</span>'
            +tag('span',f'faq.{i}.question')+'<span class="indicator" aria-hidden="true">+</span></summary><div class="answer">'+answers+picture+'</div></details>')
    config = json.dumps({'locales':manifest, 'ui':data['ui']},ensure_ascii=False).replace('<',r'\u003c').replace('>',r'\u003e').replace('&',r'\u0026')
    blocks = {'_languages':languages, '_main_video':video('main',True), '_faqs':''.join(questions), '_config':config}
    result = (ROOT/'templates/page.html').read_text('utf-8')
    for key, value in blocks.items():
        result=result.replace('{{'+key+'}}',value)
    return TOKEN.sub(lambda m:html.escape(lookup(data,m[1]),quote=True),result)


def main():
    data, manifest = load()
    rendered=render(data,manifest)
    (ROOT/'index.html').write_text(rendered,'utf-8')
    out=ROOT/'_site'
    if out.exists(): shutil.rmtree(out)
    (out/'assets/media').mkdir(parents=True)
    (out/'content').mkdir()
    (out/'index.html').write_text(rendered,'utf-8')
    for name in ('site.css','site.js','favicon.svg'):
        shutil.copy2(ROOT/'assets'/name,out/'assets'/name)
    for name in MEDIA:
        path=ROOT/'assets/media'/name
        if not path.is_file(): raise FileNotFoundError('Missing public asset: '+name)
        shutil.copy2(path,out/'assets/media'/name)
    shutil.copy2(ROOT/'content/locales.json',out/'content/locales.json')
    for language in manifest['languages']:
        if language['enabled']:
            name=language['code']+'.json'
            shutil.copy2(ROOT/'content'/name,out/'content'/name)
    (out/'.nojekyll').touch()
    print(f'Built {len(data["faq"])} FAQs with original project media.')

if __name__=='__main__':main()
