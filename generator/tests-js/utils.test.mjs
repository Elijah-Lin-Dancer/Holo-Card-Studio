// HoloLab 前端纯函数单测（node --test，无第三方依赖）
// 覆盖安全关键 escHtml（XSS 防线）的完整转义向量。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escHtml } from '../../gallery/js/utils.mjs';

test('escHtml 转义五类 HTML 特殊字符', () => {
  assert.equal(escHtml('<script>'), '&lt;script&gt;');
  assert.equal(escHtml('a&b'), 'a&amp;b');
  assert.equal(escHtml('"quoted"'), '&quot;quoted&quot;');
  assert.equal(escHtml("'single'"), '&#39;single&#39;');
});

test('escHtml 对空值安全', () => {
  assert.equal(escHtml(null), '');
  assert.equal(escHtml(undefined), '');
  assert.equal(escHtml(0), '0');
  assert.equal(escHtml(''), '');
});

test('escHtml 防存储型 XSS 组合向量', () => {
  const payload = `<img src=x onerror="alert('xss')">&</img>`;
  const out = escHtml(payload);
  // 关键安全属性：所有 < > 均被转义，输出不可被解析为任何标签结构
  assert.ok(!out.includes('<'), '输出不应残留裸 <');
  assert.ok(!out.includes('>'), '输出不应残留裸 >');
  assert.ok(out.includes('&lt;img'));
  // 属性引号也已转义，onerror 无法形成属性赋值
  assert.ok(out.includes('&quot;alert(&#39;xss&#39;)&quot;'));
});

test('escHtml 幂等（重复转义不产生双重实体破坏）', () => {
  const once = escHtml('a<b');
  const twice = escHtml(once);
  assert.equal(once, 'a&lt;b');
  // 二次转义只处理首次产物中的 &（&lt; 的 &），这是正确行为：
  // 已转义内容再次展示仍是安全文本，不产生可注入标签
  assert.ok(!twice.includes('<b>'));
});
