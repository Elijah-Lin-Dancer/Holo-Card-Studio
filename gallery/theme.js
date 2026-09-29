/* HoloLab 主题切换 — 深色（全息舞台）/ 浅色（收藏展柜），localStorage 记忆 */
(function (w) {
  var KEY = 'hololab-theme';
  function detect() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    if (saved === 'dark' || saved === 'light') return saved;
    return (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
  }
  var theme = detect();
  function apply(th) {
    theme = th;
    document.documentElement.setAttribute('data-theme', th);
    try { localStorage.setItem(KEY, th); } catch (e) {}
    if (w.__hololabOnTheme) w.__hololabOnTheme(th);
  }
  apply(theme);
  w.HoloLabTheme = {
    get: function () { return theme; },
    set: apply,
    toggle: function () { apply(theme === 'dark' ? 'light' : 'dark'); }
  };
})(window);
