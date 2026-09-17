/* Progressive enhancement. Korean content and native accordions work without JS. */
(() => {
  'use strict';
  const configNode = document.getElementById('site-config');
  if (!configNode) return;
  let config;
  try { config = JSON.parse(configNode.textContent); } catch { return; }
  document.documentElement.classList.add('js');
  let ui = config.ui;
  let activeLocale = config.locales.default;
  let activeCategory = 'all';
  let requestId = 0;
  let toastTimer;
  const items = [...document.querySelectorAll('.faq-item')];
  const search = document.getElementById('faq-search');
  const clear = document.querySelector('.clear-search');
  const filters = [...document.querySelectorAll('.filter')];
  const expand = document.querySelector('.expand-all');
  const count = document.querySelector('.result-count');
  const empty = document.querySelector('.no-results');
  const normalize = text => text.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const valueAt = (object, key) => key.split('.').reduce((v, part) => v?.[part], object);
  const visibleItems = () => items.filter(item => !item.hidden);

  function updateExpandLabel() {
    const visible = visibleItems();
    const allOpen = visible.length > 0 && visible.every(item => item.open);
    expand.textContent = allOpen ? ui.collapseAll : ui.expandAll;
    expand.dataset.i18n = allOpen ? 'ui.collapseAll' : 'ui.expandAll';
    expand.disabled = visible.length === 0;
  }
  function applyFilters() {
    const words = normalize(search.value).split(' ').filter(Boolean);
    for (const item of items) {
      const haystack = normalize(item.querySelector('summary').textContent + ' ' + [...item.querySelectorAll('.answer p')].map(p => p.textContent).join(' '));
      const matches = (activeCategory === 'all' || activeCategory === item.dataset.topic) && words.every(word => haystack.includes(word));
      item.hidden = !matches;
      if (words.length && matches) item.open = true;
    }
    clear.hidden = search.value.length === 0;
    const total = visibleItems().length;
    count.textContent = ui.resultCount.replace('{count}', total);
    empty.hidden = total !== 0;
    filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.category === activeCategory)));
    updateExpandLabel();
  }
  search.addEventListener('input', applyFilters);
  clear.addEventListener('click', () => { search.value = ''; applyFilters(); search.focus(); });
  filters.forEach(button => button.addEventListener('click', () => { activeCategory = button.dataset.category; applyFilters(); }));
  expand.addEventListener('click', () => {
    const visible = visibleItems();
    const shouldOpen = !visible.every(item => item.open);
    visible.forEach(item => { item.open = shouldOpen; });
    updateExpandLabel();
  });
  items.forEach(item => item.addEventListener('toggle', updateExpandLabel));

  function openLinkedQuestion(scroll = true) {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const item = items.find(item => item.id === id);
    if (!item) return;
    search.value = ''; activeCategory = 'all'; applyFilters(); item.open = true;
    if (scroll) requestAnimationFrame(() => item.scrollIntoView({block:'start', behavior:'instant'}));
  }
  window.addEventListener('hashchange', () => openLinkedQuestion());

  function notify(message) {
    const toast = document.querySelector('.toast');
    clearTimeout(toastTimer); toast.textContent = message; toast.hidden = false;
    toastTimer = setTimeout(() => { toast.hidden = true; }, 3200);
  }
  async function copyLink(questionId = '') {
    const url = new URL(location.href);
    url.hash = questionId;
    // Avoid sharing unrelated query parameters. Preserve the selected language only.
    url.search = '';
    if (activeLocale !== config.locales.default) url.searchParams.set('lang',activeLocale);
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(url.href);
      notify(questionId ? ui.questionCopied : ui.copied);
    } catch {
      const dialog = document.querySelector('.copy-dialog');
      const field = document.getElementById('copy-url');
      field.value = url.href;
      if (typeof dialog.showModal === 'function') {
        if (!dialog.open) dialog.showModal();
        field.focus(); field.select();
      } else { window.prompt(ui.copyFallback, url.href); }
    }
  }
  document.querySelectorAll('[data-copy-question]').forEach(button => button.addEventListener('click', () => copyLink(button.dataset.copyQuestion)));
  document.querySelector('.share-page').addEventListener('click', () => copyLink());

  async function changeLanguage(code, writeUrl = true) {
    const locale = config.locales.languages.find(language => language.code === code && language.enabled);
    if (!locale || code === activeLocale) return;
    const thisRequest = ++requestId;
    const buttons = [...document.querySelectorAll('[data-lang]')];
    try {
      const response = await fetch(new URL(`../content/${code}.json`, document.querySelector('script[src$="site.js"]').src));
      if (!response.ok) throw new Error('Translation not available');
      const data = await response.json();
      if (thisRequest !== requestId) return;
      const textNodes = [...document.querySelectorAll('[data-i18n]')];
      const attrNodes = [...document.querySelectorAll('[data-i18n-attr]')];
      // Validate all bindings before replacing any text.
      textNodes.forEach(node => { if (typeof valueAt(data,node.dataset.i18n) !== 'string') throw new Error('Incomplete translation'); });
      attrNodes.forEach(node => node.dataset.i18nAttr.split(';').forEach(binding => { if (typeof valueAt(data,binding.split(':')[1]) !== 'string') throw new Error('Incomplete attributes'); }));
      if (data.meta?.lang !== code || !data.ui?.resultCount) throw new Error('Invalid translation');
      textNodes.forEach(node => { node.textContent = valueAt(data,node.dataset.i18n); });
      attrNodes.forEach(node => node.dataset.i18nAttr.split(';').forEach(binding => { const [attr,key] = binding.split(':'); node.setAttribute(attr,valueAt(data,key)); }));
      ui = data.ui; activeLocale = code;
      document.documentElement.lang = code;
      document.title = data.meta.title;
      document.querySelector('meta[name="description"]').content = data.meta.description;
      document.querySelector('meta[property="og:title"]').content = data.meta.title;
      document.querySelector('meta[property="og:description"]').content = data.meta.description;
      document.querySelector('meta[property="og:locale"]').content = code === 'ko' ? 'ko_KR' : 'en_US';
      buttons.forEach(button => button.setAttribute('aria-pressed',String(button.dataset.lang === code)));
      try { localStorage.setItem('ffrep-language',code); } catch { /* Privacy mode is supported. */ }
      if (writeUrl) {
        const url = new URL(location.href); url.searchParams.set('lang',code);
        history.replaceState(null,'',url);
      }
      applyFilters();
    } catch {
      // Leave the complete current page in place. Never show a partial translation.
      notify(ui.comingSoon);
    }
  }
  document.querySelectorAll('[data-lang]').forEach(button => button.addEventListener('click', () => changeLanguage(button.dataset.lang)));
  const englishReady = config.locales.languages.some(language => language.code === 'en' && language.enabled);
  document.querySelector('.language-status').hidden = englishReady;
  let preferred = new URL(location.href).searchParams.get('lang');
  if (!preferred) { try { preferred = localStorage.getItem('ffrep-language'); } catch { /* No storage required. */ } }
  if (preferred) changeLanguage(preferred,false);

  if ('IntersectionObserver' in window) {
    const links = [...document.querySelectorAll('.nav a')];
    const observer = new IntersectionObserver(entries => {
      const current = entries.filter(entry => entry.isIntersecting).sort((a,b) => b.intersectionRatio-a.intersectionRatio)[0];
      if (!current) return;
      links.forEach(link => {
        if (link.hash === `#${current.target.id}`) link.setAttribute('aria-current','location');
        else link.removeAttribute('aria-current');
      });
    }, {rootMargin:'-15% 0px -50% 0px'});
    document.querySelectorAll('main section[id]').forEach(section => observer.observe(section));
  }
  let printState = [];
  window.addEventListener('beforeprint', () => { printState=items.map(item=>({open:item.open,hidden:item.hidden})); items.forEach(item=>{item.hidden=false;item.open=true;}); });
  window.addEventListener('afterprint', () => { items.forEach((item,i)=>{if(printState[i]){item.open=printState[i].open;item.hidden=printState[i].hidden;}}); });
  applyFilters();
  openLinkedQuestion();
})();
