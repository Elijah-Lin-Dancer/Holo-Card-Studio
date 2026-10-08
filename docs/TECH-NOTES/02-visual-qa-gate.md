# 技术笔记 ② · Automated Visual QA for Generative Pipelines: A Zero-API Quality Gate
# Tech Note ② · 从人眼到门禁：生成管线的自动视觉质检

> 主线 ② 收官笔记（B-1 → B-3）· 中英双语
> 设计文档见 `docs/GRAPHICS/HOLO-OPTICS.md` 姊妹篇——本文不推公式，只讲"为什么把关要自动化、阈值怎么校准、误报怎么驯服"。

---

## 1. 为什么要做这个 / Why we did this

每张全息卡有四层素材（主体 / 背景 / 文字 / 线稿），过去靠"人眼五道把关"：四肢完整、清晰度、透明通道、构图、正视角。人工把关有三个讲不出口的问题：

- **没有记录**：看一眼说"过了"，验收标准只在脑子里，无法回看、无法审计；
- **没有回归防线**：素材是 AI 生成的，下一次跑可能悄悄变差，CI 只会查格式和链接，拦不住"腿没了"；
- **人工成本随规模爆炸**：60+ 张卡后，逐张肉眼检查已经不是"顺手的活"。

于是我们建了一条**零 API 消耗**的自动质检门禁：`generator/qa/`。不调任何云端模型，全部用本地视觉算子 + 本地 ONNX 模型，跑在 `run_pipeline` 渲染之前和 GitHub Actions 里。

---

## 2. 四道门 / Four gates

```
G1 主体完整性  —— 人物四肢是否完整、主体掩膜是否连续
G2 清晰度      —— 是否模糊 / 无边缘结构 / 对比度过低
G3 透明通道    —— 抠图残边、半透明噪点是否超标
G4 构图        —— 主体占比是否合理、是否偏离中心
```

| 门 | 检测器 | 依赖 | 为什么选它 |
|---|---|---|---|
| G1 姿态 | MediaPipe Pose 0.10.14 | onnxruntime | 四肢关键点可见性 = 肢体是否存在的直接证据 |
| G1 掩膜 | rembg u2net（本地 ONNX） | ~176MB 模型 | 前景/背景分割后看主体掩膜连续性 |
| G2 | Laplacian 方差 + **Canny 边缘密度** + 直方图跨度 | numpy / opencv / scipy | 三指标互补，见 §4 的"平滑材质"故事 |
| G3 | alpha 半透明占比 + 残边占比 | numpy / scipy | 抠图质量的两条硬证据 |
| G4 | 主体掩膜占比 + 质心偏移 | u2net 掩膜 | 构图的两条硬约束 |

**G1/G4 用 u2net 掩膜，G2/G3 零重型依赖**——这个分工直接决定 CI 形态（见 §6）。

---

## 3. 校准方法：不拍脑袋 / Calibration: numbers over vibes

阈值不是查论文抄的，是**从真实分布 + 破坏样本两端夹出来的**：

1. **真实分布**：对 5 张校准卡（殷商王亥、VC 汤米、袋鼠兜猫、里斯本电车、后母戊鼎）跑初版阈值 → **一致率 0%**：全息卡的发光描边、满幅主体、插画风把"通用阈值"集体误伤；
2. **逐门看分布**：把每个指标的实测值打印出来，看真实卡落在哪、破坏样本落在哪，找"分得开"的线；
3. **破坏样本**：人为制造 4 类坏素材（裁右 40% / 高斯模糊 σ15 / alpha 60%+残边 / 缩 10% 贴角），要求拦截率 100%；
4. **校准循环**：调阈值 → 重跑一致率 + 拦截率 → 直到"真实卡全过、坏素材全拦"。

**最终验收（B-1/B-2）**：

| 项 | 结果 |
|---|---|
| 校准卡一致率 | **100%**（5/5，GROUND_TRUTH 全 True） |
| 破坏样本拦截率 | **100%**（4/4 类全拦） |
| 全项目轻量门（61 个素材目录） | 全通过 |
| 集成门禁端到端（王亥通过 / 破坏素材拦截 / --force 放行） | 全通过 |

---

## 4. 误报管理：驯服"设计特征" / False positives: design features ≠ defects

这是整个 B 系列最值钱的教训——**全息卡的艺术设计会系统性"误伤"通用质检阈值**：

- **发光描边** → 被 G3 判成"半透明噪点"（真实 0.2~0.37，通用阈值 0.20 全误报）；
- **暗黑/夜景氛围** → 直方图跨度低，被 G2 判"对比度不足"；
- **满幅主体、插画风** → G4 占比、G2 Laplacian 集体偏低；
- **半身像** → 下肢关键点缺失是**合法**的（下肢缺失降为 warning，只有上肢缺失才 FAIL G1）。

三件工具驯服误报：

1. **edge_density 兜底模糊**：真模糊（高斯 σ15）的 Canny 边缘密度 = **0.000**；平滑材质（贝币 lap=3.0、玄鸟 lap=8.8）有清晰轮廓 = 0.9~2.1。**边缘密度是"模糊"的真证据，Laplacian 只是"纹理量"**——把 Laplacian 降为 warning，模糊 FAIL 只看边缘密度；
2. **阈值按设计分布校准**：`g3_translucent_noise_max` 0.20 → 0.40（覆盖光效卡真实分布 0.2~0.37，破坏样本 0.498 仍拦）；`g2_histogram_span_min` 60 → 20（夜景卡放行）；
3. **per-card 豁免机制 `qa_overrides`**：极简对比度（小哈瓦那 span=4）这类"设计如此"的卡，在 `card-config.json` 里显式声明豁免——**豁免要留痕，不能静默**。

---

## 5. 踩坑实录（按时间顺序） / War stories (chronological)

- **MediaPipe 1.1.0 移除 legacy `solutions` API**：`pip install mediapipe` 装到 1.1.0 后 `mp.solutions.pose` 直接 AttributeError，降级 **0.10.14** 可用——依赖版本是硬约束；
- **u2net 缓存**：`~/.u2net/u2net.onnx`（~176MB）一旦丢失，G1/G4 全线"未检测到主体"，得重新下载；
- **可见度阈值 0.6 太严**：王亥右肘/右腕可见度 0.5~0.59（手臂与身体正常重叠），0.6 判"上肢缺失"——降到 **0.45** 后校准卡一致率 0% → 100%；
- **破坏样本结构**：质检接口期望 `card_dir/assets/subject.png` 目录结构，单文件样本直接报"缺少素材"——测试也要按生产结构造数据；
- **CI 与本地分工**：G1/G4 的 MediaPipe + u2net 在 CI 上太重（模型下载 + 推理），CI 只跑 G2/G3 轻量门 + 轻量破坏样本，全量门在本地管线跑——**门禁分两层，不是一刀切**。

---

## 6. 集成形态 / Integration: local gate + CI lite gate

```
本地（渲染前，全量门）                 CI（push，轻量门）
run_pipeline --project <card>  →   gallery-check.yml
  ↓                                 ├─ ci_gate.py（61 素材 G2/G3 全扫）
  validate()                       └─ break_tests.py --lite（G2/G3 破坏样本）
  ↓
  QA 门禁（G1-G4，含姿态/掩膜）
  ├─ 通过 → 继续 Blender 渲染
  ├─ 不通过 → 打印原因，中断提示重生成
  │    └─ --force 手动放行（要留痕：QA 报告落盘 qa_reports/<card>.json）
  └─ --skip-qa 调试跳过
```

- `card-config.json` 支持 `qa_series`（default / meme 两组阈值）和 `qa_overrides`（per-card 豁免）；
- 门禁报告含每门 score / issues / detail，全部落盘，**可审计**；
- **零 API 消耗**：全部本地算子 + 本地 ONNX，不碰云端模型，成本为 0。

---

## 7. 工程启示 / What this taught us

- **质检的本质是"区分设计特征与真实缺陷"**：通用阈值抄不得，必须用自己数据集的分布校准；
- **破坏样本是阈值的另一只锚**：只校准真实卡会让阈值无限放宽，破坏样本保证它仍有牙齿；
- **豁免要显式、要留痕**：`qa_overrides` 是白名单机制，任何"设计如此"的放行都写在配置里，可审计、可撤销；
- **门禁要分轻重**：全量门（重依赖）在本地渲染前，轻量门（零重依赖）进 CI——质量防线和 CI 速度不冲突。

---

## 8. 复现 / Reproduce

```bash
# 1) 校准卡一致率（需 MediaPipe 0.10.14 + u2net）
python3 generator/qa/calibrate.py          # 期望：一致率 100%

# 2) 破坏样本拦截率（全量：G1-G4）
python3 generator/qa/break_tests.py        # 期望：拦截率 100%

# 3) 破坏样本（CI 轻量版：仅 G2/G3）
python3 generator/qa/break_tests.py --lite

# 4) 全项目轻量门
python3 generator/qa/ci_gate.py            # 期望：全通过（61 素材目录）

# 5) 单卡全量门
python3 generator/qa/quality_gate.py generator/projects/shang-wang-hai

# 6) 管线门禁（渲染前自动触发；--force 放行 / --skip-qa 跳过）
python3 generator/scripts/run_pipeline.py --project generator/projects/shang-wang-hai
```

---

## English version / English

**Title:** From Human Eyes to a Gate: Automated Visual QA for Generative Pipelines

**Why:** every holographic card has four layered assets (subject / background / text / lineart). Human visual review scales poorly past 60+ cards, leaves no audit trail, and gives CI no regression defense. We built a zero-API quality gate — `generator/qa/` — that runs on local vision operators and a local ONNX model (u2net), both before Blender rendering and inside GitHub Actions.

**The four gates (G1–G4):**
- G1 subject completeness — MediaPipe Pose 0.10.14 (limb keypoint visibility) + u2net mask continuity;
- G2 sharpness — Laplacian variance + **Canny edge density** + histogram span;
- G3 alpha quality — translucent-ratio + leftover-edge ratio;
- G4 composition — subject mask ratio + centroid offset.

**Calibration, not vibes:** we clamp thresholds between the real distribution (5 calibration cards → 100% consistency) and break samples (4 sabotage classes → 100% interception). The whole pipeline is validated end-to-end: Wang Hai passes, a blurred subject is blocked, `--force` releases.

**The false-positive story is the most valuable part:** holographic art design systematically trips generic thresholds — glowing outlines look like translucent noise (real 0.2–0.37), night scenes have low histogram span, half-body portraits legitimately lack lower-limb keypoints (downgraded to warning; only missing upper limbs FAIL G1). We fix this with (1) edge-density as the true blur signal (real blur = 0.000, smooth materials like cowrie shell lap=3.0 still have edges 0.9+), (2) thresholds calibrated to our own distributions (G3 0.20→0.40 still blocks the 0.498 sabotage; G2 span 60→20), and (3) an explicit per-card exemption mechanism `qa_overrides` — waivers must be on the record, never silent.

**Integration:** local `run_pipeline` runs the full gate before rendering (block with reasons, `--force` manual release writes a QA report, `--skip-qa` for debugging); CI `gallery-check.yml` runs the zero-heavy-dependency lite gate (`ci_gate.py` full scan + `break_tests.py --lite`). Zero API cost — local operators only.
