"""HoloLab Studio · render_preview.py
方案 B：用 card.blend 内置转卡动画渲染帧序列，供 ffmpeg 合成 preview.webm。
用法：blender --background --python render_preview.py -- <project_dir> <out_dir> [start] [end]
"""
import bpy, sys
from pathlib import Path

args = sys.argv[sys.argv.index("--") + 1:]
project, outdir = Path(args[0]), Path(args[1])
start = int(args[2]) if len(args) > 2 else 1
end = int(args[3]) if len(args) > 3 else 64

blend = project / "card.blend"
outdir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene

# 渲染设置：低分辨率帧序列，控制合成体积与渲染时长
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
try:
    scene.cycles.use_denoising = False
except Exception:
    pass
scene.render.resolution_x = 320
scene.render.resolution_y = 444
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 64

# 保证「转卡控制」动画就位
pivot = bpy.data.objects.get("转卡控制 · 播放时间线预览")
print(f"[preview] pivot={'OK' if pivot else 'MISSING'}  frames={start}..{end}  size=320x444")

for f in range(start, end + 1):
    scene.frame_set(f)
    scene.render.filepath = str(outdir / f"frame_{f:04d}")
    bpy.ops.render.render(write_still=True)

print(f"[preview] done → {outdir}（{end - start + 1} 帧）")
