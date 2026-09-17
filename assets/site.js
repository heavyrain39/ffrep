/* Native FAQ disclosure and media work without JavaScript. No tracking. */
(() => {
  'use strict';
  const node = document.getElementById('site-config');
  if (!node) return;
  let config;
  try { config = JSON.parse(node.textContent); } catch { return; }
  document.documentElement.classList.add('js');
  let current = config.locales.default;
  let ui = config.ui;
  let sequence = 0;
  const get = (data, key) => key.split('.').reduce((v, k) => v?.[k],data);
  const items = [...document.querySelectorAll('.faq-item')];
  const languages = [...document.querySelectorAll('[data-lang]')];

  // Small allowlisted Markdown subset, built with DOM APIs, never innerHTML.
  function rich(text) {
    const fragment = document.createDocumentFragment();
    const pattern = /\[([^\]\n]+)\]\((https:\/\/[^\s)]+)\)/g;
    let end=0;
    for (const match of text.matchAll(pattern)) {
      let url;
      try { url = new URL(match[2]); } catch { continue; }
      if (url.protocol !== 'https:' || /[<>]/.test(match[2])) continue;
      fragment.append(document.createTextNode(text.slice(end,match.index)));
      const link=document.createElement('a');
      link.href=url.href; link.target='_blank'; link.rel='noopener noreferrer';
      link.textContent=match[1]; fragment.append(link); end=match.index+match[0].length;
    }
    fragment.append(document.createTextNode(text.slice(end)));
    return fragment;
  }
  async function setLanguage(code, updateAddress=true) {
    const request=++sequence;
    if (code===current) return;
    if (!config.locales.languages.some(l=>l.code===code && l.enabled)) return;
    try {
      const response=await fetch(new URL(`../content/${code}.json`,document.querySelector('script[src$="site.js"]').src));
      if (!response.ok) throw new Error('Translation unavailable');
      const data=await response.json();
      if (request!==sequence) return;
      const textNodes=[...document.querySelectorAll('[data-i18n]')];
      const richNodes=[...document.querySelectorAll('[data-rich]')];
      const attrs=[...document.querySelectorAll('[data-i18n-attr]')];
      for (const n of [...textNodes,...richNodes]) {
        if (typeof get(data,n.dataset.i18n || n.dataset.rich)!=='string') throw new Error('Missing text');
      }
      for (const n of attrs) {
        for (const binding of n.dataset.i18nAttr.split(';')) {
          if (typeof get(data,binding.split(':')[1])!=='string') throw new Error('Missing attribute');
        }
      }
      if (data.meta.lang!==code) throw new Error('Wrong language');
      textNodes.forEach(n=>{n.textContent=get(data,n.dataset.i18n);});
      richNodes.forEach(n=>n.replaceChildren(rich(get(data,n.dataset.rich))));
      attrs.forEach(n=>n.dataset.i18nAttr.split(';').forEach(binding=>{const [attr,key]=binding.split(':');n.setAttribute(attr,get(data,key));}));
      current=code;ui=data.ui;document.documentElement.lang=code;document.title=data.meta.title;
      document.querySelector('meta[name="description"]').content=data.meta.description;
      document.querySelector('meta[property="og:title"]').content=data.meta.title;
      document.querySelector('meta[property="og:description"]').content=data.meta.description;
      document.querySelector('meta[property="og:locale"]').content=code==='ko'?'ko_KR':'en_US';
      languages.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===code)));
      try {localStorage.setItem('ffrep-language',code);} catch {}
      if (updateAddress) {const url=new URL(location.href);url.searchParams.set('lang',code);history.replaceState(null,'',url);}
    } catch {
      // The existing complete translation remains readable on any load failure.
      const selected=languages.find(b=>b.dataset.lang===code);
      if (selected) selected.title=ui.englishSoon;
    }
  }
  languages.forEach(b=>b.addEventListener('click',()=>setLanguage(b.dataset.lang)));
  let preferred=new URL(location.href).searchParams.get('lang');
  if (!preferred) {try {preferred=localStorage.getItem('ffrep-language');} catch {}}
  if (preferred) setLanguage(preferred,false);

  document.querySelectorAll('[data-video]').forEach(button=>button.addEventListener('click',()=>{
    if (button.dataset.video!=='NFeNxwjzueg') return;
    const iframe=document.createElement('iframe');
    iframe.src='https://www.youtube-nocookie.com/embed/NFeNxwjzueg?autoplay=1&rel=0';
    iframe.title=ui.videoTitle;iframe.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';
    iframe.allowFullscreen=true;iframe.referrerPolicy='strict-origin-when-cross-origin';
    button.replaceWith(iframe);iframe.focus();
  }));
  document.querySelectorAll('video').forEach(video=>{
    const showError=()=>{const message=video.closest('figure').querySelector('.media-error');if(message)message.hidden=false;};
    video.addEventListener('error',showError);
    video.querySelectorAll('source').forEach(source=>source.addEventListener('error',showError));
    video.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==video)other.pause();}));
  });
  items.forEach(item=>item.addEventListener('toggle',()=>{if(!item.open)item.querySelectorAll('video').forEach(video=>video.pause());}));
  let beforePrint=[];
  window.addEventListener('beforeprint',()=>{beforePrint=items.map(d=>d.open);items.forEach(d=>{d.open=true;});});
  window.addEventListener('afterprint',()=>{items.forEach((d,i)=>{d.open=beforePrint[i]??d.open;});});
})();
