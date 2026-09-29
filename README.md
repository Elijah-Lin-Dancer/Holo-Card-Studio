# 🃏 HoloLab Studio

**一句话 → 一张会随视线流动光影的 3D 全息卡 → 一个全球可玩的在线展厅。**

HoloLab Studio 是一条完整的 **AIGC 全链路系统**：用豆包 Seedream 图像生成模型把
一句话（或一张参考照片）分层绘制成卡面素材，交给 Blender 构建带视差/镭射的 3D
场景，导出 GLB 后在浏览器里用 Three.js 实时合成——主体往前凸、背景往后缩、
镭射彩虹随角度流转。生成好的卡片通过一键发布脚本进入纯静态展厅（GitHub
Pages 托管，零服务器、零数据库），任何人打开链接即可拖拽、翻面、调节光影。

> 作品集项目 · AI × 3D 交叉方向
> 分层素材：豆包 Seedream 5.0 生成 + rembg 抠图 + OpenCV 线稿提取
> 3D 管线：Blender 4.5（自动下载便携版）→ glTF 导出
> 实时渲染：Three.js + GLSL 着色器（视差 / 镭射 / 星光 / 辉光）

---

## ✨ 为什么值得看

这个项目不是"调一个图像模型出张图"，而是一条把生成模型真正落地成可玩产品的
完整工程链路，覆盖：

| 能力维度 | 具体体现 |
|---|---|
| **AI 应用开发** | 豆包 Seedream API 集成；主体/背景/线稿/文字四层**分而治之**的生成策略；提示词工程；以图生图保留主体 |
| **3D 图形学** | Blender 程序化场景（视差 UV、镭射材质节点组）；glTF 导出；Three.js GLSL 片段着色器实时重建材质 |
| **系统工程** | Python 流水线（生成 → 校验 → 渲染 → 导出 → 发布）；静态站点生成；一键发布脚本；CI/CD 就绪 |
| **产品设计** | 瀑布流展厅、每卡永久 URL、风格筛选、移动端适配、分享即玩 |

## 🧱 系统架构

```
┌─────────────────────────── 本地工具链 ───────────────────────────┐
│  一句话 / 一张照片                                                 │
│     │                                                            │
│     ▼                                                            │
│  ai_generate.py（豆包 Seedream 5.0）                              │
│     ├─ 主体层 subject.png   生成 → rembg 抠图 → 透明底 PNG        │
│     ├─ 背景层 background.png 同风格环境空镜（中下部留白叠字）      │
│     ├─ 线稿层 lineart.png   OpenCV 从透明主体提取轮廓（像素级注册）│
│     └─ 文字层 text.png      精确字体排版（不让 AI 画字）          │
│     │                                                            │
│     ▼                                                            │
│  run_pipeline.py（Blender 4.5 自动下载 + SHA-256 校验）           │
│     ├─ card.blend            可编辑的 3D 场景                     │
│     ├─ renders/hero.png      Cycles 渲染正面图                    │
│     └─ web/                  Three.js 查看器 + card.glb           │
│     │                                                            │
│     ▼                                                            │
│  publish_card.py（一键发布）                                      │
└───────────────────────────┬──────────────────────────────────────┘
                           │ git push（纯静态，零后端）
                           ▼
        GitHub Pages 在线展厅（瀑布流 + 筛选 + 每卡独立 URL）
```

## 🚀 快速开始

### 环境要求

- Python 3.10+，`pip install pillow opencv-python-headless rembg onnxruntime`
- Node.js 18+（查看器依赖 three.js）
- 豆包（火山方舟）API Key —— 写入项目根目录 `.env`：

```bash
# .env（已被 .gitignore 忽略，勿提交）
ARK_API_KEY=你的密钥
```

Blender **无需手动安装**：流水线会自动下载官方便携版到 `<项目>/tools/` 并校验
SHA-256（国内网络可先手动从清华镜像下载同名包放入 `tools/`）。

### 做一张新卡

1. 建项目目录，写 `card-config.json`（参考 `generator/projects/messi-demo/card-config.json`）
2. 分层生成素材：

```bash
python3 generator/scripts/ai_generate.py --project generator/projects/<id>
```

3. 跑流水线（Blender 渲染 + GLB 导出 + 查看器）：

```bash
python3 generator/scripts/run_pipeline.py --project generator/projects/<id>
```

4. 本地预览：

```bash
cd generator/projects/<id>/web && npm install && node server.mjs
# 打开 http://127.0.0.1:4173
```

5. 发布进展厅（**自动完成压缩 + 预览动画渲染**）：

```bash
python3 generator/scripts/publish_card.py --project generator/projects/<id> --id <id> --tags "风格,题材"
cd gallery && python3 -m http.server 4174   # 预览展厅
```

发布脚本会自动：四层贴图 PNG→WebP 压缩（保留透明通道）、定位 Blender 并渲染 96 帧旋转预览动画 → ffmpeg 合成 `preview.webm`、更新 `cards.json` 清单。重跑幂等（已有 webp/动画自动跳过）；`--skip-preview` 可跳过动画渲染。

部署到 GitHub Pages 见 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)（三步上线）。

### 一句话自动出卡（One-Sentence Card Generator）

无需手写配置——给一句话，文字模型自动生成整张卡的配置并接入流水线：

```bash
# 1. 生成配置（默认文字模型 doubao-seed-2-0-mini-260428）
python3 generator/scripts/one_shot_card.py "给中国航天员设计一张全息收藏卡"

# 2-4. 走标准流水线出卡、渲染、发布（见上文「做一张新卡」）
```

发布阶段全自动：压缩 + 预览动画 + 清单更新一键完成，无需任何手动渲染/压缩步骤。

示例输出（自动校验 + 编号 + 渲染参数，直接可跑流水线）：

```json
{
  "title": "星辰远征",
  "subtitle": "taikonaut · 逐梦星海",
  "technique": "星海驭风",
  "tagline": "逐梦苍穹，远征星海",
  "collection": "HoloLab 典藏 · 星辰远征系列"
}
```

展厅第三张卡即由该工具生成：`一句话 → 全息卡` 全自动闭环。

### 做一张参考图卡（宠物、朋友、角色）

```bash
python3 generator/scripts/ai_generate.py --project generator/projects/<id> --reference 照片路径
```

Seedream 会保留照片中主体的姿态与构图，重绘为卡牌风格。

## 📁 目录结构

```
holo-lab/
├── generator/
│   ├── scripts/
│   │   ├── one_shot_card.py      # 一句话自动出卡（文字模型 → card-config.json）
│   │   ├── ai_generate.py        # 豆包 Seedream 分层画图（本项目的核心增量）
│   │   ├── run_pipeline.py       # 流水线编排（Blender 构建/渲染/导出）
│   │   ├── build_card.py         # Blender 程序化场景 + 材质节点
│   │   ├── export_web.py         # glTF/GLB 导出
│   │   ├── generate_typography.py# 文字层精确排版
│   │   ├── validate_assets.py    # 四层素材体检（真实 alpha / 线稿极值）
│   │   ├── ensure_blender.py     # Blender 自动下载 + SHA-256 校验
│   │   ├── render_preview.py     # 旋转预览帧渲染（360×500 / 96 帧）
│   │   ├── publish_card.py       # 一键发布：压缩 + 预览动画 + 清单（核心增量）
│   │   └── web-template-holographic/  # Three.js 查看器模板
│   └── projects/<card-id>/       # 每张卡的项目目录（素材/场景/产物）
├── gallery/                      # 纯静态展厅（可直接推 GitHub Pages）
│   ├── index.html                # 瀑布流首页
│   ├── cards.json                # 卡片清单（JSON 驱动，无数据库）
│   ├── vendor/three/             # 共享 three.js 依赖
│   └── cards/<card-id>/          # 每张卡的查看器 + 资产 + 缩略图
├── docs/
│   ├── DEPLOYMENT.md             # GitHub Pages 部署指南
│   ├── architecture.md           # 系统设计
│   ├── ai-pipeline.md            # AI 分层生成策略
│   └── graphics.md               # 3D 渲染与着色器原理
└── .github/workflows/deploy.yml  # CI 自动部署
```

## 📖 深入阅读

- [`docs/architecture.md`](docs/architecture.md) —— 系统设计与分层决策
- [`docs/ai-pipeline.md`](docs/ai-pipeline.md) —— 四层生成策略、提示词工程、抠图与线稿提取
- [`docs/graphics.md`](docs/graphics.md) —— 视差 UV、镭射材质、GLSL 着色器原理
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) —— 上线步骤

## 🎴 示例卡

- 「梅西称王」—— 球王 · 阿根廷十号 · 全息典藏系列
- 「流行之王」—— 迈克尔·杰克逊 · 舞台之巅 · 传奇系列
- 「星辰远征」—— 中国航天员 · 逐梦星海 · 星辰远征系列（一句话自动出卡生成）
- 「齐天大圣」—— 孙悟空 · 傲世苍穹 · 西游系列（一句话自动出卡生成）

## 🛤️ 路线图

- [x] 豆包 Seedream 分层生成 + 抠图 + 线稿提取
- [x] Blender 全息流水线 + Three.js 查看器
- [x] 静态展厅 + 一键发布 + CI 部署就绪
- [x] 素材体积压缩（PNG→WebP，-81%，已入发布流水线）
- [x] 卡片动态预览（Blender 旋转序列 → preview.webm + hover 播放，已入发布流水线）
- [x] 一句话自动出卡（文字模型 → 配置 → 全自动闭环）
- [ ] lenticular 双图光栅模式接入
- [ ] 展厅自动分类（按人物/风格/稀有度）

## ⚖️ 开源声明

本项目在开源项目 [EverettFish/holo-card-studio](https://github.com/EverettFish/holo-card-studio)
（MIT License）基础上二次开发。个人增量包括：**AI 分层画图自动化**（原项目依赖
Codex 人工调用图像模型，本项目改为可复现的豆包 API 管线）、**OpenCV 线稿提取**、
**一键发布与静态展厅系统**、**部署与文档体系**。Blender 场景构建脚本沿用原项目
的实现，素材规范兼容原项目格式。

## 📄 License

MIT
