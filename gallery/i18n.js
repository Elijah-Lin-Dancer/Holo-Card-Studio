/* HoloLab i18n — 中英双语界面文案（纯静态，零依赖） */
(function (w) {
  var LANG_KEY = 'hololab-lang';

  var dict = {
    // 导航
    nav_gallery:     { zh: '展厅',      en: 'Gallery' },
    nav_create:      { zh: '创造',      en: 'Create' },
    nav_github:      { zh: 'GitHub',    en: 'GitHub' },
    theme_label:     { zh: '切换主题',  en: 'Toggle theme' },
    lang_label:      { zh: 'Switch to English', en: '切换到中文' },

    // Hero
    hero_eyebrow:    { zh: 'HOLOGRAPHIC COLLECTION 01', en: 'HOLOGRAPHIC COLLECTION 01' },
    hero_title:      { zh: '会随着你的视线流动的光影收藏。', en: 'A collection of light that flows with your gaze.' },
    hero_sub:        { zh: '每一张卡都由 AI 分层绘制、Blender 渲染、Three.js 实时合成——拖一拖，主体往前凸，背景往后退，镭射彩虹随角度流转。', en: 'Every card is layered by AI, rendered in Blender and composited live in Three.js — drag to push the subject forward, ease the background back, and watch rainbow foil shift with the angle.' },
    hero_cta_gallery:{ zh: '进入展厅',  en: 'Enter the gallery' },
    hero_cta_create: { zh: '开始创造',  en: 'Start creating' },
    scroll_hint:     { zh: '向下滚动，进入展厅', en: 'Scroll to enter the gallery' },

    // 统计
    stat_cards:      { zh: '张卡',      en: 'cards' },
    stat_seedream:   { zh: 'AI 分层绘制', en: 'AI layered art' },
    stat_blender:    { zh: '3D 渲染', en: '3D rendering' },
    stat_static:     { zh: '零后端 · 零数据库', en: 'Zero backend · zero DB' },
    stat_mit:         { zh: '开源许可', en: 'open source' },

    // 筛选
    filters_all:     { zh: '全部',      en: 'All' },

    // 画廊
    empty:           { zh: '暂无卡片，稍后再来看看。', en: 'No cards yet — check back soon.' },

    // 尾部 CTA

    // 页脚
    footer_slogan:   { zh: '光随手动，画有余深。', en: 'Light follows your hand; depth lives in every frame.' },
    footer_tag:      { zh: 'HoloLab Studio — 作品集项目 · AI × 3D 交叉方向', en: 'HoloLab Studio — portfolio project · AI × 3D intersection' },
    footer_credit:   { zh: '基于 MIT 开源项目 holo-card-studio 二次开发，保留上游署名', en: 'Re-engineered from the MIT-licensed holo-card-studio; upstream credit preserved.' },
    footer_author:   { zh: '作者 Elijah Lin', en: 'by Elijah Lin' },
    footer_license:  { zh: 'MIT License · 开源许可', en: 'MIT License' },

    // 创造页
    cr_eyebrow:      { zh: 'HOLOLAB CREATE · 创作工坊', en: 'HOLOLAB CREATE · Studio' },
    cr_title:        { zh: '一句话，造一张全息卡。', en: 'One sentence. One holographic card.' },
    cr_sub:          { zh: '先输入一句话想法，扩写引擎会把它展开成结构化的详细描述——你随时可以修改。展厅里的每一张卡都来自同一条管线：文字模型把详细描述写成卡面配置，AI 分层绘制素材，Blender 合成 3D 卡体，一键发布上线。', en: 'Drop one sentence of an idea; the expander engine turns it into a structured description you can edit freely. Every card in the gallery comes from one pipeline: a language model turns the description into a card config, AI paints the layers, Blender assembles the 3D card, one-command publishing ships it.' },
    cr_label1:       { zh: '你的创意一句话', en: 'Your idea in one sentence' },
    cr_ph1:          { zh: '例如：我想要一张凤凰', en: 'e.g. I want a phoenix card' },
    cr_label2:       { zh: '详细描述（可自由修改）', en: 'Detailed description (feel free to edit)' },
    cr_ph2:          { zh: '详细描述将进入创作管线：主体、背景、色调、构图、线稿、卡面文字', en: 'This description feeds the pipeline: subject, background, palette, composition, line art, card text' },
    cr_gen:          { zh: '生成具体描述', en: 'Generate description' },
    cr_desc_btn:     { zh: '重新生成', en: 'Regenerate' },
    cr_desc_note:    { zh: '本地扩写引擎生成，无需联网、不消耗额度；想要 LLM 级润色，复制下方命令在本地跑文字模型。', en: 'Generated locally by the expander engine — no network, no quota. For LLM-grade polish, run the command below to use the language model locally.' },
    cr_go:           { zh: '开始创造',  en: 'Create card' },
    cr_save:         { zh: '保存到我的卡', en: 'Save to my cards' },
    cr_saved:        { zh: '✓ 已保存', en: '✓ Saved' },
    cr_mine:         { zh: '我的卡（私人）', en: 'My cards (private)' },
    cr_empty:        { zh: '还没有私人卡。保存的创意只存在你的浏览器里，别人看不到。', en: 'No private cards yet. Saved ideas live only in your browser — nobody else can see them.' },
    cr_export:       { zh: '导出卡片包', en: 'Export package' },
    cr_publish:      { zh: '申请公开', en: 'Request publish' },
    cr_pub_note:     { zh: '公开申请会导出卡片包文件。把文件发给 HoloLab 助手，进入策展管线：审核 + 正式渲染后，永久上线公开展厅。', en: 'Requesting publish exports a card package. Send the file to the HoloLab assistant — after curation and production rendering it goes live in the public gallery forever.' },
    cr_pub_done:     { zh: '卡片包已导出，可发给 HoloLab 助手进入策展管线。', en: 'Card package exported. Send it to the HoloLab assistant for the curation pipeline.' },
    cr_del:          { zh: '删除', en: 'Delete' },
    cr_lang_tag:     { zh: '中文', en: 'EN' },
    cr_hint_pre:     { zh: '想不到写什么？', en: 'Out of ideas? ' },
    cr_hint_btn:     { zh: '给我一个示例', en: 'Give me an example' },
    pv_head:         { zh: '概念预演',  en: 'Concept preview' },
    pv_note:         { zh: '文字模型、分层绘制与渲染由本地管线完成，这里展示你的创意如何进入管线', en: 'The text model, layered painting and rendering run in your local pipeline — here is how your idea enters it' },
    pv_brief:        { zh: 'BRIEF · 创意简报', en: 'BRIEF' },
    pv_await:        { zh: '等待管线',  en: 'Waiting' },
    pv_drawing:      { zh: 'AI 绘制中…', en: 'AI painting…' },
    pv_done:         { zh: '完成 · 四层就绪', en: 'Done · 4 layers ready' },
    layer_subject:   { zh: 'SUBJECT · 主体层', en: 'SUBJECT' },
    layer_bg:        { zh: 'BACKGROUND · 背景层', en: 'BACKGROUND' },
    layer_lineart:   { zh: 'LINEART · 线稿层', en: 'LINEART' },
    layer_text:      { zh: 'TEXT · 文字层', en: 'TEXT' },
    pstep_1:         { zh: '文字模型把一句话写成卡面配置', en: 'Text model writes the card config' },
    pstep_2:         { zh: 'AI 分层绘制主体 / 背景 / 线稿 / 文字', en: 'AI paints subject / background / lineart / text' },
    pstep_3:         { zh: '抠图与线稿提取，素材对齐', en: 'Matting & lineart extraction, assets aligned' },
    pstep_4:         { zh: 'Blender 合成 3D 卡体，Cycles 渲染', en: 'Blender builds the 3D body, Cycles renders' },
    pstep_5:         { zh: '一键发布：压缩 + 预览动画 + 清单', en: 'One-command publish: compress + preview + manifest' },
    pstep_6:         { zh: '上线展厅，任何人打开即玩', en: 'Ships to the gallery for anyone to open' },
    pstep_done:      { zh: '完成',      en: 'Done' },
    cmd_title:       { zh: '想要真卡？复制命令，本地跑一遍', en: 'Want the real card? Copy the command, run it locally' },
    cmd_sub:         { zh: '在线展厅是纯静态页面，不携带任何密钥。真实生成在本地完成：克隆仓库 → 一句话出卡 → 一键发布，全程约几分钟，管线完全开源可复现。', en: 'This gallery is a static page with no keys. Real generation runs locally: clone → one-sentence card → one-command publish. It takes minutes, and the pipeline is fully open source.' },
    cmd_step1_t:     { zh: '1 · 克隆仓库', en: '1 · Clone the repo' },
    cmd_step1_d:     { zh: 'git clone 拉取全部管线源码与文档。', en: 'git clone pulls the full pipeline source and docs.' },
    cmd_step2_t:     { zh: '2 · 一句话出卡', en: '2 · One-sentence card' },
    cmd_step2_d:     { zh: '文字模型自动生成卡面配置、编号与渲染参数（需在 .env 配置豆包 API Key）。', en: 'The text model writes the config, numbering and render params (set your Doubao API key in .env).' },
    cmd_step3_t:     { zh: '3 · 一键发布', en: '3 · One-command publish' },
    cmd_step3_d:     { zh: '压缩素材、渲染预览动画、更新清单，push 后 GitHub Actions 自动上线。', en: 'Compress, render the preview, update the manifest — GitHub Actions deploys on push.' },
    cmd_copy:        { zh: '复制命令',  en: 'Copy command' },
    cmd_copied:      { zh: '已复制',    en: 'Copied' },
    note_title:      { zh: '为什么不在网页里直接生成？', en: 'Why not generate right in the page?' },
    note_1:          { zh: '一条完整的生成链需要调用豆包 API（密钥绝不能进入前端）并在本地跑 Blender 渲染。这是有意的架构取舍：', en: 'A full generation chain needs the Doubao API (keys must never enter the frontend) and local Blender rendering. This is a deliberate architecture choice:' },
    note_strong:     { zh: '展厅负责"看"，管线负责"造"', en: 'the gallery shows, the pipeline makes' },
    note_2:          { zh: '，两者解耦后，任何人都能长期打开展厅，而创作者拥有全部控制权。管线原理见 ', en: ' — decoupled, the gallery stays open to anyone while creators keep full control. See ' },
    note_links:      { zh: 'README 与 docs/', en: 'README and docs/' },
    note_3:          { zh: '（架构、AI 管线、图形学、白皮书）。', en: ' (architecture, AI pipeline, graphics, whitepaper).' },
    // 卡面占位
    mc_tag:          { zh: 'HOLOGRAPHIC COLLECTION', en: 'HOLOGRAPHIC COLLECTION' }
  };

  function detect() {
    var saved = null;
    try { saved = localStorage.getItem(LANG_KEY); } catch (e) {}
    // URL 参数优先（分享链接强制语言），其次用户选择，最后浏览器语言
    var m = location.search.match(/[?&]lang=(zh|en)/);
    if (m) return m[1];
    if (saved === 'zh' || saved === 'en') return saved;
    var nav = (navigator.language || 'zh').toLowerCase();
    return nav.indexOf('zh') === 0 ? 'zh' : 'en';
  }

  var lang = detect();
  function t(key) {
    var e = dict[key];
    return e ? e[lang] : key;
  }
  function apply() {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    var nodes = document.querySelectorAll('[data-i18n],[data-i18n-ph]');
    for (var i = 0; i < nodes.length; i++) {
      var ph = nodes[i].getAttribute('data-i18n-ph');
      if (ph) nodes[i].placeholder = t(ph);
      var k = nodes[i].getAttribute('data-i18n');
      if (!k) continue;
      var v = t(k);
      if (nodes[i].tagName === 'INPUT') { nodes[i].value = v; continue; }
      nodes[i].textContent = v;
      if (nodes[i].getAttribute('data-i18n-title')) nodes[i].title = v;
    }
    var metas = document.querySelectorAll('meta[data-i18n-desc]');
    for (var j = 0; j < metas.length; j++) metas[j].content = t(metas[j].getAttribute('data-i18n-desc'));
  }
  function setLang(l) {
    lang = l;
    try { localStorage.setItem(LANG_KEY, l); } catch (e) {}
    apply();
    if (w.__hololabOnLang) w.__hololabOnLang(l);
  }

  w.HoloLabI18n = { t: t, apply: apply, setLang: setLang, get: function () { return lang; } };
})(window);
