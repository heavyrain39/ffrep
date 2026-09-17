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
  const get = (data, key) => key.split('.').reduce((v, k) => v?.[k], data);
  const items = [...document.querySelectorAll('.faq-item')];
  const languages = [...document.querySelectorAll('[data-lang]')];
  const group = document.querySelector('.language');
  const cache = new Map(Object.entries(config.translations || {}));
  const storageKey = 'ffrep-language';
  const errors = {
    ko: '언어를 불러오지 못했습니다. 다시 눌러 주세요.',
    en: "Couldn't load this language. Please try again."
  };
  const status = document.createElement('span');
  status.className = 'sr-only';
  status.setAttribute('role', 'status');
  group.append(status);

  function enabled(code) {
    if (typeof code !== 'string') return null;
    const normalized = code.toLowerCase();
    return config.locales.languages.some(l => l.code === normalized && l.enabled) ? normalized : null;
  }
  function preferredLanguage() {
    // Explicit link > deliberate saved choice > browser's primary language.
    const requested = enabled(new URL(location.href).searchParams.get('lang'));
    if (requested) return requested;
    try {
      const saved = enabled(localStorage.getItem(storageKey));
      if (saved) return saved;
    } catch { /* Restricted storage must not disable automatic selection. */ }
    const primary = navigator.languages?.[0] || navigator.language || '';
    return enabled(/^ko(?:-|$)/i.test(primary) ? 'ko' : 'en') || config.locales.default;
  }
  function rememberChoice(code) {
    // Automatic detection and shared URLs do not overwrite a deliberate choice.
    try { localStorage.setItem(storageKey, code); } catch {}
    try {
      const url = new URL(location.href);
      url.searchParams.set('lang', code);
      history.replaceState(null, '', url);
    } catch { /* Also support local-file previews and restrictive browsers. */ }
  }

  // Small allowlisted Markdown subset, built with DOM APIs, never innerHTML.
  function rich(text) {
    const fragment = document.createDocumentFragment();
    const pattern = /\[([^\]\n]+)\]\((https:\/\/[^\s)]+)\)/g;
    let end = 0;
    for (const match of text.matchAll(pattern)) {
      let url;
      try { url = new URL(match[2]); } catch { continue; }
      if (url.protocol !== 'https:' || /[<>]/.test(match[2])) continue;
      fragment.append(document.createTextNode(text.slice(end, match.index)));
      const link = document.createElement('a');
      link.href = url.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = match[1];
      fragment.append(link);
      end = match.index + match[0].length;
    }
    fragment.append(document.createTextNode(text.slice(end)));
    return fragment;
  }
  function loadLanguage(code) {
    if (!cache.has(code)) {
      const script = document.querySelector('script[src$="site.js"]');
      const url = new URL(`../content/${code}.json`, script.src);
      cache.set(code, fetch(url).then(response => {
        if (!response.ok) throw new Error('Translation unavailable');
        return response.json();
      }).catch(error => {
        cache.delete(code);
        throw error;
      }));
    }
    return cache.get(code);
  }
  async function setLanguage(code, manual = false) {
    code = enabled(code);
    if (!code) return;
    const request = ++sequence;
    status.textContent = '';
    if (code === current) {
      // Selecting KO while EN is loading must cancel EN and still save KO.
      group.removeAttribute('aria-busy');
      languages.forEach(button => button.removeAttribute('title'));
      if (manual) rememberChoice(code);
      return;
    }
    group.setAttribute('aria-busy', 'true');
    try {
      const data = await loadLanguage(code);
      if (request !== sequence) return;
      const textNodes = [...document.querySelectorAll('[data-i18n]')];
      const richNodes = [...document.querySelectorAll('[data-rich]')];
      const attrs = [...document.querySelectorAll('[data-i18n-attr]')];
      // Prepare and validate every replacement before touching the current page.
      for (const n of [...textNodes, ...richNodes]) {
        if (typeof get(data, n.dataset.i18n || n.dataset.rich) !== 'string') throw new Error('Missing text');
      }
      for (const n of attrs) {
        for (const binding of n.dataset.i18nAttr.split(';')) {
          if (typeof get(data, binding.split(':')[1]) !== 'string') throw new Error('Missing attribute');
        }
      }
      if (data.meta?.lang !== code || typeof data.meta.title !== 'string' ||
          typeof data.meta.description !== 'string' || typeof data.ui?.videoTitle !== 'string') {
        throw new Error('Invalid translation metadata');
      }
      if (!Array.isArray(data.faq) || data.faq.length !== items.length ||
          data.faq.some((q, i) => q.id !== items[i].id)) {
        throw new Error('Translation changed question identities');
      }
      const fragments = richNodes.map(n => rich(get(data, n.dataset.rich)));
      textNodes.forEach(n => { n.textContent = get(data, n.dataset.i18n); });
      richNodes.forEach((n, i) => n.replaceChildren(fragments[i]));
      attrs.forEach(n => n.dataset.i18nAttr.split(';').forEach(binding => {
        const [attr, key] = binding.split(':');
        n.setAttribute(attr, get(data, key));
      }));
      current = code;
      ui = data.ui;
      document.documentElement.lang = code;
      document.title = data.meta.title;
      document.querySelector('meta[name="description"]').content = data.meta.description;
      document.querySelector('meta[property="og:title"]').content = data.meta.title;
      document.querySelector('meta[property="og:description"]').content = data.meta.description;
      document.querySelector('meta[property="og:locale"]').content = code === 'ko' ? 'ko_KR' : 'en_US';
      languages.forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.lang === code));
        button.removeAttribute('title');
      });
      if (manual) rememberChoice(code);
    } catch {
      if (request !== sequence) return;
      cache.delete(code);
      // Leave the entire previous language intact and let the user retry.
      status.textContent = errors[current] || errors.en;
      const selected = languages.find(button => button.dataset.lang === code);
      if (selected) selected.title = status.textContent;
    } finally {
      if (request === sequence) group.removeAttribute('aria-busy');
    }
  }
  languages.forEach(button => button.addEventListener('click', () => setLanguage(button.dataset.lang, true)));
  setLanguage(preferredLanguage());
  window.addEventListener('languagechange', () => setLanguage(preferredLanguage()));
  window.addEventListener('popstate', () => setLanguage(preferredLanguage()));

  document.querySelectorAll('[data-video]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.video !== 'NFeNxwjzueg') return;
    const iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube-nocookie.com/embed/NFeNxwjzueg?autoplay=1&rel=0';
    iframe.title = ui.videoTitle;
    iframe.dataset.i18nAttr = 'title:ui.videoTitle';
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    button.replaceWith(iframe);
    iframe.focus();
  }));
  document.querySelectorAll('video').forEach(video => {
    const showError = () => {
      const message = video.closest('figure').querySelector('.media-error');
      if (message) message.hidden = false;
    };
    video.addEventListener('error', showError);
    video.querySelectorAll('source').forEach(source => source.addEventListener('error', showError));
    video.addEventListener('play', () => document.querySelectorAll('video').forEach(other => {
      if (other !== video) other.pause();
    }));
  });
  items.forEach(item => item.addEventListener('toggle', () => {
    if (!item.open) item.querySelectorAll('video').forEach(video => video.pause());
  }));
  let beforePrint = [];
  window.addEventListener('beforeprint', () => {
    beforePrint = items.map(d => d.open);
    items.forEach(d => { d.open = true; });
  });
  window.addEventListener('afterprint', () => {
    items.forEach((d, i) => { d.open = beforePrint[i] ?? d.open; });
  });
})();
