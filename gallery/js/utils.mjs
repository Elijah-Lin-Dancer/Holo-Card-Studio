// HoloLab 前端纯函数库（ES module）
// 单测入口：generator/tests-js/utils.test.mjs（node --test）
// 浏览器入口：<script type="module" src="./app.js"> 内 import
export function escHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
}
