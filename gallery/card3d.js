/* =========================================================================
 * card3d.js — C-scheme True-3D card frame renderer
 * -------------------------------------------------------------------------
 * 双线制作体系 · 新线（True-3D / C-scheme）的运行时渲染器。
 *
 * 旧线（Classic）  : 四层素材 → Blender 渲染 GLB + preview.webm → 详情页
 *                    WebGL 加载 card.glb（全息 shader + Bloom）。
 * 新线（True-3D）  : 四层素材 → 本模块在浏览器里程序化构建实体卡框
 *                    （圆角几何 + 金属材质 + 悬浮层真深度视差 + Bloom），
 *                    不需要 Blender / GLB / preview 视频。
 *
 * 用法（新线卡详情页 app.js 里）：
 *   import { initTrue3D } from '../../card3d.js';
 *   const ctrl = initTrue3D(document.querySelector('#stage'), {
 *     background: './assets/background.png',
 *     subject:    './assets/subject.png',
 *     lineart:    './assets/lineart.png',
 *     text:       './assets/text.png',
 *     cardWidth:  2,      // 卡面宽（世界单位）
 *     cardHeight: 3,      // 卡面高
 *     thickness:  0.14,   // 卡体厚度（米，14mm 金属质感）
 *     autoRotate: true,
 *   });
 *   // 页面卸载时： ctrl.dispose()
 *
 * 依赖：three r180（vendor/three/build/three.module.js，含 three.core.js 壳）
 *       + OrbitControls / RoundedBoxGeometry / postprocessing（Bloom）。
 * 兼容：与既有详情页 app.js 同一 importmap（'three' / 'three/addons/'）。
 * ========================================================================= */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// 灰度线稿 → 白色发光描边纹理（line + 光晕 glow 两层）
async function makeGlowTextures(url) {
  const img = await loadImage(url);
  const mk = (blur) => {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const ctx = c.getContext('2d');
    if (blur) ctx.filter = `blur(${blur}px)`;
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height);
    for (let i = 0; i < d.data.length; i += 4) {
      // 四层管线 lineart = 白底黑线：白底透明、黑线反转为白色发光描边
      const g = d.data[i];
      d.data[i] = 255; d.data[i + 1] = 255; d.data[i + 2] = 255;
      d.data[i + 3] = blur ? (255 - g) * 0.55 : (255 - g);  // 光晕层透明度减半
    }
    ctx.putImageData(d, 0, 0);
    return c;
  };
  return {
    line: new THREE.CanvasTexture(mk(0)),
    glow: new THREE.CanvasTexture(mk(14)),
  };
}

function loadImage(url) {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => {
      const out = downsample(img);
      if (out === img) { res(out); return; }
      out.onload = () => res(out);   // data URL 解码是异步的，必须等它就绪
      out.onerror = rej;
    };
    img.onerror = rej;
    img.src = url;
  });
}
// 卡面显示尺寸远小于素材原图：统一缩到短边 ≤1024，纹理带宽/显存降 60%+，避免掉帧卡顿
function downsample(img) {
  const MAX = 1024;
  const short = Math.min(img.width, img.height);
  if (short <= MAX) return img;
  const k = MAX / short;
  const w = Math.round(img.width * k), h = Math.round(img.height * k);
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0, w, h);
  const out = new Image();
  out.src = c.toDataURL('image/png');
  return out;
}

/**
 * 在 canvas 上初始化 C 方案真 3D 卡框。
 * @returns {{dispose:Function, ok:boolean}} ok=false 表示 WebGL 不可用（调用方应回退静态封面）
 */
export async function initTrue3D(canvas, cfg = {}) {
  const status = (msg) => { if (cfg.onStatus) cfg.onStatus(msg); };

  // —— WebGL 可用性探测（不可用时静默降级，不抛错）——
  let testGl;
  try { testGl = canvas.getContext('webgl2') || canvas.getContext('webgl'); }
  catch (_) { testGl = null; }
  if (!testGl) { status('WebGL 不可用，回退静态封面'); return { ok: false, dispose() {} }; }

  const W = cfg.cardWidth || 2;
  const H = cfg.cardHeight || 3;
  const THICK = cfg.thickness || 0.14;

  let renderer, composer, bloomOn = true;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  } catch (e) {
    status('WebGL 初始化失败，回退静态封面'); return { ok: false, dispose() {} };
  }
  const isDark = !!(window.HoloLabTheme && HoloLabTheme.get() === 'dark');
  renderer.setClearColor(isDark ? 0x12100d : 0xf6f4ee, 1);
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;

  // —— 素材 ——
  const [bgImg, subImg, txtImg, glow] = await Promise.all([
    loadImage(cfg.background), loadImage(cfg.subject),
    loadImage(cfg.text), makeGlowTextures(cfg.lineart),
  ]);
  const bgTex = new THREE.Texture(bgImg); bgTex.colorSpace = THREE.SRGBColorSpace; bgTex.needsUpdate = true;
  const subTex = new THREE.Texture(subImg); subTex.colorSpace = THREE.SRGBColorSpace; subTex.needsUpdate = true;
  const txtTex = new THREE.Texture(txtImg); txtTex.colorSpace = THREE.SRGBColorSpace; txtTex.needsUpdate = true;
  const bgMat  = new THREE.MeshBasicMaterial({ map: bgTex });
  const subMat = new THREE.MeshBasicMaterial({ map: subTex, transparent: true, depthWrite: false });
  const txtMat = new THREE.MeshBasicMaterial({ map: txtTex, transparent: true, depthWrite: false });
  const lineMat = new THREE.MeshBasicMaterial({ map: glow.line, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const glowMat = new THREE.MeshBasicMaterial({ map: glow.glow, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });

  // —— 场景 ——
  const scene = new THREE.Scene();
  const grp = new THREE.Group();

  // 实体卡体：圆角、有厚度、金属质感（随光线转动有高光与厚度）
  const cardBody = new THREE.Mesh(
    new RoundedBoxGeometry(W, H, THICK, 3, 0.08),
    new THREE.MeshStandardMaterial({
      color: cfg.frameColor || 0xc8a25a,
      metalness: 0.85, roughness: 0.32, envMapIntensity: 0.8,
    })
  );
  grp.add(cardBody);

  // 卡面（背景）贴在卡体正面（不透明，提供深度基准）
  const face = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.09, H - 0.09), bgMat);
  face.position.z = THICK / 2;
  face.renderOrder = 1;
  grp.add(face);

  // 悬浮层：真实深度差 → 真视差（主体视觉零损失）
  // 层距 ≥0.025 世界单位 + renderOrder 固定，避免透明层 z-fighting 频闪
  const l2 = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.14, H - 0.14), glowMat);  // 光晕（最底）
  l2.position.z = THICK / 2 + 0.025;
  l2.renderOrder = 2;
  const l1 = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.16, H - 0.16), lineMat);  // 发光描边
  l1.position.z = THICK / 2 + 0.05;
  l1.renderOrder = 3;
  const l4 = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.18, H - 0.18), txtMat);   // 文字
  l4.position.z = THICK / 2 + 0.075;
  l4.renderOrder = 4;
  const l3 = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.18, H - 0.18), subMat);   // 主体（最顶）
  l3.position.z = THICK / 2 + 0.11;
  l3.renderOrder = 5;
  grp.add(l1, l2, l3, l4);

  // 卡框边缘发光条
  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new RoundedBoxGeometry(W, H, THICK, 3, 0.08)),
    new THREE.LineBasicMaterial({ color: 0x7dd3fc, transparent: true, opacity: 0.35 })
  );
  grp.add(edge);

  scene.add(grp);

  // —— 光照 ——
  scene.add(new THREE.AmbientLight(0x404860, 0.9));
  const key = new THREE.DirectionalLight(0xfff2dd, 2.4);
  key.position.set(4, 6, 5);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x4aa8ff, 1.2);
  rim.position.set(-5, -2, -4);
  scene.add(rim);
  const back = new THREE.PointLight(0x7dd3fc, 2, 12);
  back.position.set(0, 1.5, -2.5);
  scene.add(back);

  // —— 相机与轨道 ——
  const cam = new THREE.PerspectiveCamera(42, 1, 0.1, 30);
  cam.position.set(0, 0.1, 4.6);
  const ctrl = new OrbitControls(cam, canvas);
  ctrl.enableDamping = true;
  ctrl.autoRotate = cfg.autoRotate !== false;
  ctrl.autoRotateSpeed = 1.6;

  // —— Bloom（帧率低可关）——
  const comp = new EffectComposer(renderer);
  comp.addPass(new RenderPass(scene, cam));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.55, 0.35, 0.82);
  comp.addPass(bloom);

  function resize() {
    const w = Math.max(canvas.clientWidth, 2), h = Math.max(canvas.clientHeight, 2);
    renderer.setSize(w, h, false);
    cam.aspect = w / h; cam.updateProjectionMatrix();
    comp.setSize(w, h);
  }
  window.addEventListener('resize', resize);
  resize();

  let raf = 0;
  const clock = new THREE.Clock();
  function tick() {
    raf = requestAnimationFrame(tick);
    ctrl.update();
    if (bloomOn) comp.render(); else renderer.render(scene, cam);
  }
  tick();
  status('渲染中 ✓（C 方案真 3D 卡框）');

  return {
    ok: true,
    setAutoRotate: (on) => { ctrl.autoRotate = on; },
    reset: () => { ctrl.reset(); },
    setBloom: (on) => { bloomOn = on; },
    dispose() {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      ctrl.dispose();
      renderer.dispose();
      [bgTex, subTex, txtTex, glow.line, glow.glow].forEach(t => t.dispose());
    },
  };
}
