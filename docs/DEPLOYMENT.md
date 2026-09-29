# 部署到 GitHub Pages（免费公开上线）

HoloLab Studio 的展厅是**纯静态站点**（无后端、无数据库），可以直接用 GitHub
Pages 免费托管，任何人打开链接就能浏览和玩卡。

> 生成流水线（豆包 API + Blender）留在本地执行；线上只展示生成好的静态资产。

## 前置条件

- 一个 GitHub 账号（免费即可）
- 本地已安装 git，并能向 GitHub 推送（配置好 SSH key 或 HTTPS 凭据）

## 三步上线

### 1. 在 GitHub 新建仓库

- 仓库名建议：`holo-lab`（或你喜欢的名字，比如 `holo-card-gallery`）
- 设为 **Public**（作品集必须公开，招生官/面试官才能打开）
- 不要勾选 "Add a README"（避免初始提交冲突）

### 2. 推送 gallery 到仓库

在本地项目根目录执行：

```bash
cd holo-lab
git init
git add -A
git commit -m "HoloLab Studio: AI 分层生成 × Blender 渲染 × 静态展厅"
git branch -M main
git remote add origin git@github.com:<你的用户名>/holo-lab.git
git push -u origin main
```

> 注意：`.gitignore` 已排除 `.env`（密钥）和 `generator/projects/*/work/`，
> 密钥**不会**被推送到 GitHub，请确认 `git status` 中没有 `.env`。

### 3. 启用 GitHub Pages

网页上操作：

1. 打开仓库 → **Settings** → **Pages**
2. Build and deployment → Source 选 **Deploy from a branch**
3. Branch 选 `main`，目录选 `/ (root)` → Save
4. 等待 1–2 分钟，出现绿色提示后访问：
   `https://<你的用户名>.github.io/holo-lab/`

完成。现在任何人打开上面的链接，就能看到展厅首页，点进卡片拖拽、翻面、
拉镭射滑块。

## 后续每次出新卡

1. 跑流水线生成新卡（见 `README.md` 的「做一张新卡」）
2. 一键发布进 gallery：

```bash
python3 generator/scripts/publish_card.py \
  --project generator/projects/<新卡目录> \
  --id <卡片ID> --tags "风格,题材"
```

3. 推送上线：

```bash
git add -A && git commit -m "publish: 新卡 <卡名>" && git push
```

## 可选：GitHub Actions 自动部署

把 `deploy.yml`（见 `.github/workflows/`）加入仓库后，以后 push 到 main 会自动
构建并部署到 Pages，无需手动操作。

## 排障

| 现象 | 处理 |
|---|---|
| 打开是 404 | 确认 Pages 分支/目录选择正确；等待 1–2 分钟 |
| 卡片页黑屏 | 浏览器需支持 WebGL（手机/电脑默认支持）；确认访问的是 `https` 链接 |
| 图片加载慢 | 当前素材为 1920×2880 原图；后续可加压缩步骤（见 docs 路线图） |
| `.env` 出现在 git status | 停止，检查 `.gitignore`，不要提交 |
