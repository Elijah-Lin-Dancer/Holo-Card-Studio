// HoloLab Gallery · 展厅（纯静态，JSON 清单驱动）+ 全息动效引擎
// 手写实现：粒子背景 / 光标光晕 / 标题逐字动画 / 卡片 staggered 入场 / 3D tilt / 双语切换

const I18N = window.HoloLabI18n;
const THEME = window.HoloLabTheme;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
/* HTML 转义：cards.json 为可公开投稿数据源，展示前必须转义防存储型 XSS */
function escHtml(s) {
  return String(s == null ? '' : s)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

/* ============ 1. 语言 / 主题切换器 ============ */
const langBtn = document.getElementById('lang-btn');
const themeBtn = document.getElementById('theme-btn');

function paintLangBtn() {
  langBtn.textContent = I18N.get() === 'zh' ? 'EN' : '中文';
}
function setLang(l) {
  I18N.setLang(l);
  paintLangBtn();
  reSplitTitle();
  /* 语言切换：重渲染动态生成的 UI（分类 chips、锁定卡徽标、私藏提示等） */
  renderChips();
  render();
  paintTourBtn();   /* 导览按钮文案跟随语言 */
}
langBtn.addEventListener('click', () => setLang(I18N.get() === 'zh' ? 'en' : 'zh'));
themeBtn.addEventListener('click', () => THEME.toggle());
window.__hololabOnTheme = () => { /* 粒子颜色随主题更新由 starfield 内部处理 */ };
I18N.apply();
paintLangBtn();

/* ============ 2. 星尘粒子背景（Canvas） ============ */
(function starfield() {
  const cv = document.getElementById('starfield');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  let W, H, stars = [], raf = null, mx = 0, my = 0;
  function palette() {
    const d = THEME.get() === 'dark';
    return d ? ['255,255,255', '201,168,106', '127,212,255'] : ['64,52,30', '150,102,26', '8,88,130'];
  }
  function resize() { W = cv.width = innerWidth; H = cv.height = innerHeight; }
  function make() {
    const density = finePointer ? 5200 : 8000;
    const n = Math.min(420, Math.floor(W * H / density));
    const pal = palette();
    stars = [];
    for (let i = 0; i < n; i++) {
      stars.push({
        x: Math.random() * W, y: Math.random() * H,
        r: Math.random() * 2.0 + 1.2,
        a: Math.random() * 0.45 + 0.25,
        s: Math.random() * 0.5 + 0.1,
        drift: (Math.random() - 0.5) * 0.3,
        tw: Math.random() * Math.PI * 2,
        tws: 0.02 + Math.random() * 0.05,
        halo: Math.random() < 0.28,
        depth: 0.3 + Math.random() * 1.25,
        c: pal[i % 3]
      });
    }
  }
  function step() {
    ctx.clearRect(0, 0, W, H);
    for (const st of stars) {
      st.y -= st.s;
      if (st.y < -2) { st.y = H + 2; st.x = Math.random() * W; }
      st.x += st.drift;
      if (st.x < -4) st.x = W + 4; else if (st.x > W + 4) st.x = -4;
      st.tw += st.tws;
      const pulse = 0.5 + 0.5 * Math.sin(st.tw);
      const al = st.a * (0.3 + 0.7 * pulse);
      const px = st.x - (mx - W / 2) * 0.035 * st.depth;
      const py = st.y - (my - H / 2) * 0.02 * st.depth;
      const r = st.halo ? st.r * (1 + 0.3 * Math.sin(st.tw * 0.7)) : st.r;
      if (st.halo) {
        ctx.fillStyle = 'rgba(' + st.c + ',' + (al * 0.16).toFixed(3) + ')';
        ctx.beginPath(); ctx.arc(px, py, r * 3.4, 0, 6.2832); ctx.fill();
      }
      ctx.fillStyle = 'rgba(' + st.c + ',' + al.toFixed(3) + ')';
      ctx.beginPath(); ctx.arc(px, py, r, 0, 6.2832); ctx.fill();
    }
    if (!reduceMotion) raf = requestAnimationFrame(step);
  }
  resize(); make();
  if (reduceMotion) { step(); return; }
  step();
  addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; }, { passive: true });
  addEventListener('resize', () => { resize(); make(); });
  const origOnTheme = window.__hololabOnTheme;
  window.__hololabOnTheme = (th) => { make(); if (origOnTheme) origOnTheme(th); };
})();

/* ============ 3. 光标光晕（桌面） ============ */
(function cursorGlow() {
  const g = document.querySelector('.cursor-glow');
  if (!g || !finePointer || reduceMotion) return;
  let tx = innerWidth / 2, ty = innerHeight / 2, cx = tx, cy = ty, raf = null;
  addEventListener('mousemove', e => { tx = e.clientX; ty = e.clientY; });
  (function loop() {
    cx += (tx - cx) * 0.12; cy += (ty - cy) * 0.12;
    g.style.transform = 'translate(' + (cx - 170) + 'px,' + (cy - 170) + 'px)';
    raf = requestAnimationFrame(loop);
  })();
})();

/* ============ 4. Hero 标题逐字动画 ============ */
const heroTitle = document.getElementById('hero-title');
function splitTitle(el) {
  const text = el.textContent;
  el.textContent = '';
  el.classList.remove('in');
  for (const ch of text) {
    if (ch === ' ' || ch === '　') { el.appendChild(document.createTextNode(' ')); continue; }
    const w = document.createElement('span');
    w.className = 'w';
    const s = document.createElement('span');
    s.textContent = ch;
    w.appendChild(s);
    el.appendChild(w);
  }
  // 强制回流后触发入场
  void el.offsetWidth;
  requestAnimationFrame(() => el.classList.add('in'));
}
function reSplitTitle() { if (heroTitle) splitTitle(heroTitle); if (window.__hololabSyncShine) window.__hololabSyncShine(); }
if (heroTitle && !reduceMotion) reSplitTitle();

/* ============ 5. 卡片加载 + 动效 ============ */
const grid = document.getElementById('gallery');
const empty = grid.querySelector('.empty');
let activeFilter = 'all';
let activeCategory = 'all';   /* 大分类（流媒体式）：all | football | meme | game | history | art | travel */
let cards = [];
let currentEls = [];
let curated = {};   /* curation.json：id → {zh,en} 创作手记 */
let viewState = 'grid';   /* 'grid' | 'curated' */

async function load() {
  const [res, cur] = await Promise.all([
    fetch('./cards.json'),
    fetch('./curation.json').then(r => r.ok ? r.json() : {}).catch(() => ({}))
  ]);
  const data = await res.json();
  cards = data.cards || [];
  curated = cur || {};
  const stat = document.getElementById('stat-cards');
  if (stat) animateCount(stat, cards.length);
  renderChips();
  render();
}

/* ============ 5a. 视图切换：网格 / 策展时间线 ============ */
const curationSec = document.getElementById('curation');
const viewSwitch = document.querySelector('.view-switch');
function setView(v) {
  viewState = v;
  document.querySelectorAll('.view-btn').forEach(b => {
    const on = b.dataset.view === v;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  grid.hidden = v !== 'grid';
  if (curationSec) curationSec.hidden = v !== 'curated';
  if (v !== 'grid') stopTour();   /* 切到策展视图时中止导览 */
  if (tourBtn) tourBtn.disabled = (v !== 'grid' || reduceMotion);   /* 导览仅作用于网格视图 */
  render();
}
if (viewSwitch) {
  viewSwitch.addEventListener('click', e => {
    const b = e.target.closest('.view-btn');
    if (!b) return;
    setView(b.dataset.view);
  });
}

/* 自动分类（流媒体式）：第一行 = 全部 + 6 大分类（按 card.category），
   选中某分类后第二行 = 该分类内的 style_tags 子标签（二次收窄，默认折叠）。
   碎片 style_tags 不再作为顶层筛选项，只作分类内细分。 */
const filtersBox = document.getElementById('filters');
const CATEGORIES = ['all', 'football', 'meme', 'game', 'history', 'art', 'travel'];
const SUBSELECT_EXCLUDE = ['足球', '梗卡']; /* 分类通用词：已由大分类 chips 表达，不再当子标签 */
const FILTERS_COLLAPSE_AFTER = 7; // 子标签默认显示数量，其余收进"更多"
function renderChips() {
  if (!filtersBox) return;
  const t = (key, fb) => (typeof window.HoloLabI18n !== 'undefined' ? window.HoloLabI18n.t(key) : fb);
  const mk = (f, label, parent, isActive, kind) => {
    const b = document.createElement('button');
    const cls = ['chip'];
    if (kind === 'cat') cls.push('chip-cat');
    if (kind === 'tag') cls.push('chip-tag');
    if (isActive) cls.push('active');
    b.className = cls.join(' ');
    b.dataset.filter = f;
    b.textContent = label;
    b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    parent.appendChild(b);
    return b;
  };
  filtersBox.innerHTML = '';
  filtersBox.classList.remove('expanded');

  // 结构化分行：主分类独占一行（.filter-row-main），子标签整行另起（.filter-row-sub）
  const rowMain = document.createElement('div');
  rowMain.className = 'filter-row filter-row-main';
  const rowSub = document.createElement('div');
  rowSub.className = 'filter-row filter-row-sub';
  filtersBox.appendChild(rowMain);
  filtersBox.appendChild(rowSub);

  // 第一行：大分类 chips
  CATEGORIES.forEach(cat => {
    const f = 'cat:' + cat;
    const label = cat === 'all' ? t('cat_all', 'All') : t('cat_' + cat, cat);
    mk(f, label, rowMain, activeCategory === cat, 'cat');
  });

  // 第二行：当前分类内的子标签（仅选中具体分类时出现）
  if (activeCategory !== 'all') {
    const tagSet = [];
    cards.forEach(c => {
      if (c.category !== activeCategory) return;
      (c.style_tags || []).forEach(tg => { if (tagSet.indexOf(tg) === -1 && SUBSELECT_EXCLUDE.indexOf(tg) === -1) tagSet.push(tg); });
    });
    const visibleTags = tagSet.slice(0, FILTERS_COLLAPSE_AFTER);
    const hiddenTags = tagSet.slice(FILTERS_COLLAPSE_AFTER);
    visibleTags.forEach(tag => mk('tag:' + tag, t(tag, tag), rowSub, activeFilter === 'tag:' + tag, 'tag'));
    if (hiddenTags.length > 0) {
      const toggle = document.createElement('button');
      toggle.className = 'chip chip-toggle';
      toggle.dataset.action = 'toggle-filters';
      rowSub.appendChild(toggle);
      const extra = document.createElement('div');
      extra.className = 'chip-extra';
      hiddenTags.forEach(tag => mk('tag:' + tag, t(tag, tag), extra, activeFilter === 'tag:' + tag, 'tag'));
      rowSub.appendChild(extra);
      const userExpanded = localStorage.getItem('hololab_filters_expanded') === '1';
      const activeInHidden = hiddenTags.some(tag => activeFilter === 'tag:' + tag);
      const isExpanded = userExpanded || activeInHidden;
      if (isExpanded) filtersBox.classList.add('expanded');
      toggle.textContent = isExpanded ? t('filters_less', 'Less') : t('filters_more', 'More');
    }
  }
}
if (filtersBox) {
  filtersBox.addEventListener('click', e => {
    const toggle = e.target.closest('.chip-toggle');
    if (toggle) {
      filtersBox.classList.toggle('expanded');
      const expanded = filtersBox.classList.contains('expanded');
      localStorage.setItem('hololab_filters_expanded', expanded ? '1' : '0');
      const t = (key, fb) => (typeof window.HoloLabI18n !== 'undefined' ? window.HoloLabI18n.t(key) : fb);
      toggle.textContent = expanded ? t('filters_less', 'Less') : t('filters_more', 'More');
      return;
    }
    const chip = e.target.closest('.chip');
    if (!chip) return;
    const f = chip.dataset.filter || '';
    if (f.indexOf('cat:') === 0) {
      activeCategory = f.slice(4);
      if (activeCategory !== 'all') activeFilter = 'cat:' + activeCategory;
      else activeFilter = 'all';
    } else {
      activeFilter = f; /* tag:xxx */
    }
    renderChips();
    render();
  });
}
function animateCount(el, target) {
  const t0 = performance.now(), dur = 1200;
  function tick(t) {
    const p = Math.min(1, (t - t0) / dur);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ============ 5b. 隐藏解锁（locked card） ============ */
const UNLOCK_KEY = 'hololab_unlocked';
let unlockState = {};
try { unlockState = JSON.parse(localStorage.getItem(UNLOCK_KEY) || '{}'); } catch (e) { /* 损坏则重置 */ }
function isUnlocked(id) { return !!unlockState[id]; }
function saveUnlock(id) { unlockState[id] = true; try { localStorage.setItem(UNLOCK_KEY, JSON.stringify(unlockState)); } catch (e) { /* 隐私模式忽略 */ } }
async function sha256Hex(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}
let lockModalCtx = null;
function ensureLockModal() {
  if (lockModalCtx) return lockModalCtx;
  const L = k => (typeof window.HoloLabI18n !== 'undefined' ? window.HoloLabI18n.t(k) : k);
  const m = document.createElement('div');
  m.className = 'lock-modal';
  m.innerHTML =
    '<div class="lock-box" role="dialog" aria-modal="true" aria-label="' + L('lock_title') + '">' +
    '<button class="lock-close" aria-label="' + L('lock_cancel') + '">×</button>' +
    '<h3>' + L('lock_title') + '</h3>' +
    '<p class="lock-hint">' + L('lock_hint') + '</p>' +
    '<input class="lock-input" type="password" placeholder="' + L('lock_input_ph') + '" autocomplete="off" autocapitalize="off" spellcheck="false">' +
    '<p class="lock-err" hidden></p>' +
    '<div class="lock-actions">' +
    '<button class="lock-no">' + L('lock_no_thanks') + '</button>' +
    '<button class="lock-yes">' + L('lock_btn') + '</button>' +
    '</div></div>';
  document.body.appendChild(m);
  const input = m.querySelector('.lock-input'), err = m.querySelector('.lock-err');
  let card = null;
  const close = () => { m.classList.remove('open'); err.hidden = true; input.value = ''; };
  m.querySelector('.lock-close').onclick = close;
  m.querySelector('.lock-no').onclick = close;
  m.addEventListener('click', e => { if (e.target === m) close(); });
  m.querySelector('.lock-yes').onclick = async () => {
    const pw = input.value.trim();
    if (!pw || !card || !card.lockHash) return;
    const h = await sha256Hex(pw);
    if (h === card.lockHash) {
      saveUnlock(card.id);
      input.value = ''; close(); render();
      if (card.url) window.location.href = card.url;
    } else {
      err.textContent = L('lock_wrong'); err.hidden = false; input.select();
    }
  };
  input.addEventListener('keydown', e => { if (e.key === 'Enter') m.querySelector('.lock-yes').click(); });
  lockModalCtx = { open: c => { card = c; m.classList.add('open'); setTimeout(() => input.focus(), 60); } };
  return lockModalCtx;
}
function promptUnlock(c) { ensureLockModal().open(c); }

function makeCard(c, i) {
  const card = document.createElement('a');
  card.className = 'card';
  card.href = c.url;
  card.setAttribute('aria-label', c.title);
  card.style.setProperty('--d', ((i % 8) * 70) + 'ms');
  const locked = !!(c.locked) && !isUnlocked(c.id);
  const L = k => (typeof window.HoloLabI18n !== 'undefined' ? window.HoloLabI18n.t(k) : k);
  card.innerHTML =
    '<div class="thumb-wrap' + (locked ? ' locked' : '') + '">' +
    '<img class="' + (locked ? 'locked-img ' : '') + '" src="' + escHtml(c.thumb) + '" alt="' + escHtml(c.title) + '" loading="lazy">' +
    (locked
      ? '<div class="lock-overlay"><svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/><circle cx="12" cy="15.5" r="1.4" fill="currentColor" stroke="none"/></svg><span>' + escHtml(L('locked_badge')) + '</span></div>'
      : (c.lenticular
        ? '<canvas class="lent" width="720" height="1000" aria-hidden="true"></canvas>'
        : (c.preview ? '<video class="card-video" src="' + escHtml(c.preview) + '" muted playsinline loop preload="none"></video>' : ''))) +
    '<span class="rarity">' + escHtml(c.collection || '典藏') + '</span>' +
    (c.render_mode === 'premium' ? '<span class="premium-badge">✦ ' + escHtml(L('premium_badge')) + '</span>' : '') +
    '</div>' +
    '<div class="meta' + (locked ? ' locked-meta' : '') + '">' +
    '<div class="tags">' + (c.style_tags || []).map(t => '<span class="tag">' + escHtml(t) + '</span>').join('') + '</div>' +
    '<h3>' + escHtml(c.title) + '</h3>' +
    '<div class="sub">' + escHtml(c.subtitle || '') + '</div>' +
    '<p class="desc">' + escHtml(c.description || '') + '</p>' +
    '<div class="ed">' + escHtml(c.edition || '') + ' · ' + escHtml(c.date || '') + '</div>' +
    (locked ? '<div class="lock-meta-tip">' + escHtml(L('lock_private')) + '</div>' : '') +
    '</div>';
  const vid = card.querySelector('.card-video');
  if (vid) {
    card.addEventListener('mouseenter', () => { vid.currentTime = 0; vid.play().catch(() => { }); });
    card.addEventListener('mouseleave', () => { vid.pause(); });
  }
  /* 锁卡：点击弹密码框，不直接跳详情页 */
  if (locked) {
    card.addEventListener('click', e => { e.preventDefault(); promptUnlock(c); });
    card.classList.add('is-locked');
  }
  /* lenticular 光栅：双视角帧按鼠标位置条纹混合（桌面精细指针） */
  const lent = card.querySelector('canvas.lent');
  if (lent && finePointer && !reduceMotion) {
    const imgs = [new Image(), new Image()];
    imgs[0].src = c.lenticular.L;
    imgs[1].src = c.lenticular.R;
    const ctx = lent.getContext('2d');
    let shown = false, x = 0.5, raf = null;
    function draw() {
      raf = null;
      const w = lent.width, h = lent.height, n = 26, cw = w / n, ch = h;
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < n; i++) {
        const ph = ((i / n) + x) % 1;
        const img = imgs[ph < 0.5 ? 0 : 1];
        if (img.complete && img.naturalWidth) {
          // 源矩形按源图实际尺寸取样（防越界），目标矩形铺满 canvas；源图与 canvas 等比时无缝放大
          const sw = img.naturalWidth / n, sh = img.naturalHeight;
          const sww = Math.min(sw + 0.5, img.naturalWidth - i * sw);
          ctx.drawImage(img, i * sw, 0, sww, sh, i * cw, 0, cw + 1, ch);
        }
      }
    }
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      x = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
      if (!shown) { lent.style.display = 'block'; shown = true; }
      if (!raf) raf = requestAnimationFrame(draw);
    });
    card.addEventListener('mouseleave', () => {
      lent.style.display = 'none';
      shown = false;
      if (raf) { cancelAnimationFrame(raf); raf = null; }
    });
  }
  return card;
}

function filtered() {
  return cards.filter(c => {
    if (activeCategory !== 'all' && c.category !== activeCategory) return false;
    if (activeFilter.indexOf('tag:') === 0) {
      const tag = activeFilter.slice(4);
      if (!(c.style_tags || []).includes(tag)) return false;
    }
    return true;
  });
}

function render() {
  const list = filtered();
  if (viewState === 'curated') { renderCurated(list); return; }
  renderGrid(list);
}

function renderGrid(list) {
  stopTour();   /* 重渲染前中止导览（DOM 重建会使游走引用失效） */
  grid.querySelectorAll('.card').forEach(el => el.remove());
  currentEls = [];
  empty.hidden = list.length > 0;
  if (!list.length) return;
  const frag = document.createDocumentFragment();
  list.forEach((c, i) => { const el = makeCard(c, i); frag.appendChild(el); currentEls.push(el); });
  grid.appendChild(frag);
  if (reduceMotion) {
    currentEls.forEach(el => el.classList.add('in'));
    bindTilt(currentEls);
    return;
  }
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
  currentEls.forEach(el => io.observe(el));
  bindTilt(currentEls);
}

/* ============ 5c. 策展时间线 ============ */
const timeline = document.getElementById('timeline');
function editionNum(c) { const n = parseInt(c.edition, 10); return isNaN(n) ? 0 : n; }
function makeTimelineItem(c, i) {
  const el = document.createElement('div');
  el.className = 'tl-item';
  el.style.setProperty('--d', ((i % 8) * 70) + 'ms');
  const locked = !!(c.locked) && !isUnlocked(c.id);
  const L = k => (typeof window.HoloLabI18n !== 'undefined' ? window.HoloLabI18n.t(k) : k);
  const note = (curated[c.id] || {})[I18N.get()] || (curated[c.id] || {}).zh || '';
  const tags = (c.style_tags || []).map(t => '<span class="tag">' + escHtml(t) + '</span>').join('');
  el.innerHTML =
    '<div class="tl-date"><span class="tl-d">' + escHtml(String(c.date || '').replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$2.$3')) + '</span></div>' +
    '<div class="tl-axis"><span class="tl-dot"></span></div>' +
    '<div class="tl-body">' +
    '<a class="tl-thumb' + (locked ? ' is-locked' : '') + '" href="' + escHtml(c.url) + '" aria-label="' + escHtml(c.title) + '">' +'<span class="premium-badge tl">✦ ' + escHtml(L('premium_badge')) + '</span>' +
    '<img class="' + (locked ? 'locked-img ' : '') + '" src="' + escHtml(c.thumb) + '" alt="' + escHtml(c.title) + '" loading="lazy">' +
    (locked ? '<div class="lock-overlay"><svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/><circle cx="12" cy="15.5" r="1.4" fill="currentColor" stroke="none"/></svg><span>' + escHtml(L('locked_badge')) + '</span></div>' : '') +
    '</a>' +
    '<div class="tl-info">' +
    '<div class="tags">' + tags + '</div>' +
    '<h3>' + escHtml(c.title) + '</h3>' +
    '<p class="sub">' + escHtml(c.subtitle || '') + '</p>' +
    '<p class="tl-note">' + escHtml(note || '') + '</p>' +
    '<div class="tl-meta">' + escHtml(c.edition || '') + (c.date ? ' · ' + escHtml(c.date) : '') + '</div>' +
    '</div></div>';
  if (locked) {
    const a = el.querySelector('.tl-thumb');
    a.addEventListener('click', e => { e.preventDefault(); promptUnlock(c); });
  }
  return el;
}

function renderCurated(list) {
  if (!timeline) return;
  const sorted = list.slice().sort((a, b) => {
    const d = String(a.date || '').localeCompare(String(b.date || ''));
    if (d !== 0) return d;
    return editionNum(a) - editionNum(b);
  });
  timeline.querySelectorAll('.tl-item').forEach(el => el.remove());
  currentEls = [];
  empty.hidden = sorted.length > 0;
  if (!sorted.length) return;
  const frag = document.createDocumentFragment();
  sorted.forEach((c, i) => { const el = makeTimelineItem(c, i); frag.appendChild(el); currentEls.push(el); });
  timeline.appendChild(frag);
  if (reduceMotion) {
    currentEls.forEach(el => el.classList.add('in'));
    return;
  }
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
  currentEls.forEach(el => io.observe(el));
}

/* 3D tilt（桌面）+ 光标光斑跟随 */
function bindTilt(els) {
  if (!finePointer || reduceMotion) return;
  els.forEach(el => {
    let raf = null;
    el.addEventListener('mousemove', e => {
      if (grid.classList.contains('touring')) return;   /* 导览期间禁用 tilt，避免与聚光动画抢 transform */
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (((e.clientX - r.left) / r.width) * 100).toFixed(1) + '%');
      el.style.setProperty('--my', (((e.clientY - r.top) / r.height) * 100).toFixed(1) + '%');
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        el.style.transform = 'translateY(-4px) perspective(720px) rotateY(' + (px * 8).toFixed(2) + 'deg) rotateX(' + (-py * 7).toFixed(2) + 'deg)';
        raf = null;
      });
    });
    el.addEventListener('mouseleave', () => { if (!grid.classList.contains('touring')) el.style.transform = ''; });
  });
}

/* ============ 6. 强化层 v3：流光扫字 / 磁吸按钮 / 滚动视差 ============ */
(function heroShine() {
  if (!heroTitle || reduceMotion) return;
  const sh = document.createElement('span');
  sh.className = 'hero-shine';
  sh.setAttribute('aria-hidden', 'true');
  heroTitle.appendChild(sh);
  window.__hololabSyncShine = () => {
    if (!sh.isConnected) heroTitle.appendChild(sh);   // splitTitle 清空 h1 时会带走 shine，需重新挂回
    sh.innerHTML = heroTitle.innerHTML;               // 逐字结构与标题同步，光扫位置与字完全一致
    sh.style.animation = 'none';
    void sh.offsetWidth;
    sh.style.animation = '';
  };
  window.__hololabSyncShine();
})();

(function magnet() {
  if (!finePointer || reduceMotion) return;
  const cta = document.querySelector('.hero-cta');
  if (!cta) return;
  cta.querySelectorAll('.btn').forEach(b => {
    b.addEventListener('mousemove', e => {
      const r = b.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      const d = Math.hypot(dx, dy);
      if (d < 100) {
        const k = Math.min(1, (100 - d) / 100) * 6;
        b.style.transform = 'translate(' + ((dx / d) * k || 0) + 'px,' + ((dy / d) * k || 0) + 'px)';
      } else b.style.transform = '';
    });
    b.addEventListener('mouseleave', () => { b.style.transform = ''; });
  });
})();

(function scrollParallax() {
  if (!window.gsap || !window.ScrollTrigger || reduceMotion) return;
  gsap.registerPlugin(ScrollTrigger);
  const hero = document.querySelector('.hero');
  const heroInner = document.querySelector('.hero-inner');
  const scrollHint = document.querySelector('.scroll-hint');
  if (hero && heroInner) {
    gsap.to(heroInner, {
      y: 90, opacity: 0.2, ease: 'none',
      scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: 0.6 }
    });
  }
  if (scrollHint) {
    gsap.to(scrollHint, {
      opacity: 0, ease: 'none',
      scrollTrigger: { trigger: hero, start: 'top top', end: '28% top', scrub: 0.4 }
    });
  }
})();

/* 筛选 */
load().catch(err => {
  empty.hidden = false;
  empty.textContent = '加载失败：' + err.message;
});

/* ============ 8. 自动导览 v2（Auto Tour：光束流动 + 卡面激活 + HUD） ============ */
const tourBtn = document.getElementById('tour-btn');
const tourBeam = document.querySelector('.tour-beam');
const tourHud = document.querySelector('.tour-hud');
const hudCount = tourHud ? tourHud.querySelector('.th-count') : null;
const hudName = tourHud ? tourHud.querySelector('.th-name') : null;
let tourOn = false, tourOrder = [], tourIdx = 0, tourEls = [], tourTimer = null;

function tourElsNow() {
  /* 网格视图 + 当前可见 + 非锁卡 */
  return currentEls.filter(el => !el.classList.contains('is-locked'));
}

function paintTourBtn() {
  if (!tourBtn) return;
  const k = tourOn ? 'tour_stop' : 'tour_play';
  const span = tourBtn.querySelector('span');
  if (span) span.textContent = I18N.t(k);
  tourBtn.setAttribute('aria-pressed', tourOn ? 'true' : 'false');
  tourBtn.setAttribute('aria-label', I18N.t(k));
  tourBtn.title = I18N.t('tour_hint');
}

function cardCenter(el) {
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

function beamReset(firstEl) {
  if (!tourBeam || !window.gsap) return;
  if (firstEl) {
    const c = cardCenter(firstEl);
    gsap.set(tourBeam, { xPercent: -50, yPercent: -50, x: c.x, y: c.y, opacity: 0, scale: .7 });
  } else {
    gsap.set(tourBeam, { xPercent: -50, yPercent: -50, opacity: 0, scale: .7 });
  }
}

/* 聚焦当前卡：卡面被"激活" */
function applyFocus(el) {
  if (!tourOn) return;
  el.classList.add('tour-focus');
  if (window.gsap) {
    gsap.to(el, {
      scale: 1.06, y: -7, rotateX: 2.5, filter: 'brightness(1.08)', opacity: 1,
      duration: .5, ease: 'power2.out', overwrite: 'auto'
    });
    const sub = el.querySelector('.sub');
    if (sub) gsap.fromTo(sub, { opacity: .2, y: 5 }, { opacity: 1, y: 0, duration: .45, ease: 'power1.out' });
  }
  /* 标题金色流光扫过 */
  const h3 = el.querySelector('h3');
  if (h3) { h3.classList.remove('shine-on'); void h3.offsetWidth; h3.classList.add('shine-on'); }
  /* 预览视频：聚焦播放 1.4s */
  const vid = el.querySelector('.card-video');
  if (vid) { vid.currentTime = 0; vid.play().catch(() => { }); if (window.gsap) gsap.delayedCall(1.4, () => { if (!vid.paused) vid.pause(); }); }
  /* HUD：第 N 张 + 卡名 */
  if (hudCount && hudName) {
    hudCount.textContent = (tourIdx + 1) + ' / ' + tourEls.length;
    hudName.textContent = (h3 ? h3.textContent : '');
    if (tourHud) tourHud.classList.add('on');
  }
}

/* 压暗其余卡 */
function dimOthers(el) {
  if (window.gsap) {
    tourEls.forEach(e => {
      if (e === el) return;
      e.classList.remove('tour-focus');
      gsap.to(e, {
        scale: 1, y: 0, rotateX: 0, filter: 'brightness(.82)', opacity: .88,
        duration: .5, ease: 'power1.out', overwrite: 'auto'
      });
    });
  } else {
    tourEls.forEach(e => { if (e !== el) e.classList.remove('tour-focus'); });
  }
}

function stopTour(restore) {
  tourOn = false;
  if (tourTimer) { clearTimeout(tourTimer); tourTimer = null; }
  if (tourBeam && window.gsap) {
    gsap.to(tourBeam, { opacity: 0, scale: .55, duration: .5, ease: 'power1.out' });   /* 光束谢幕 */
  }
  if (tourHud) tourHud.classList.remove('on');
  if (restore !== false && currentEls.length) {
    currentEls.forEach(el => {
      el.classList.remove('tour-focus');
      const h3 = el.querySelector('h3'); if (h3) h3.classList.remove('shine-on');
      const vid = el.querySelector('.card-video'); if (vid) vid.pause();
      if (window.gsap) {
        gsap.to(el, { scale: 1, y: 0, rotateX: 0, filter: 'brightness(1)', opacity: 1, duration: .45, ease: 'power1.out', overwrite: 'auto' });
      } else {
        el.style.transform = ''; el.style.filter = ''; el.style.opacity = '';
      }
    });
  }
  grid.classList.remove('touring');
  paintTourBtn();
}

function stepTour() {
  if (!tourOn) return;
  const el = tourEls[tourOrder[tourIdx]];
  if (!el) { stopTour(); return; }
  /* 下一张不在视口：先平滑滚过去 */
  const r = el.getBoundingClientRect();
  const vh = innerHeight;
  if (r.top < 40 || r.bottom > vh * 0.86) {
    window.scrollTo({ top: Math.max(0, scrollY + r.top - vh * 0.36), behavior: 'smooth' });
  }
  dimOthers(el);
  if (tourBeam && window.gsap) {
    if (tourIdx === 0) {
      /* 第一张：光束原地"生长"点亮，不做长距离飞行 */
      gsap.fromTo(tourBeam, { opacity: 0, scale: .7 }, {
        opacity: 1, scale: 1, duration: .55, ease: 'power1.out',
        onComplete: () => applyFocus(el)
      });
    } else {
      const c = cardCenter(el);
      /* 光束从上一张的位置滑过来，到位瞬间点亮卡面 */
      gsap.to(tourBeam, {
        x: c.x, y: c.y, opacity: 1, scale: 1, duration: .75, ease: 'power2.inOut',
        onComplete: () => applyFocus(el)
      });
    }
  } else {
    applyFocus(el);
  }
  tourIdx++;
  if (tourIdx >= tourOrder.length) {
    /* 一圈走完：最后一张多驻留一会再谢幕 */
    tourTimer = setTimeout(() => stopTour(), 2800);
    return;
  }
  tourTimer = setTimeout(stepTour, 2500);
}

function startTour() {
  if (reduceMotion || viewState !== 'grid' || grid.hidden) return;
  stopTour();
  const els = tourElsNow();
  if (els.length < 2) return;   /* 单张或空列表没有巡展意义 */
  const order = els.map((_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = order[i]; order[i] = order[j]; order[j] = t;
  }
  tourEls = els; tourOrder = order; tourIdx = 0;
  tourOn = true;
  grid.classList.add('touring');
  beamReset(els[order[0]]);   /* 光束预置到首张卡中心，第一段原地亮起 */
  paintTourBtn();
  /* 开场编排：卡片错落苏醒后，光束开始第一段行程 */
  if (window.gsap) {
    gsap.fromTo(els, { opacity: .5, y: 16 }, {
      opacity: 1, y: 0, stagger: .05, duration: .55, ease: 'power2.out', overwrite: 'auto',
      onComplete: () => { if (tourOn) stepTour(); }
    });
  } else {
    stepTour();
  }
}

if (tourBtn) {
  tourBtn.addEventListener('click', () => (tourOn ? stopTour() : startTour()));
  if (reduceMotion) tourBtn.disabled = true;
}
