// HoloLab Gallery · 瀑布流展厅（纯静态，JSON 清单驱动）
const grid = document.getElementById('grid') || document.getElementById('gallery');
const empty = grid.querySelector('.empty');
let activeFilter = 'all';
let cards = [];

async function load() {
  const res = await fetch('./cards.json');
  const data = await res.json();
  cards = data.cards || [];
  document.getElementById('stat-cards').textContent = cards.length;
  render();
}

function render() {
  const list = activeFilter === 'all'
    ? cards
    : cards.filter(c => (c.style_tags || []).includes(activeFilter));
  grid.querySelectorAll('.card').forEach(el => el.remove());
  empty.hidden = list.length > 0;
  for (const c of list) {
    const card = document.createElement('a');
    card.className = 'card';
    card.href = c.url;
    card.setAttribute('aria-label', c.title);
    card.innerHTML = `
      <div class="thumb-wrap">
        <img src="${c.thumb}" alt="${c.title}" loading="lazy">
        ${c.preview ? `<video class="card-video" src="${c.preview}" muted playsinline loop preload="none"></video>` : ''}
        <span class="rarity">${c.collection || '典藏'}</span>
      </div>
      <div class="meta">
        <div class="tags">${(c.style_tags || []).map(t => `<span class="tag">${t}</span>`).join('')}</div>
        <h3>${c.title}</h3>
        <div class="sub">${c.subtitle || ''}</div>
        <p class="desc">${c.description || ''}</p>
        <div class="ed">${c.edition || ''} · ${c.date || ''}</div>
      </div>`;
    const vid = card.querySelector('.card-video');
    if (vid) {
      card.addEventListener('mouseenter', () => { vid.currentTime = 0; vid.play().catch(() => {}); });
      card.addEventListener('mouseleave', () => { vid.pause(); });
    }
    grid.appendChild(card);
  }
}

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
  empty.textContent = '展厅加载失败：' + err.message;
});
