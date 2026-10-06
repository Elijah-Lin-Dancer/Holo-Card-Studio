<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="HoloLab Studio — 一句话 → 一张 3D 全息卡 → 一个在线展厅" width="100%">
</p>

<h1 align="center">🃏 HoloLab Studio ✨</h1>

<p align="center"><b>一句话 → 一张随视线流动光影的 3D 全息卡 → 一个全世界任何人都能打开的在线展厅。</b></p>

<p align="center">
  🌐 <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><b>https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/</b></a>
</p>

<p align="center">
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_%E5%9C%A8%E7%BA%BF%E5%B1%95%E5%8E%85-%E7%AB%8B%E5%8D%B3%E4%BD%93%E9%AA%8C-7fd4ff?style=for-the-badge" alt="在线展厅"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/%F0%9F%93%9C_%E8%AE%B8%E5%8F%AF-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio"><img src="https://img.shields.io/badge/%E2%9A%A1_100%25_%E9%9D%99%E6%80%81-%E9%9B%B6%E6%9C%8D%E5%8A%A1%E5%99%A8-b98ae6?style=for-the-badge" alt="100% Static"></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/%F0%9F%A7%8A_Blender-4.5-e08ac0?style=for-the-badge" alt="Blender 4.5"></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/%F0%9F%8C%80_Three.js-GLSL-8a7446?style=for-the-badge" alt="Three.js"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fcards.json&query=%24.cards.length&label=%F0%9F%83%8F%20%E5%8D%A1%E7%89%87&color=c9a86a&style=for-the-badge" alt="Cards (auto)"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_8_%E8%AF%AD%E8%A8%80-7fd4ff?style=for-the-badge" alt="8 Languages"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio/actions"><img src="https://img.shields.io/github/actions/workflow/status/Elijah-Lin-Dancer/Holo-Card-Studio/gallery-check.yml?style=for-the-badge&label=CI%20Passing" alt="CI Passing"></a>
</p>

**中文 · [English](README.md)**

---

## 🚀 在线预览

> ### 🌐 **<https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/>**
> 拖动卡片、翻转、看镭射彩虹随角度流转——无需安装、无需账号、无需服务器。

## ✨ 这是什么？

一条完整的 **AIGC 管线**，把**一句话**变成一张**可交互的 3D 全息收藏卡**：

| 步骤 | 发生了什么 |
|---|---|
| 🧠 **文字模型** | 一句话（自动识别 中文 / Deutsch / English）→ 结构化双语卡面配置 |
| 🎨 **AI 分层素材** | 豆包 Seedream 分层绘制 **4 层** — 主体 · 背景 · 线稿 · 文字层 — 分而治之 |
| 🧊 **3D 场景** | Blender 构建视差 / 镭射彩虹场景，导出 **GLB** |
| 🌀 **实时合成** | Three.js + GLSL 着色器在浏览器实时渲染视差、镭射彩虹、星尘与泛光 |
| 🚀 **发布** | 一条命令 → 纯静态 GitHub Pages（零服务器、零数据库） |

*作品集项目 · AI × 3D 交叉方向 · 原生 JS 前端 · 零框架*

## 🎴 会动的卡片

| 演示 — 马尔科·罗伊斯「黄黑之魂」（edition 007/009，德语卡面） |
|:--|
| ![罗伊斯全息卡演示](docs/screenshots/demo-reus.gif) |

这是 Blender 管线输出的**真实转台渲染**（96 帧），不是效果图。展厅里悬停播放、详情页实时渲染 WebGL 场景。

## 🗂️ 完整收藏

![HoloLab 卡片墙](docs/screenshots/card-wall.jpg)

**26 张卡 · 8 种语言 · 每张卡都是一个永久链接**，任何人都能打开、分享：

- 🇦🇷 **梅西系列**（5 张）— 最初的《梅西称王》+ 巴萨 · PSG · 迈阿密国际 · 2022 世界杯
- 💙❤️ **巴萨传承系列**（6 张）— 克鲁伊夫《建筑大师》· 瓜迪奥拉《Tiki-Taka》· 梅西 ×4 时代（西语卡面）
- 🎤 **流行之王** — 迈克尔·杰克逊（英语）
- 🖤💛 **马尔科·罗伊斯**（3 张）— 多特《黄黑之魂》· 德国队《未竟之约》· 洛杉矶银河《银河新章》（德语卡面）
- 🎨 **弗里达·卡罗** — 墨西哥画家（西语点缀）
- 🎬 **萨蒂亚吉特·雷伊** — 孟加拉电影大师（孟加拉语卡面）
- 🐎 **Neeltje** — 丹麦卡伦堡的一匹弗里斯兰母马（丹麦语卡面，**🔒 密码锁定**）
- 🐋 **蓝鲸** — 第一张社区投稿卡（自动渲染管线）
- 🤖 **哈兰德多重宇宙**（15 张）— 梗卡：进球机器 · 打坐冥想 · 魔人布欧 · 迪斯科神曲 · 维京战士 · 大葱塑 · 吃重庆轻轨 · 偷喝门将水 · 鲨鱼笑 · Tom猫（英/中/挪语卡面）
- 📚 **岸本健二** —《破碎的我》人气角色（英语卡面）
- 🚋 **Elétrico 28** — 致敬里斯本黄色电车（葡萄牙语卡面）
- 🦘🐱 **Pouch Invader** — Lay 的社区投稿卡「The Laytenant」（英语卡面）
- 🚀 **星辰远征** · 🐵 **齐天大圣** · 🐆 **雪原极光** — 一句话管线出卡

每张卡都能翻转：**结构化卡背**——生涯数据 · 荣誉 · 引语，用卡片自己的语言书写。

## 💡 为什么值得你看

这不是"调一个图像模型出一张图"——它是一条把生成模型变成**可玩产品**的完整工程链：

| 能力 | 仓库里的证据 |
|---|---|
| 🤖 **AI 应用** | 豆包 Seedream API 集成；**分而治之**的分层生成（主体 / 背景 / 线稿 / 文字层）；提示词工程；图生图主体保持 |
| 🧊 **3D 图形学** | Blender 程序化场景（视差 UV、镭射彩虹材质节点组）；glTF 导出；Three.js GLSL 片元着色器实时重建材质 |
| ⚙️ **系统工程** | Python 管线（生成 → 校验 → 渲染 → 导出 → 发布）；静态站点生成；一条命令发布；CI 就绪布局 |
| 🎨 **产品设计** | 瀑布流展厅、每卡永久 URL、风格筛选、移动端适配、即玩即分享 |

## 🧩 前端展示（最新）

静态页面已升级成**动态交互层**：

- 🏠 **首页** — GSAP ScrollTrigger 滚动视差（scrub），标题金色**流光扫字**（切换语言自动重扫），卡片悬停**光斑跟随** + 全息**镭射扫过**，blur→清晰卡片入场，CTA **磁吸按钮**，双主题星尘 + 极光背景
- 🎥 **自动导览 v2「光影导览」** ✨ 展厅招牌体验：**金色光束**在卡片间**平滑滑行**（GSAP, power2.inOut），聚焦卡**被激活**——标题流光、lenticular 光栅脉动、预览视频自动播放；底部 **HUD** 显示"第 N/总数 · 卡名"；启动时卡片错落**苏醒**、收尾时光束**谢幕**；整片画廊 4.5s 呼吸；跳过锁卡；策展视图与 reduced-motion 下禁用
- 🗓️ **策展时间线视图** — 每张卡都有双语创作手记，展厅可在瀑布流与展览时间线间切换
- 🔒 **密码锁定卡** — 未解锁的卡在展厅保持隐藏，输入正确密码才可查看（仓库只存 SHA-256 哈希，源码无明文）
- 🛠️ **创造工坊** — 与展厅统一的星尘 + 极光背景，输入面板聚焦光晕，预演区浮现动画；一句话 → 详细设计 → 私藏 → 申请公开
- 🃏 **卡片详情页** — 极淡全息光晕 + 卡片浮起入场动画，**双主题**（暗色舞台 / 浅色展柜）跟随首页主题
- 🌓 **双主题 & 全界面双语**（中文 / EN）— 含筛选标签、锁定提示、导览按钮；卡面文字按设计保持原语言
- 📮 **公众投稿** — 社区卡经 GitHub Issue → 自动渲染管线（审核 · 4 层素材 · Blender GLB · preview.webm）→ 上线展厅，署名作者
- ♿ 所有动效尊重 `prefers-reduced-motion`；桌面专属交互按精细指针门控

## ⚙️ 管线一览

```mermaid
flowchart LR
  A["💡 一句话创意"] --> B["🧠 文字模型 → 卡面配置（多语言）"]
  B --> C["🎨 Seedream 分层素材 ×4<br/>主体 · 背景 · 线稿 · 文字层"]
  C --> D["🧊 Blender 视差场景 → GLB"]
  D --> E["🌀 Three.js 实时查看器<br/>（视差 · 镭射彩虹 · 星尘 · 泛光）"]
  E --> F["🚀 发布 → GitHub Pages<br/>100% 静态 · 零服务器"]
  F -. 再来一句话 .-> A
```

## 🏃 快速开始

### 🖥️ 直接逛展厅（无需任何配置）

打开上面的**在线预览**即可。无需账号、无需安装、无需服务器——它是纯静态页面。

### 💻 本地跑展厅

```bash
git clone https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio.git
cd Holo-Card-Studio/gallery
python3 -m http.server 4191
# 打开 http://127.0.0.1:4191
```

### 🎨 一句话造一张卡（本地管线）

**环境要求：** Blender 4.5（便携版自动下载）· Node.js 18+ · Python 3.10+。

**.env**（已 gitignore，切勿提交）：
```bash
ARK_API_KEY=你的_豆包_ark_key
```

1️⃣ **一句话生成卡面配置**（自动识别 中文 / Deutsch / English）：
```bash
python3 generator/scripts/one_shot_card.py "我想要一张凤凰"
python3 generator/scripts/one_shot_card.py "Ich möchte eine Hologramm-Karte von Marco Reus"   # → 德语卡面
```

2️⃣ **分层素材 → Blender 管线 → 发布到展厅：**
```bash
python3 generator/scripts/ai_generate.py --project projects/<slug> --model doubao-seedream-5-0-flash-260915
python3 generator/scripts/run_pipeline.py --project projects/<slug>
python3 generator/scripts/publish_card.py --project projects/<slug> --tags "主题,标签"
```

3️⃣ **推送上线** — GitHub Actions 自动部署 Pages：
```bash
git add -A && git commit -m "add card <slug>" && git push
```

📷 **参考照做卡**（宠物、朋友、角色）：把照片放到 `generator/projects/<slug>/ref.png`，管线直接参考生成。

🎛️ **模型选型（已锁定）：** 图片 `doubao-seedream-5-0-flash-260915` · 文字 `doubao-seed-2-0-mini-260428` · 视频 `doubao-seedance-2-0-fast`（账号尚未开通）。

## 📁 仓库结构

```
Holo-Card-Studio/
├── gallery/                  # 纯静态站点（线上部署的就是它）
│   ├── index.html            # 展厅首页 🖼️（瀑布流 + 策展时间线）
│   ├── create.html           # 一句话创造工坊 ✏️（公众投稿入口）
│   ├── cards.json            # 卡片清单（唯一事实源）
│   ├── curation.json         # 双语创作手记（策展时间线，C1）
│   ├── i18n.js               # 中英 UI 词典（含筛选标签与导览）
│   ├── cards/<id>/           # 每卡：app.js · style.css · assets/ · card.glb · preview.webm · lent-L/R
│   └── vendor/               # three.js + GSAP 本地化，零 CDN 依赖
├── generator/
│   ├── projects/<slug>/      # 每卡一个目录：config, work/, web/, renders/
│   ├── tests/                # pytest 套件（20 测试，C2）
│   └── scripts/
│       ├── one_shot_card.py  # 文字模型 → 卡面配置（zh/en/de/es/bn/da/pt/no）
│       ├── ai_generate.py    # Seedream 分层素材 + 抠图 + 线稿
│       ├── run_pipeline.py   # Blender 场景 → GLB → 预览
│       ├── publish_card.py   # 压缩 · 缩略图 · 预览动画 · 登记
│       ├── submit_card.py    # 公众投稿：审核 · 配置 · 全管线
│       ├── inject_og.py      # 每卡 OG 元信息注入（C3）
│       └── verify_gallery.py # 展厅健康检查（CI 使用）
├── .github/workflows/
│   ├── deploy.yml            # Pages 部署
│   ├── gallery-check.yml     # CI：20 pytest + 展厅体检（C2）
│   ├── render-card.yml       # 出卡渲染：分层素材 → Blender → 发布（push 重试 ×3）
│   └── auto-render.yml       # 社区投稿：issue → 审核 → 出卡 → 部署
├── tools/blender-4.5.0/      # 便携版 Blender（gitignored）
├── docs/                     # 架构、AI 管线、图形学、白皮书
└── README.md
```

## 🖼️ 示例卡片

- 🇦🇷 **梅西称王** — 阿根廷十号 · 全息典藏系列
- 🎤 **流行之王** — 迈克尔·杰克逊 · 传奇系列
- 🖤💛 **黄黑之魂** — 马尔科·罗伊斯 · 多特蒙德 · 德语卡面
- 🏆 **未竟之约** — 马尔科·罗伊斯 · 德国国家队 · 2014 世界杯
- 🌌 **银河新章** — 马尔科·罗伊斯 · 洛杉矶银河 · MLS 杯冠军
- 🎨 **弗里达·卡罗** — 墨西哥画家 · 典藏系列
- 🎬 **萨蒂亚吉特·雷伊**（সত্যজিত রায়）— 孟加拉电影大师 · 孟加拉语卡面
- 🐎 **Neeltje**（hun Friese merrie）— 丹麦卡伦堡 · 丹麦语卡面 · 🔒 锁定
- 🐋 **蓝鲸** — 第一张社区投稿卡（自动渲染管线）
- 💙❤️ **巴萨传承系列**（6 张）— 梅西 ×4 时代 · 克鲁伊夫 · 瓜迪奥拉 · 西语卡面
- 🤖 **哈兰德多重宇宙**（15 张）— 魔人布欧撞脸 · 进球机器 2.0 · 打坐 · 迪斯科神曲 · 维京战士 · 大葱塑 · 吃重庆轻轨 · 偷喝门将水 · 鲨鱼笑 · Tom猫（英/中/挪）
- 📚 **岸本健二** —《破碎的我》人气角色 · 英语卡面
- 🚋 **Elétrico 28**（A Vitória de Lisboa）— 里斯本黄色电车 · 葡萄牙语卡面
- 🦘🐱 **Pouch Invader**（THE LAYTENANT）— Lay 社区投稿 · 英语卡面
- 🚀 **星辰远征** — 宇航员 · 一句话管线生成
- 🐵 **齐天大圣** — 孙悟空 · 一句话管线生成
- 🐆 **雪原极光** — 雪豹 · 霜原野生系列

## 🗺️ 路线图

**已完成 ✅**
- [x] Seedream 分层生成 + 抠图 + 线稿提取
- [x] Blender 全息管线 + Three.js 查看器
- [x] 一句话出卡 + 双语展厅 + 多语言卡面（中 · 英 · 德 · 丹 · 孟加拉 · 西 · 葡 · 挪）
- [x] 结构化卡背（生涯数据 · 荣誉 · 引语）
- [x] 前端交互层（视差 · 流光 · 光斑 · 磁吸 · 双主题）
- [x] **访客公开投稿通道** — GitHub Issue → 自动渲染管线 → 上线展厅（全自动）
- [x] **C1 策展时间线** — 双语创作手记、展览视图
- [x] **C2 CI 校验** — 20 pytest + 展厅健康检查，每次推送
- [x] **C3 OG 元信息** — 每卡社交预览注入
- [x] **密码锁定卡** — SHA-256 锁定、展厅内解锁体验
- [x] **自动导览 v2「光影导览」** — 光束滑行 · 卡面激活 · HUD · 开场/收尾编排
- [x] 实时卡数徽章（直读 cards.json，永不落后）
- [x] 渲染工作流加固 — push 重试 ×3 + 自动部署（并发不再丢卡）
- [x] CI i18n 覆盖 — 每个 style tag 必须命中中英词典
- [x] 仓库瘦身（git gc 996M → 124M）

**待办 🚧**
- 持续加卡——展厅是活的成长型作品集；公众投稿管线让任何人的一句话都能成为永久卡片。

## 📚 文档

- [架构设计](docs/architecture.md) — 系统设计与权衡
- [AI 管线](docs/ai-pipeline.md) — 分层生成详解
- [设计决策](docs/DESIGN-DECISIONS.md) — 为什么投稿需要 GitHub 账号 & 成本模型
- [图形学](docs/graphics.md) — Blender 节点与 GLSL 着色器笔记
- [部署](docs/DEPLOYMENT.md) — Pages 与 Actions
- [开发计划](docs/DEVELOPMENT-PLAN.md)
- [工具路线图](docs/TOOLKIT-ROADMAP.md)
- [白皮书](docs/WHITEPAPER.md)

## 🙏 致谢

基于开源项目 [holo-card-studio](https://github.com/EverettFish/holo-card-studio)（MIT）二次开发，保留上游署名。

## 📄 许可

[MIT](LICENSE) — 自由使用、修改与分享。
