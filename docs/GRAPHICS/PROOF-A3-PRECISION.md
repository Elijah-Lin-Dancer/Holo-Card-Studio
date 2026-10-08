A-3 物理仿真全息 Shader 精度报告（6 波长精确版）
=====================================================
1. GLSL vs numpy 参考模型（同公式等值执行，3 组）：
   default / view(θ=0.4) / thick(420nm) → ΔE76 = 0.000（>8 占比 0%）
2. Blender Node Group 6 波长 vs 参考模型（中心像素，Standard 域）：
   ΔE76 = 4.656 ✅ < 8（残差来源：8bit PNG 量化 + 24 采样噪声 + sRGB 编码往返）
3. Node Group 3 通道近似（历史版本）vs 参考模型：
   ΔE76 mean = 27.9~38.5，>8 占比 100% → 不合格，故升级 6 波长
4. 视角驱动验证：两帧平均色差 0.033（正视角 vs 旋转30°，色相随视角位移）
5. 关键踩坑记录：
   - Blender 4.5 Math 三角函数单位为「度」→ phase 弧度必须先 DEGREES 再 COSINE
   - CIE 常数权重必须由 wavelength_to_rgb 精确取值（572nm x=0.815 而非 0.665）
   - 渲染验证须 view_transform='Standard'（Filmic 会把物理色相压成灰白）
