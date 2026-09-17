#!/usr/bin/env python3
"""Build the public static site using only Python's standard library."""
from __future__ import annotations
import argparse
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\{\{([A-Za-z0-9_.]+)\}\}')

# Original, illustrative geometry; not imported from an avatar or neural dataset.
SHOKI = '''<path d="M94 47L167 25L224 56L151 82ZM94 47V98L151 129V82M224 56V106L151 129M94 98L60 128L72 180H47M119 111L101 149L118 197H87M197 111L228 145L217 193H248M224 92L256 119L250 171H275"/>
<path d="M100 49L155 72L210 55M151 82V119M167 25V54M103 73L117 81M125 85L139 93"/>
<path d="M55 123H65V133H55ZM96 144H106V154H96ZM223 140H233V150H223ZM251 114H261V124H251Z"/>
<path d="M28 205H286" stroke-dasharray="3 8" opacity=".35"/>'''
YUMEKA = '''<path d="M69 12H99L109 23V49L99 60H69L59 49V23ZM77 60V72M92 60V72M44 81L77 72H92L125 81L113 124L97 146H72L56 124ZM72 146L60 172L68 195L58 232H80L86 193L85 170M97 146L109 172L101 195L111 232H89L83 193M44 81L25 121L33 152L21 164M125 81L144 121L136 152L148 164M56 124H113M77 72L69 108L85 127L100 108L92 72"/>
<path d="M20 117H30V127H20ZM139 117H149V127H139ZM63 190H73V200H63ZM96 190H106V200H96Z"/>
<path d="M9 246H161" stroke-dasharray="3 8" opacity=".35"/>'''

def lookup(data, path):
    value = data
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value, list) else value[part]
    if not isinstance(value, str):
        raise ValueError(f'Text key must be a string: {path}')
    return value


def text(tag, key, attrs=''):
    return f'<{tag} data-i18n="{key}"{(" " + attrs) if attrs else ""}>{{{{{key}}}}}</{tag}>'


def flatten(value, prefix=''):
    if isinstance(value, dict):
        return {k: v for key, child in value.items() for k, v in flatten(child, f'{prefix}.{key}' if prefix else key).items()}
    if isinstance(value, list):
        return {k: v for i, child in enumerate(value) for k, v in flatten(child, f'{prefix}.{i}').items()}
    return {prefix: value}


def load():
    manifest = json.loads((ROOT/'content/locales.json').read_text('utf-8'))
    default = manifest['default']
    if default != 'ko':
        raise ValueError('The committed fallback is Korean. Keep ko as default.')
    data = json.loads((ROOT/f'content/{default}.json').read_text('utf-8'))
    ids = [q['id'] for q in data['faq']['items']]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[a-z0-9-]+', i) for i in ids):
        raise ValueError('FAQ IDs must be unique, URL-safe, and stable across locales.')
    locales = manifest['languages']
    if len({x['code'] for x in locales}) != len(locales):
        raise ValueError('Duplicate locale codes')
    for lang in locales:
        if not re.fullmatch(r'[a-z]{2}(?:-[A-Z]{2})?', lang['code']):
            raise ValueError('Invalid locale code')
        if not lang['enabled']:
            continue
        translated = json.loads((ROOT/f"content/{lang['code']}.json").read_text('utf-8'))
        if translated['meta']['lang'] != lang['code'] or flatten(translated).keys() != flatten(data).keys():
            raise ValueError(f"Translation schema mismatch: {lang['code']}")
        for key, value in flatten(data).items():
            if (key.endswith('.id') or key.endswith('.category')) and flatten(translated)[key] != value:
                raise ValueError(f'Stable identifier changed: {key}')
        if any(not isinstance(v, str) for v in flatten(translated).values()):
            raise ValueError('Content values must be strings')
    return data, manifest


def render(data, manifest):
    blocks = {}
    blocks['_language_buttons'] = ''.join(
        f'<button type="button" data-lang="{l["code"]}" aria-label="{html.escape(l["label"], quote=True)}" '
        f'aria-pressed="{str(l["code"] == manifest["default"]).lower()}"'
        + ('' if l['enabled'] else ' disabled title="{{ui.comingSoon}}" data-i18n-attr="title:ui.comingSoon"')
        + f'>{l["code"].upper()}</button>' for l in manifest['languages'])
    blocks['_essentials'] = ''.join(f'<article class="essential"><span class="essential-number">0{i+1}</span><div>' + text('h2', f'essentials.{i}.label') + text('p', f'essentials.{i}.text') + '</div></article>' for i in range(len(data['essentials'])))
    blocks['_about_paragraphs'] = ''.join(text('p', f'about.paragraphs.{i}') for i in range(len(data['about']['paragraphs'])))
    blocks['_flow'] = ''.join(text('div', f'about.loop.{i}', 'class="flow-step"') for i in range(len(data['about']['loop'])))
    body_cards = []
    for i, body in enumerate(data['bodies']['items']):
        geometry = SHOKI if body['id'] == 'shoki' else YUMEKA
        view = '0 0 320 240' if body['id'] == 'shoki' else '-75 0 320 258'
        body_cards.append(f'<article class="body-card" id="body-{body["id"]}"><div class="body-card-top"><span class="mono">BODY / 0{i+1}</span>' + text('span', f'bodies.items.{i}.kind') + f'</div><svg class="body-art" viewBox="{view}" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">{geometry}</svg><div class="body-name">' + text('h3',f'bodies.items.{i}.name')+text('span',f'bodies.items.{i}.nameKo')+'</div>'+text('div',f'bodies.items.{i}.tag','class="body-tag"')+text('p',f'bodies.items.{i}.text')+text('p',f'bodies.items.{i}.note','class="body-note"')+'</article>')
    blocks['_bodies'] = ''.join(body_cards)
    blocks['_filters'] = ''.join(text('button', f'faq.categories.{i}.label', f'type="button" class="filter" data-category="{c["id"]}" aria-pressed="false"') for i, c in enumerate(data['faq']['categories']))
    faqs = []
    for i, q in enumerate(data['faq']['items']):
        answers = ''.join(text('p',f'faq.items.{i}.answer.{j}') for j in range(len(q['answer'])))
        faqs.append(f'<details class="faq-item" id="{q["id"]}" data-topic="{q["category"]}"'+(' open' if i == 0 else '')+'><summary><span class="q-number" aria-hidden="true">'+f'{i+1:02d}'+'</span>'+text('span',f'faq.items.{i}.question')+'<span class="plus" aria-hidden="true"></span></summary><div class="answer">'+answers+f'<button type="button" class="permalink js-only" data-copy-question="{q["id"]}"><span aria-hidden="true">↗ </span>'+text('span','ui.questionLink')+'</button></div></details>')
    blocks['_faqs'] = ''.join(faqs)
    blocks['_reading_cards'] = ''.join('<article class="reading-card">'+text('span',f'reading.cards.{i}.label','class="reading-mode"')+text('h3',f'reading.cards.{i}.title')+text('p',f'reading.cards.{i}.text')+'</article>' for i in range(len(data['reading']['cards'])))
    blocks['_shoki_geometry'], blocks['_yumeka_geometry'] = SHOKI, YUMEKA
    blocks['_site_config'] = json.dumps({'locales':manifest, 'ui':data['ui']},ensure_ascii=False).replace('<', chr(92)+'u003c').replace('>', chr(92)+'u003e').replace('&', chr(92)+'u0026')
    template = (ROOT/'templates/page.html').read_text('utf-8')
    for key, value in blocks.items():
        template = template.replace('{{'+key+'}}', value)
    result = TOKEN.sub(lambda m: html.escape(lookup(data,m[1]),quote=True), template)
    if '{{' in result or '}}' in result:
        # JSON in the config may have consecutive braces. Only unresolved placeholders are errors.
        if re.search(r'\{\{[a-zA-Z_]', result):
            raise ValueError('Unresolved placeholder')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail when generated index.html is stale.')
    args=parser.parse_args()
    data, manifest = load()
    rendered = render(data,manifest)
    index=ROOT/'index.html'
    if args.check:
        if not index.exists() or index.read_text('utf-8') != rendered:
            raise SystemExit('index.html is stale. Run python scripts/build.py.')
    else:
        index.write_text(rendered,'utf-8')
    out=ROOT/'_site'
    if out.exists(): shutil.rmtree(out)
    out.mkdir()
    (out/'index.html').write_text(rendered,'utf-8')
    shutil.copytree(ROOT/'assets',out/'assets')
    (out/'content').mkdir()
    shutil.copy2(ROOT/'content/locales.json',out/'content/locales.json')
    for lang in manifest['languages']:
        if lang['enabled']: shutil.copy2(ROOT/f"content/{lang['code']}.json", out/f"content/{lang['code']}.json")
    (out/'.nojekyll').touch()
    print(f'Built {len(data["faq"]["items"])} Korean FAQs; enabled locales: '+', '.join(l['code'] for l in manifest['languages'] if l['enabled']))

if __name__=='__main__': main()
