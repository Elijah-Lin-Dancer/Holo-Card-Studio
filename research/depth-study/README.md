# 深度信号在生成式分层资产上的可用性边界

本目录是一次实证审计的全部可复现材料。结论本身写在
[`docs/EXPERIMENTS-depth-occlusion-audit.md`](../../docs/EXPERIMENTS-depth-occlusion-audit.md)。

核心问题：卡片由 T2I 生成背景 + 抠图主体 + 单目深度三层拼成，
**深度信号到底能用在决策链的哪一层？**

## 数据文件

| 文件 | 内容 |
|---|---|
| `data/depth_failure_probe.json` | 62 张卡的深度探针指标（纹理假说各代理量、误裁率、纵深跨度） |
| `data/occlusion_ablation.json` | 62 张 × 30 组配置（5 估计器 × 6 阈值）的消融结果 |
| `data/atmosphere_batch.json` | 62 张卡的大气合成景深效果（σ=12 / 30 两档，SR / BVR / far_mean） |

均为文本，可直接阅读。`.csv` 为同源表格版本。

## 脚本

| 脚本 | 作用 |
|---|---|
| `generator/depth/probe_depth_failure.py` | 探针：测纹理代理量、误裁率、纵深跨度之间的关系 |
| `generator/depth/ablate_occlusion.py` | 30 组遮挡判据配置消融，含最小二乘平面残差估计器 |
| `generator/depth/batch_atmosphere.py` | 全库大气合成，测 SR / BVR / far_mean |
| `build_subject_study.py` | 生成 2AFC 主观实验的 16 组刺激与自包含问卷 |
| `analyze_subjective.py` | 收齐被试数据后做评分与统计 |

## 复现

深度推理需要模型权重（不入库）：

```bash
# 1. 把 Depth Anything V2 small 的 int8 ONNX 放到
#    generator/depth/models/model_int8.onnx
#    （约 26MB，配 config.json / preprocessor_config.json）

# 2. 跑三组实验
python3 generator/depth/probe_depth_failure.py --repo . --out research/depth-study/data
python3 generator/depth/ablate_occlusion.py  --repo . --out research/depth-study/data
python3 generator/depth/batch_atmosphere.py  --repo . --out research/depth-study/data

# 3. 生成主观实验材料（需要先有 atmosphere_batch.json）
python3 research/depth-study/build_subject_study.py
```

`build_subject_study.py` 会在本目录下生成 `subject-study/`（刺激图 + 8.9MB 自包含问卷）。
该目录是二进制材料，已加入 `.gitignore`，不随仓库分发。

## 现状

- 三组客观实验已完成，数据在上表三个文件里。
- **主观实验尚未收集任何真实被试数据**，`analyze_subjective.py` 目前无数据可跑。
- 因此「区域锐度比 SR 能否代表感知改善」这一问仍**未确认**，不作结论引用。
