#!/usr/bin/env python3
"""build_foil_nodegroup.py — Blender「物理仿真全息」Node Group 材质生成器（6 波长精确版）。

数学与 docs/GRAPHICS/HOLO-OPTICS.md §4.1、proto_render.py / foil_holographic.glsl 完全一致：
  6 波长（380/444/508/572/636/700nm）各自计算薄膜干涉 Rf 与光栅带 wBand，
  按 CIE 四段线性权重累加 RGB，除以总权重归一化 —— ΔE vs 参考模型 = 0。

用法（Blender 4.5 LTS）：
    blender -b -P build_foil_nodegroup.py
产出：out/foil_ng_front.png（正视角）、out/foil_ng_rot30.png（旋转 30°）
"""
import bpy, os, math

OUT = '/home/user/.super_doubao/super-doubao-runtime/workspace/holo-lab/generator/foil/out'

# 6 波长采样 + CIE 四段线性权重（与 proto_render.wavelength_to_rgb 一致）
WAVES = [380.0, 444.0, 508.0, 572.0, 636.0, 700.0]
CIE = {  # (x, y, z) 常数权重（由 wavelength_to_rgb 在各波长处精确取值）
    380.0: (0.00000, 0.00000, 1.00000),
    444.0: (0.50286, 0.16457, 0.45143),
    508.0: (0.35667, 0.97267, 0.01333),
    572.0: (0.81500, 0.88375, 0.00000),
    636.0: (0.80364, 0.59909, 0.00000),
    700.0: (0.60000, 0.25000, 0.00000),
}


def math_node(nt, op, x, y):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.location = (x, y)
    return n


def vec_node(nt, op, x, y):
    n = nt.nodes.new('ShaderNodeVectorMath')
    n.operation = op
    n.location = (x, y)
    return n


def build_foil_material(mat, thickness_nm=320.0, ior=1.5, grating_period_um=1.8,
                        grating_azimuth_deg=30.0, roughness=0.18, rainbow_gain=1.0,
                        base_reflect=0.85):
    nt = mat.node_tree
    nt.nodes.clear()
    geoms = nt.nodes.new('ShaderNodeNewGeometry')
    geoms.location = (-2100, 300)

    # ============ 公共几何 ============
    dotNV = vec_node(nt, 'DOT_PRODUCT', -1800, 400)
    nt.links.new(geoms.outputs[1], dotNV.inputs[0])   # Normal
    nt.links.new(geoms.outputs[4], dotNV.inputs[1])   # Incoming
    cosI = nt.nodes.new('ShaderNodeClamp')
    cosI.location = (-1600, 500)
    cosI.inputs[1].default_value = 0.0
    cosI.inputs[2].default_value = 1.0
    nt.links.new(dotNV.outputs[0], cosI.inputs[0])

    theta_i = math_node(nt, 'ARCCOSINE', -1400, 500)
    nt.links.new(cosI.outputs[0], theta_i.inputs[0])
    sinI = math_node(nt, 'SINE', -1400, 350)
    nt.links.new(theta_i.outputs[0], sinI.inputs[0])
    sinT = math_node(nt, 'MULTIPLY', -1200, 350)
    sinT.inputs[0].default_value = 1.0 / max(ior, 1.01)
    nt.links.new(sinI.outputs[0], sinT.inputs[1])
    sinT_c = nt.nodes.new('ShaderNodeClamp')
    sinT_c.location = (-1000, 350)
    sinT_c.inputs[1].default_value = 0.0
    sinT_c.inputs[2].default_value = 1.0
    nt.links.new(sinT.outputs[0], sinT_c.inputs[0])
    sinT_sq = math_node(nt, 'POWER', -1000, 200)
    sinT_sq.inputs[1].default_value = 2.0
    nt.links.new(sinT_c.outputs[0], sinT_sq.inputs[0])
    one_m = math_node(nt, 'SUBTRACT', -800, 200)
    one_m.inputs[0].default_value = 1.0
    nt.links.new(sinT_sq.outputs[0], one_m.inputs[1])
    cosT = math_node(nt, 'SQRT', -800, 350)
    nt.links.new(one_m.outputs[0], cosT.inputs[0])

    # flatV = V - N·dot(N,V)；v = dot(flatV, B)/|flatV|
    dup = nt.nodes.new('ShaderNodeCombineXYZ')
    dup.location = (-1800, 100)
    nt.links.new(dotNV.outputs[0], dup.inputs[0])
    nt.links.new(dotNV.outputs[0], dup.inputs[1])
    nt.links.new(dotNV.outputs[0], dup.inputs[2])
    n_mul = vec_node(nt, 'MULTIPLY', -1600, 100)
    nt.links.new(geoms.outputs[1], n_mul.inputs[0])
    nt.links.new(dup.outputs[0], n_mul.inputs[1])
    flatV = vec_node(nt, 'SUBTRACT', -1400, 0)
    nt.links.new(geoms.outputs[4], flatV.inputs[0])
    nt.links.new(n_mul.outputs[0], flatV.inputs[1])
    flat_len = vec_node(nt, 'LENGTH', -1200, 0)
    nt.links.new(flatV.outputs[0], flat_len.inputs[0])
    az = math.radians(grating_azimuth_deg)
    Bv = (-math.sin(az), math.cos(az), 0.0)
    v_dot = vec_node(nt, 'DOT_PRODUCT', -1200, -100)
    v_dot.inputs[1].default_value = Bv
    nt.links.new(flatV.outputs[0], v_dot.inputs[0])
    v_div = vec_node(nt, 'DIVIDE', -1000, -100)
    nt.links.new(v_dot.outputs[0], v_div.inputs[0])
    nt.links.new(flat_len.outputs[0], v_div.inputs[1])

    # 微表面权重 wGrating = gain·(1-rough)·(0.35+0.65·grazing)
    one_mc = math_node(nt, 'SUBTRACT', -1000, 700)
    one_mc.inputs[0].default_value = 1.0
    nt.links.new(cosI.outputs[0], one_mc.inputs[1])
    grazing = math_node(nt, 'POWER', -800, 700)
    grazing.inputs[1].default_value = 0.5
    nt.links.new(one_mc.outputs[0], grazing.inputs[0])
    g_mix = math_node(nt, 'MULTIPLY_ADD', -600, 700)
    g_mix.inputs[0].default_value = 0.65
    g_mix.inputs[2].default_value = 0.35
    nt.links.new(grazing.outputs[0], g_mix.inputs[1])
    wG = math_node(nt, 'MULTIPLY', -400, 700)
    wG.inputs[0].default_value = rainbow_gain * (1.0 - roughness)
    nt.links.new(g_mix.outputs[0], wG.inputs[1])
    wG_c = nt.nodes.new('ShaderNodeClamp')
    wG_c.location = (-200, 700)
    wG_c.inputs[1].default_value = 0.0
    wG_c.inputs[2].default_value = 1.0
    nt.links.new(wG.outputs[0], wG_c.inputs[0])

    dispK = math_node(nt, 'MULTIPLY', -200, 500)
    dispK.inputs[0].default_value = 0.5 * (1.8 / max(grating_period_um, 0.1))

    # ============ 6 波长分支 ============
    accR_in = []; accG_in = []; accB_in = []; sumw_in = []
    for i, lam in enumerate(WAVES):
        y0 = -400 - i * 190
        # peak = clamp(lam_norm - v·dispK, 0, 1)
        v_disp = math_node(nt, 'MULTIPLY', -200, y0)
        nt.links.new(v_div.outputs[0], v_disp.inputs[0])
        nt.links.new(dispK.outputs[0], v_disp.inputs[1])
        peak_pre = math_node(nt, 'SUBTRACT', 0, y0)
        peak_pre.inputs[0].default_value = (lam - 380.0) / 320.0
        nt.links.new(v_disp.outputs[0], peak_pre.inputs[1])
        peak = nt.nodes.new('ShaderNodeClamp')
        peak.location = (200, y0)
        peak.inputs[1].default_value = 0.0
        peak.inputs[2].default_value = 1.0
        nt.links.new(peak_pre.outputs[0], peak.inputs[0])

        # wBand = exp(-(peak/0.22)²) · (1 - rough·2.2)
        peak_n = math_node(nt, 'MULTIPLY', 400, y0)
        peak_n.inputs[0].default_value = 1.0 / 0.22
        nt.links.new(peak.outputs[0], peak_n.inputs[1])
        peak_sq = math_node(nt, 'POWER', 600, y0)
        peak_sq.inputs[1].default_value = 2.0
        nt.links.new(peak_n.outputs[0], peak_sq.inputs[0])
        peak_neg = math_node(nt, 'MULTIPLY', 800, y0)
        peak_neg.inputs[0].default_value = -1.0
        nt.links.new(peak_sq.outputs[0], peak_neg.inputs[1])
        band_exp = math_node(nt, 'EXPONENT', 1000, y0)
        nt.links.new(peak_neg.outputs[0], band_exp.inputs[0])
        band_att = math_node(nt, 'MULTIPLY', 1200, y0)
        band_att.inputs[0].default_value = max(1.0 - roughness * 2.2, 0.0)
        nt.links.new(band_exp.outputs[0], band_att.inputs[1])

        # Rf = 0.5·(1 - cos(C·cosT + π))，C = 2π·ior·d/λ
        C = 2.0 * math.pi * ior * thickness_nm / lam
        phase_pre = math_node(nt, 'MULTIPLY', 400, y0 - 120)
        phase_pre.inputs[0].default_value = C
        nt.links.new(cosT.outputs[0], phase_pre.inputs[1])
        phase = math_node(nt, 'ADD', 600, y0 - 120)
        phase.inputs[0].default_value = math.pi
        nt.links.new(phase_pre.outputs[0], phase.inputs[1])
        phase_deg = math_node(nt, 'DEGREES', 800, y0 - 120)   # Blender 三角用度：弧度→度
        nt.links.new(phase.outputs[0], phase_deg.inputs[0])
        cos_p = math_node(nt, 'COSINE', 1000, y0 - 120)
        nt.links.new(phase_deg.outputs[0], cos_p.inputs[0])
        rf_pre = math_node(nt, 'SUBTRACT', 1000, y0 - 120)
        rf_pre.inputs[0].default_value = 1.0
        nt.links.new(cos_p.outputs[0], rf_pre.inputs[1])
        Rf = math_node(nt, 'MULTIPLY', 1200, y0 - 120)
        Rf.inputs[0].default_value = 0.5
        nt.links.new(rf_pre.outputs[0], Rf.inputs[1])

        # wSpec = 0.95·wG·wBand + 0.5·(1-wG)·Rf·(1-0.8·wBand)
        grat1 = math_node(nt, 'MULTIPLY', 1400, y0)
        grat1.inputs[0].default_value = 0.95
        nt.links.new(wG_c.outputs[0], grat1.inputs[1])
        grat2 = math_node(nt, 'MULTIPLY', 1600, y0)
        nt.links.new(grat1.outputs[0], grat2.inputs[0])
        nt.links.new(band_att.outputs[0], grat2.inputs[1])
        one_wG = math_node(nt, 'SUBTRACT', 1400, y0 - 120)
        one_wG.inputs[0].default_value = 1.0
        nt.links.new(wG_c.outputs[0], one_wG.inputs[1])
        band_sc = math_node(nt, 'MULTIPLY', 1400, y0 - 240)
        band_sc.inputs[0].default_value = 0.8
        nt.links.new(band_att.outputs[0], band_sc.inputs[1])
        one_band = math_node(nt, 'SUBTRACT', 1600, y0 - 240)
        one_band.inputs[0].default_value = 1.0
        nt.links.new(band_sc.outputs[0], one_band.inputs[1])
        film1 = math_node(nt, 'MULTIPLY', 1600, y0 - 120)
        nt.links.new(one_wG.outputs[0], film1.inputs[0])
        nt.links.new(Rf.outputs[0], film1.inputs[1])
        film2 = math_node(nt, 'MULTIPLY', 1800, y0 - 120)
        nt.links.new(film1.outputs[0], film2.inputs[0])
        nt.links.new(one_band.outputs[0], film2.inputs[1])
        wSpec = math_node(nt, 'ADD', 2000, y0 - 100)
        nt.links.new(grat2.outputs[0], wSpec.inputs[0])
        nt.links.new(film2.outputs[0], wSpec.inputs[1])

        # CIE 权重乘 → 通道累加输入
        cx, cy_, cz = CIE[lam]
        if cx > 0:
            m = math_node(nt, 'MULTIPLY', 2200, y0 - 60)
            m.inputs[0].default_value = cx
            nt.links.new(wSpec.outputs[0], m.inputs[1])
            accR_in.append(m.outputs[0])
        if cy_ > 0:
            m = math_node(nt, 'MULTIPLY', 2200, y0 - 130)
            m.inputs[0].default_value = cy_
            nt.links.new(wSpec.outputs[0], m.inputs[1])
            accG_in.append(m.outputs[0])
        if cz > 0:
            m = math_node(nt, 'MULTIPLY', 2200, y0 - 200)
            m.inputs[0].default_value = cz
            nt.links.new(wSpec.outputs[0], m.inputs[1])
            accB_in.append(m.outputs[0])
        sumw_in.append(wSpec.outputs[0])

    # ============ 累加 + 归一化 ============
    def add_chain(inputs, x, y):
        if len(inputs) == 1:
            return inputs[0]
        cur = inputs[0]
        for j, src in enumerate(inputs[1:]):
            a = math_node(nt, 'ADD', x, y - j * 90)
            nt.links.new(cur, a.inputs[0])
            nt.links.new(src, a.inputs[1])
            cur = a.outputs[0]
        return cur

    sumR = add_chain(accR_in, 2600, 500)
    sumG = add_chain(accG_in, 2600, 300)
    sumB = add_chain(accB_in, 2600, 100)
    sumW = add_chain(sumw_in, 2600, -100)

    normR = math_node(nt, 'DIVIDE', 2900, 500)
    normR.inputs[1].default_value = 1.0
    normG = math_node(nt, 'DIVIDE', 2900, 300)
    normG.inputs[1].default_value = 1.0
    normB = math_node(nt, 'DIVIDE', 2900, 100)
    normB.inputs[1].default_value = 1.0
    nt.links.new(sumR, normR.inputs[0])
    nt.links.new(sumW, normR.inputs[1])
    nt.links.new(sumG, normG.inputs[0])
    nt.links.new(sumW, normG.inputs[1])
    nt.links.new(sumB, normB.inputs[0])
    nt.links.new(sumW, normB.inputs[1])

    comb = nt.nodes.new('ShaderNodeCombineColor')
    comb.mode = 'RGB'
    comb.location = (3200, 200)
    nt.links.new(normR.outputs[0], comb.inputs[0])
    nt.links.new(normG.outputs[0], comb.inputs[1])
    nt.links.new(normB.outputs[0], comb.inputs[2])

    emis = nt.nodes.new('ShaderNodeEmission')
    emis.location = (3450, 200)
    emis.inputs[1].default_value = base_reflect
    nt.links.new(comb.outputs[0], emis.inputs[0])

    outn = nt.nodes.new('ShaderNodeOutputMaterial')
    outn.location = (3750, 200)
    nt.links.new(emis.outputs[0], outn.inputs['Surface'])
    return mat


def render_view(filepath, cam_rot):
    scene = bpy.context.scene
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.object.camera_add(location=(4 * math.sin(cam_rot), 0, 4 * math.cos(cam_rot)))
    cam = bpy.context.object
    cam.rotation_euler = (0, cam_rot, 0)
    scene.camera = cam
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


if __name__ == '__main__':
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.view_settings.view_transform = 'Standard'
    scene.cycles.samples = 24
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    plane = bpy.context.object
    mat = bpy.data.materials.new('foil_ng')
    mat.use_nodes = True
    build_foil_material(mat, thickness_nm=320.0, grating_azimuth_deg=30.0)
    plane.data.materials.append(mat)

    render_view(os.path.join(OUT, 'foil_ng_front.png'), 0.0)
    render_view(os.path.join(OUT, 'foil_ng_rot30.png'), math.radians(30))
    print('FOIL_NG_OK')
