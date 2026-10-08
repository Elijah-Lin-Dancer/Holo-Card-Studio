// foil_holographic.glsl — 物理仿真全息材质（薄膜干涉 ⊕ 光栅衍射）
// 详情页 WebGL 实时渲染版本。数学与 docs/GRAPHICS/HOLO-OPTICS.md §4.1、
// generator/foil/proto_render.py（numpy 原型）完全一致：6 波长累加 + 归一化。
// 兼容 GLSL ES 3.00（WebGL2 / Three.js ShaderMaterial）。
#version 300 es
precision highp float;
precision highp int;

// ---------------- uniforms（每张卡一组 = 光学指纹，来自 card-config） ----------------
uniform float u_thicknessNm;      // 薄膜厚度 nm（油彩色相主控）
uniform float u_ior;              // 介质折射率
uniform float u_periodUm;         // 光栅周期 μm（彩虹展开宽度，Λ↑ → 彩虹窄）
uniform vec3  u_grooveDir;        // 沟槽方向（切向空间，单位向量）
uniform float u_roughness;        // 微表面粗糙度（0..1）
uniform float u_gain;             // 彩虹增益
uniform float u_baseReflect;      // 基底反射率

// ---------------- varyings ----------------
in  vec3 vNormal;                 // 片元法线（观察空间）
in  vec3 vViewDir;                // 片元 → 相机（观察空间）
out vec4 fragColor;

const float PI     = 3.14159265358979;
const float TWO_PI = 6.28318530717959;

// 波长 → sRGB 近似（与 numpy 原型的 CIE 四段线性完全一致，lam 单位 nm）
vec3 wavelengthToRGB(float lam) {
    vec3 c = vec3(0.0);
    if (lam < 450.0) {                            // 380..450nm
        float q = (lam - 380.0) / 70.0;
        c = vec3(0.55 * q, 0.18 * q, 1.0 - 0.6 * q);
    } else if (lam < 510.0) {                     // 450..510nm
        float q = (lam - 450.0) / 60.0;
        c = vec3(0.55 - 0.2 * q, 0.18 + 0.82 * q, 0.4 - 0.4 * q);
    } else if (lam < 590.0) {                     // 510..590nm
        float q = (lam - 510.0) / 80.0;
        c = vec3(0.35 + 0.6 * q, 1.0 - 0.15 * q, 0.0);
    } else {                                      // 590..700nm
        float q = (lam - 590.0) / 110.0;
        c = vec3(0.95 - 0.35 * q, 0.85 - 0.6 * q, 0.0);
    }
    return c;
}

// 薄膜反射率（Airy 单程近似 + 半波损失），同 numpy：Rf = 0.5*(1-cos(phase))
float thinFilmReflectance(float lamNm, float cosThetaT) {
    float C = TWO_PI * u_ior * u_thicknessNm / lamNm;
    float phase = C * cosThetaT + PI;            // +π 半波损失
    return 0.5 * (1.0 - cos(phase));
}

void main() {
    vec3 N = normalize(vNormal);
    vec3 V = normalize(vViewDir);

    // ---- 入射几何 ----
    float cosI = clamp(dot(N, V), 0.0, 1.0);
    float sinT = min(1.0, sqrt(max(1.0 - cosI * cosI, 0.0)) / max(u_ior, 1.01));
    float cosT = sqrt(max(1.0 - sinT * sinT, 0.0));

    // ---- 沟槽坐标系：flatV = V - N·dot(N,V)，v = dot(flatV, B)/|flatV| ----
    vec3 flatV = V - N * dot(N, V);
    float lenF = max(length(flatV), 1e-6);
    vec3 B = normalize(u_grooveDir - N * dot(N, u_grooveDir));   // 投影到表面
    float v = dot(flatV, B) / lenF;

    // ---- 微表面权重 ----
    float grazing  = pow(max(1.0 - cosI, 0.0), 0.5);
    float wGrating = clamp(u_gain * (1.0 - u_roughness) * (0.35 + 0.65 * grazing), 0.0, 1.0);
    float dispK    = 0.5 * (1.8 / max(u_periodUm, 0.1));        // 色散斜率 ∝ 1/Λ

    // ---- 6 波长累加（380..700nm）同 numpy 原型 ----
    const int Nw = 6;
    float lam[Nw] = float[Nw](380.0, 444.0, 508.0, 572.0, 636.0, 700.0);
    vec3 acc = vec3(0.0);
    float sumw = 0.0;
    for (int i = 0; i < Nw; i++) {
        float lamNorm = (lam[i] - 380.0) / 320.0;                // 0..1
        float peak = clamp(lamNorm - v * dispK, 0.0, 1.0);
        float wBand = exp(-pow(peak / 0.22, 2.0)) * (1.0 - u_roughness * 2.2);
        float Rf = thinFilmReflectance(lam[i], cosT);
        float wSpec = 0.95 * wGrating * wBand
                    + 0.5 * (1.0 - wGrating) * Rf * (1.0 - 0.8 * wBand);
        acc += wavelengthToRGB(lamNorm) * wSpec;
        sumw += wSpec;
    }
    if (sumw > 1e-6) acc /= sumw;

    fragColor = vec4(acc * u_baseReflect, 1.0);
}
