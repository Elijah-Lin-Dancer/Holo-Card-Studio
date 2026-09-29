// HoloLab Gallery · 展厅（纯静态，JSON 清单驱动）+ 全息动效引擎
// 手写实现：粒子背景 / 光标光晕 / 标题逐字动画 / 卡片 staggered 入场 / 3D tilt / 双语切换

const I18N = window.HoloLabI18n;
const THEME = window.HoloLabTheme;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

/* ============ 1. 语言 / 主题切换器 ============ */
const langBtn = document.getElementById('lang-btn');
const themeBtn = document.getElementById('theme-btn');

function paintLangBtn() {
  langBtn.textContent = I18N.get() === 'zh' ? 'EN' : '中文';
}
function setLang(l) { I18N.setLang(l); paintLangBtn(); reSplitTitle(); }
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
  let W, H, stars = [], raf = null;
  function palette() {
    const d = THEME.get() === 'dark';
    return d ? ['255,255,255', '201,168,106', '127,212,255'] : ['96,84,60', '143,106,44', '14,111,159'];
  }
  function resize() { W = cv.width = innerWidth; H = cv.height = innerHeight; }
  function make() {
    const density = finePointer ? 16000 : 24000;
    const n = Math.min(170, Math.floor(W * H / density));
    const pal = palette();
    stars = [];
    for (let i = 0; i < n; i++) {
      stars.push({
        x: Math.random() * W, y: Math.random() * H,
        r: Math.random() * 1.4 + 0.35,
        a: Math.random() * 0.5 + 0.1,
        s: Math.random() * 0.28 + 0.05,
        tw: Math.random() * Math.PI * 2,
        c: pal[i % 3]
      });
    }
  }
  function step() {
    ctx.clearRect(0, 0, W, H);
    for (const st of stars) {
      st.y -= st.s;
      if (st.y < -2) { st.y = H + 2; st.x = Math.random() * W; }
      st.tw += 0.02;
      const al = st.a * (0.55 + 0.45 * Math.sin(st.tw));
      ctx.beginPath();
      ctx.fillStyle = 'rgba(' + st.c + ',' + al.toFixed(3) + ')';
      ctx.arc(st.x, st.y, st.r, 0, 6.2832);
      ctx.fill();
    }
    raf = requestAnimationFrame(step);
  }
  resize(); make(); step();
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
function reSplitTitle() { if (heroTitle) splitTitle(heroTitle); }
if (heroTitle && !reduceMotion) reSplitTitle();

/* ============ 5. 卡片加载 + 动效 ============ */
const grid = document.getElementById('gallery');
const empty = grid.querySelector('.empty');
let activeFilter = 'all';
let cards = [];
let currentEls = [];

async function load() {
  const res = await fetch('./cards.json');
  const data = await res.json();
  cards = data.cards || [];
  const stat = document.getElementById('stat-cards');
  if (stat) animateCount(stat, cards.length);
  render();
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

function makeCard(c, i) {
  const card = document.createElement('a');
  card.className = 'card';
  card.href = c.url;
  card.setAttribute('aria-label', c.title);
  card.style.setProperty('--d', ((i % 8) * 70) + 'ms');
  card.innerHTML =
    '<div class="thumb-wrap">' +
    '<img src="' + c.thumb + '" alt="' + c.title + '" loading="lazy">' +
    (c.preview ? '<video class="card-video" src="' + c.preview + '" muted playsinline loop preload="none"></video>' : '') +
    '<span class="rarity">' + (c.collection || '典藏') + '</span>' +
    '</div>' +
    '<div class="meta">' +
    '<div class="tags">' + (c.style_tags || []).map(t => '<span class="tag">' + t + '</span>').join('') + '</div>' +
    '<h3>' + c.title + '</h3>' +
    '<div class="sub">' + (c.subtitle || '') + '</div>' +
    '<p class="desc">' + (c.description || '') + '</p>' +
    '<div class="ed">' + (c.edition || '') + ' · ' + (c.date || '') + '</div>' +
    '</div>';
  const vid = card.querySelector('.card-video');
  if (vid) {
    card.addEventListener('mouseenter', () => { vid.currentTime = 0; vid.play().catch(() => { }); });
    card.addEventListener('mouseleave', () => { vid.pause(); });
  }
  return card;
}

function render() {
  const list = activeFilter === 'all'
    ? cards
    : cards.filter(c => (c.style_tags || []).includes(activeFilter));
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

/* 3D tilt（桌面） */
function bindTilt(els) {
  if (!finePointer || reduceMotion) return;
  els.forEach(el => {
    let raf = null;
    el.addEventListener('mousemove', e => {
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        el.style.transform = 'translateY(-4px) perspective(720px) rotateY(' + (px * 8).toFixed(2) + 'deg) rotateX(' + (-py * 7).toFixed(2) + 'deg)';
        raf = null;
      });
    });
    el.addEventListener('mouseleave', () => { el.style.transform = ''; });
  });
}

/* 筛选 */
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeFilter = chip.dataset.filter;
    render();
  });
});

load().catch(err => {
  empty.hidden = false;
  empty.textContent = '加载失败：' + err.message;
});
