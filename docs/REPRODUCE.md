# 一键复现指南 · Reproduce HoloLab in Five Minutes

> 目标：任何人 clone 这个仓库后，不用读代码，按下面步骤就能
> **跑起展厅 → 用一句话造一张卡 → 通过全部测试 → 发布**。
> 这是一份"工程素养"文档：可复现 = 可信。

## 0. 环境要求

| 依赖 | 版本 |
|---|---|
| Python | 3.10+ |
| Node.js | 18+（仅卡片 web 模板需要） |
| Blender | 4.5（管线首次渲染时自动下载便携版，也可预置到 `tools/`） |

不需要数据库、不需要服务器、不需要外部服务（除生成卡时的 AI API key）。

---

## 1. 克隆与安装

```bash
git clone https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio.git
cd Holo-Card-Studio
make setup        # pip install + 生成 .env 模板
```

`make setup` 会创建 `.env`。要**出卡**需要填 `ARK_API_KEY`（AI 生图用）；
只**浏览展厅**则不需要任何 key。

---

## 2. 本地浏览展厅（零配置）

```bash
make preview
# 打开 http://127.0.0.1:4191
```

80 张卡、双主题、中英双语、自动导览，全部离线可看。

---

## 3. 一句话造一张卡（完整管线）

```bash
make new SENTENCE="给中国航天员设计一张全息收藏卡"
# 输出一个 slug，比如 card-zhongguo-hangtianyuan

make render SLUG=card-zhongguo-hangtianyuan
# 四层 AI 生图 → 抠图 → 文字层 → Blender 合成 GLB → 压缩
```

也可以一步到位：

```bash
make card SENTENCE="给中国航天员设计一张全息收藏卡" SLUG=card-zhongguo-hangtianyuan
```

管线特性（详见 `docs/ai-pipeline.md`）：

- **失败恢复**：某一层生图失败只重跑那一层，已成功层自动复用；
- **幂等**：同一个 slug 重跑不会损坏状态；
- **本地复用**：素材齐全时纯本地合成，不消耗 API。

---

## 4. 跑全部测试（与 CI 完全一致）

```bash
make test        # 28 项 pytest（config schema / manifest / i18n / importmap / 缩略图 / 资产 / prompt / preflight）
make check       # 出卡前预检（字段完整、四层素材、缓存）
```

每次 `git push` 时 GitHub Actions 会自动跑同样的 `gallery-check`，
外加 80 卡全量资产校验——本地过、线上必过。

---

## 5. 发布到展厅

```bash
make publish SLUG=card-zhongguo-hangtianyuan
git add -A && git commit -m "add card card-zhongguo-hangtianyuan" && git push
```

GitHub Actions 自动部署，几分钟后卡出现在线上展厅。

---

## 6. 用参考照片出卡（宠物/朋友/角色）

把照片放到 `generator/projects/<slug>/ref.png`，管线自动以它为参照生成。
（这是"隐藏解锁卡"等个性化卡的制作路径。）

---

## 常见问题

| 现象 | 原因与解决 |
|---|---|
| `make render` 很慢 | 首次渲染要下载 Blender 便携版（SHA-256 校验）；之后走缓存 |
| 抠图阶段重复下载模型 | u2net 缓存被清，属正常；预检脚本会提示 |
| 生图报 key 错误 | 检查 `.env` 的 `ARK_API_KEY`；只浏览展厅可跳过 render |
| 标签没翻译 | 新 `style_tags` 必须在 `gallery/i18n.js` 有中英词条，否则 CI 拦截（这是特性） |

---

## 质量门禁（每个出卡人必读）

出卡前必须过五道闸：**四肢完整 → 背景不同色系 → 抠图透明通道自检 →
正视角可辨（不转也认得）→ 批量不豁免**。完整规范见
[`docs/CARD-QUALITY.md`](CARD-QUALITY.md)。缺肢体、隐形主体是缺陷，不是特色。

---

*本仓库是在 MIT 上游 [holo-card-studio](https://github.com/EverettFish/holo-card-studio)
基础上二次开发的独立作品，传承关系见 [WHITEPAPER.md](WHITEPAPER.md) 第二章。*
