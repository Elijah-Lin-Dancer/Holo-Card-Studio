# 生成式分层资产走向可交互 2.5D：三条脉络与一个很窄的口子

> 调研目的：判断 Holo 全息卡项目能否以「生成式资产的可用性/可组合性评估」立一篇不注水的论文。
> 调研时间：2026-11-09。检索工具：学术检索（5 轮，中英双语）。核验：3 篇读到摘要层，其余为题录层。

## 一、核心结论

**总体判断**：这条路的五个相关方向都已经各自建制，找不到一个"整块空白"。也就是说，把它做成一篇论文的问题，不是"有没有人做"，而是"你剩下的那块地太小，而它又恰好夹在两个成熟社区中间"。真正的结论是：**不要用「可组合性评估」立题**；如果一定要在这个项目上出论文，最有价值的落点不是"评估别人生成的图好不好"，而是"**生成式图像是单目深度模型的分布外输入，它的失效可以不用真值就判出来**"——这条我们手上有实测证据。

1. **组合性生成与语义对齐评估已经成熟**。T2I-CompBench++ 已经做到 8000 条组合提示、四类组合挑战（属性绑定、物体关系、生成计数、复杂组合），并把 3D 空间关系与计数新列进类目，横评 11 个 T2I 模型，还同时用检测式指标与多模态大模型指标两套度量（Huang 等，2023）。再加 GenEval 的对象级对齐框架（Ghosh 等，2023）、ACL 2024 的可解释条件合成度量 VIEScore（Ku 等，2024），以及一篇已发表的 T2I 质量评估综述（Tian 等，2025）。**这类工作不是没人做，是已经卷到做综述的程度。**

2. **带 alpha 的分层资产生成也已有专门工作**。ECCV 2024 的 Alfie 直接做 RGBA 图像生成，NeurIPS 2024 的 RGBA 实例生成把"生成可组合的实例层"当成目标本身（Fontanella 等，2024）。也就是说，"生成一张能抠出来单独用的层"这件事，2024 年就已经被当成独立课题写了。

3. **深度驱动的 2.5D 合成不仅成熟，而且刚好把我们在项目里踩到的坑写进了别人的摘要**。SLIDE 的摘要原话是：以往方法"使用 hard depth layering，因此无法建模薄发丝这类精细外观"，于是提出 soft layering，并配深度感知的补全模块，在三个视图合成数据集上做实验、外加在野图像的用户研究（Jampani 等，2021）。我们在赛里木湖卡上实测到的"分层台阶条纹"，就是它说的 hard layering 缺陷。**这意味着这一模块可以作为工程实现写进系统章节，但不能作为方法贡献。**

4. **深度合成结果的质量评估，在 3DTV/DIBR 社区已经饱和**。NIQSV+ 的思路正是"没有参考视图、没有深度图，就靠合成过程特有的失真——模糊区、空洞、拉伸——来判质量"，并且实验显示它逼近最好的全参考 3D 指标、显著优于通用 2D 指标（Tian 等，2018）。这类无参考度量在 IEEE TIP/TMM 上有一整串（Li 等，2018；Zhou 等，2019）。**"为深度合成结果设计一个新指标"这条路，已经被走完了。**

5. **剩下可能空着的，只有一个很窄的交叉点**：把「生成式分层资产」当成"有生产约束的输入"，用"组装成 2.5D 展示件之后的渲染失真"当判据来评估它。这个位置在检索里没有检出直接对应的工作（属于真空白，不是没搜到）。但它同时被两头夹着——上游是 T2I 评估（管语义对不对），下游是 DIBR 质量评估（管渲染坏没坏）。**审稿人最容易给出的定性就是"既有评估框架在新下游任务上的应用"。**

## 二、研究范围与方法

- 检索轮次：5 轮，覆盖①原始主题词直搜（英）②单目深度 2.5D 合成③合成/抠图/和谐化④下游可用性⑤中文 T2I 评估。
- 语种：英文为主 + 中文一轮。
- 检出文献：13 篇进入清单（其中 3 篇读到摘要层并用于核心论证，其余仅在题录层用于存在性判断）。
- 未直接检索：知网/万方（未接入）；未做引用网络回溯（缺被引数据库入口）。
- 饱和判断：五个子方向各 ≥2 篇有效命中，主题无空类别；新增衰减已明显；**未达五条饱和判据的全部**，如实记为检索局限。

## 三、文献多维地图

| 主题 | 支持文献数 | 代表文献 | 争议 / 反对 | 研究空白 / 后续价值 |
|---|---:|---|---|---|
| A. 组合性生成与语义对齐评估 | 5 篇（含 1 篇综述） | T2I-CompBench++；GenEval；VIEScore | 已建制，无重大方法论冲突；分歧集中在"用检测还是用 MLLM 打分" | 语义层已饱和；**几何/3D 可用性不在其覆盖范围** |
| B. RGBA / 分层资产生成 | 2 篇 | Alfie（ECCV 2024）；RGBA 实例生成（NeurIPS 2024） | 无明显争议 | 生成层已有工作，**但"生成层是否可组装"未被单独立题** |
| C. 单图深度驱动的 2.5D 合成 | 3 篇 | SLIDE；One Shot 3D Photography | hard vs soft layering 已有明确倾向（soft 更优） | 技术已解决；本项目复现其结论，无增量 |
| D. 深度合成视图的质量评估 | 4 篇 | NIQSV+；Li 等（2018）；Zhou 等（2019） | 无原理性冲突，差异在失真建模粒度 | 指标体系成熟；**换一套指标不构成贡献** |
| E. 跨层合成与光照和谐化 | 2 篇 | Multi-scale Image Harmonization（SIGGRAPH 2010）；Chen & Kae（CVPR 2019） | 无 | 经典问题；本项目跨层光照"祈祷对齐"属已知未解项 |

整体分布：**A、D 两块最厚（都已到"有综述/有系列指标"的程度），B、C、E 中等；真正稀疏的是"B×C"之间那道缝——分层资产被组装成 2.5D 之后的可用性，没人以渲染失真为判据系统评估过。**

## 四、研究视角与本文结构

分类轴按**"资产在流水线上的位置"**切，而不是按方法名切：生成（A、B）→ 组装（C、E）→ 判优劣（D）。这样切是因为本项目的核心矛盾就在"生成完之后那一步没人管"，按位置切才能让空格显形。五类互斥且覆盖"一张图从被生成到被展示"的完整链路。

## 五、核心逻辑图

`figures/logic_graph.whiteboard.xml`（Mermaid 白板，节点带文献编号，边带语义标签）。脉络是：生成侧（M1 语义评估 / M2 分层资产生成）指向组装侧（M3 深度 2.5D），组装必然分化出质量评估（M4），和谐化（M5）作为补充；同时 M1 对 M3 构成限定（语义对不代表几何可用），M4 反过来对 M1 构成反驳（渲染失真已有专门度量，语义指标不必越界）。

## 六、主题章节

### （一）语义对齐评估：卷到极致，但只管"对不对"

*本节文献：Huang 等（2023）、Ghosh 等（2023）、Ku 等（2024）、Tian 等（2025）*

这一支的 claim 是：**T2I 评估已经能把"图里有没有这个物体、属性绑没绑对、空间关系对不对"测得很细，但它测的全部是语义层，不测"这张图能不能被拿去做别的事"。** T2I-CompBench++ 把 3D 空间关系都纳入了类目，看起来已经到了几何，但那仍是"图上看起来是不是左边那个在前"，不是"这个层拿去组装会不会塌"。与 VIEScore 的可解释度量相比，两者的分歧不在原理而在打分器：一个用检测器，一个用多模态大模型。这个分歧对本项目无实质意义，因为两者都不回答"可用性"。

> **小结**：语义评估可以直接引用，但不能当作本项目"评估可用性"的替代品——它不覆盖组装阶段。

### （二）分层资产生成：有人做了生成，没人做"生成完能不能用"

*本节文献：Fontanella 等（2024）、Alfie（ECCV 2024，题录）*

claim：**"生成可组合的层"在 2024 年已成为独立课题，但这些工作的验收标准仍是"层长得对"，不是"层装得起来"。** RGBA 实例生成把实例层当作组合场景的原料，Alfie 把 RGBA 生成的门槛降到消费级。两者共同的隐含前提是"层生成出来就能用"。而本项目 82 张真实生产数据给出的反例是：层生成出来之后，还有 alpha 比例不达标、主体与背景锐度倒挂、轮廓与背景结构冲突等一批问题。**这条前提从未被检验，是这个方向最实在的缝。**

> **小结**：这是唯一有希望的位置，但需要把"检验前提"做成真实验，而不是做一套主观评分表。

### （三）深度 2.5D：技术已解决，包括我们踩的那个坑

*本节文献：Jampani 等（2021）、Kopf 等（2020，题录）*

claim：**用单目深度把单图变成可视角移动的 2.5D，是一个已发表、已有用户研究验证的成熟方向；本项目在其中没有方法增量。** SLIDE 的摘要直接点名 hard layering 无法保留细结构，并用 soft layering 修正——这与本项目实测的"K=6 分层台阶"是同一个问题、同一个方向上的结论。差别只在实现细节（它用学习式补全处理遮挡区，我们用规则回退）。**把这一模块写进论文没有问题，但只能写在"系统实现"里，不能写在"方法贡献"里。**

> **小结**：可以作为工程章节，不构成新颖性来源。

### （四）深度合成的质量评估：指标体系已成熟

*本节文献：Tian 等（2018）、Li 等（2018）、Zhou 等（2019）*

claim：**"合成结果坏了"这件事，3DTV 社区早就建立了专门的无参考度量，且明确针对合成过程特有的三类失真。** NIQSV+ 的做法是绕开参考图和深度图，直接测模糊区、空洞、拉伸；这与本项目想做的"用渲染失真判可用性"在方法上是同构的。差别只在数据来源（DIBR 来自真实拍摄的多视点+深度，本项目来自生成资产）。**换数据源不构成新方法**，除非能证明"生成资产的失真分布与 DIBR 失真分布显著不同、导致现有指标系统性失效"——这才是可发表的那一步。

> **小结**：这是本项目最容易被审稿人一句话打死的地方，必须先想清楚"我的失真分布为什么不同"。

### （五）跨层和谐化：经典问题，本项目仍是未解

*本节文献：Sunkavalli 等（2010）、Chen 和 Kae（2019）*

claim：**主体层与背景层的光照不一致，是一个 2010 年就有经典解法、2019 年还在用对抗学习推进的老问题；本项目的现状是"在 prompt 里祈祷对齐"。** 这不是缺陷披露，是方法缺口——但也正因为它是老问题，补上它同样不产生贡献。

> **小结**：属工程欠账，不属论文素材。

## 七、争议与开放问题

**争议一（已消解）**：hard layering 与 soft layering 孰优。SLIDE 给出倾向（soft 更优，理由是细结构保留），本项目实测台阶条纹与之吻合。判定：条件差异，已消解。

**争议二（标记未解）**：评估的对象应是"语义对齐"还是"渲染可用"。两者都成立，但对应不同下游；目前没有工作把两者放在同一套指标下比较。这是真冲突，暂无法判断。

**开放问题一（真空白）**：生成式图像是单目深度模型的分布外输入，其失效模式没有被系统刻画。检索未检出对应工作。本项目已有实证：抽象雷纹背景上，深度模型把高光"脑补"成近景，导致按安装面深度判前景时把主体裁掉一块。

**开放问题二（真空白但载体极小）**：深度线索对"收藏卡"这类小型展示件的感知真实感影响，没有文献。因为载体本身没有文献——这既是机会也是风险（没有社区，就没有审稿人）。

## 八、可研究的方向

**1（优先，AI 味最正）《生成式图像上单目深度的失效可预测性：无真值的失效判据》**
缺口依据：开放问题一。方法思路：以本项目 82 张分层层 + 公开 T2I 数据集为探针，用现成单目深度模型（消费级 ONNX 即可，无需 GPU）批量推理，用"深度图边缘与图像边缘的一致性 + 平面区域的深度方差"作为失效代理指标，与人工标注的失效样本做相关；再验证"失效深度图"是否真的导致下游组装错误（用遮挡误裁率与台阶强度做客观后果指标）。难点：要证明代理指标与后果相关，而不只是与某个人工标签相关。

**2《深度线索对 2.5D 收藏卡感知真实感的影响：一次受控用户研究》**
缺口依据：开放问题二。方法思路：以现有 82 张卡为刺激材料，选 12–16 张做三档处理（现状 / 仅景深 / 景深+空气透视），做 2AFC 偏好 + Likert 真实感评分，N≥30，线上收集；需控制卡片题材熟悉度与观看设备。难点：需要被试，且要写清伦理与设备控制。

**3《分层资产的组装可用性指标：以组装后渲染失真为判据》**（可用于 workshop/demo，不宜作 main-track）
缺口依据：B×C 那道缝。方法思路：定义一组以"组装后可见失真"为判据的指标（台阶强度、主体误裁率、跨层锐度比），在 82 张真实生产卡上做分布统计，并与 NIQSV+ 类指标对照，检验"生成资产失真分布是否与 DIBR 失真分布显著不同"。难点：这正是第四节那个必须先回答的问题。

**4（不推荐）纯管线系统论文**：把整条链写成系统描述。缺方法增量，缺对比基线，属注水。

## 九、局限性

- 核心论证仅建立在 3 篇读到摘要层的文献上；其余 10 篇只在题录层用于存在性判断，未引述其具体方法或数字。
- 未做全文精读，未做引用网络回溯与前向追踪（缺被引数据库入口），因此"真空白"的判定强度有限，属**低置信度空白**。
- 未直接检索中文库（知网、万方）；中文侧可能另有工作未覆盖。
- 五条饱和判据未全部满足即收束，如实记为检索局限。
- 已生成逻辑图与交接包，但**未产出成稿层（连续综述正文）与飞书文档**——因为本次结论可能改变选题方向，为一个可能被放弃的方向写综述，属无效投入。等选题拍板后补。

## 十、参考文献

1. Jampani, V., Chang, H., Sargent, K., et al. SLIDE: Single Image 3D Photography with Soft Layering and Depth-aware Inpainting. arXiv:2109.01068, 2021. https://arxiv.org/abs/2109.01068
2. Huang, K., Sun, K., Xie, E., Li, Z., Liu, X. T2I-CompBench++: An Enhanced and Comprehensive Benchmark for Compositional Text-to-image Generation. NeurIPS 2023 Datasets & Benchmarks. https://arxiv.org/abs/2307.06350
3. Tian, S., Zhang, L., Morin, L., Déforges, O. NIQSV+: A No-Reference Synthesized View Quality Assessment Metric. IEEE Transactions on Image Processing, 2018. https://pubmed.ncbi.nlm.nih.gov/29324418/
4. Ku, M., Jiang, D., Wei, C., Yue, X., Chen, W. VIEScore: Towards Explainable Metrics for Conditional Image Synthesis Evaluation. ACL 2024. https://aclanthology.org/anthology-files/anthology-files/anthology-files/pdf/acl/2024.acl-long.663.pdf
5. Ghosh, D., Hajishirzi, H., Schmidt, L. GenEval: An Object-Focused Framework for Evaluating Text-to-Image Alignment. NeurIPS 2023 Datasets & Benchmarks. https://papers.neurips.cc/paper_files/paper/2023/file/a3bf71c7c63f0c3bcb7ff67c67b1e7b1-Paper-Datasets_and_Benchmarks.pdf
6. Fontanella, A., Tudosiu, P., Yang, Y., Zhang, S., Parisot, S. Generating Compositional Scenes via Text-to-image RGBA Instance Generation. NeurIPS 2024. https://papers.nips.cc/paper_files/paper/2024/file/4d90363e96781894b1327b87d1ade17e-Paper-Conference.pdf
7. Quattrini, F., Pippi, V., Cascianelli, S., Cucchiara, R. Alfie: Democratising RGBA Image Generation With No $$$. ECCV 2024. https://iris.unimore.it/retrieve/handle/11380/1381929/908211/2024_ECCV_Alfie_CR.pdf
8. Kopf, J., Chong, Y., Quigley, O., et al. One Shot 3D Photography. ACM Transactions on Graphics, 2020. https://discovery.researcher.life/article/one-shot-3d-photography/671a38512eee3db9aed3243bdf996b75
9. Li, L., Zhou, Y., Gu, K., Lin, W., Wang, S. Quality Assessment of DIBR-Synthesized Images by Measuring Local Geometric Distortions and Global Sharpness. IEEE Transactions on Multimedia, 2018. https://kegu.netlify.app/PDF/Quality%20assessment%20of%20DIBR-synthesized%20images%20by%20measuring%20local%20geometric%20distortions%20and%20global%20sharpness.pdf
10. Zhou, Y., Li, L., Wang, S., Wu, J., Fang, Y., Gao, X. No-Reference Quality Assessment for View Synthesis Using DoG-based Edge Statistics and Texture Naturalness. IEEE Transactions on Image Processing, 2019. https://ieeexplore.ieee.org/abstract/document/8700605/
11. Sunkavalli, K., Johnson, M. K., Matusik, W., Pfister, H. Multi-scale Image Harmonization. ACM Transactions on Graphics (SIGGRAPH), 2010. https://dl.acm.org/doi/pdf/10.1145/1778765.1778862
12. Chen, B., Kae, A. Toward Realistic Image Compositing with Adversarial Learning. CVPR 2019. https://openaccess.thecvf.com/content_CVPR_2019/papers/Chen_Toward_Realistic_Image_Compositing_With_Adversarial_Learning_CVPR_2019_paper.pdf
13. Tian, Y., Liu, Y., Wang, S., Kwong, S. Quality Assessment for Text-to-Image Generation: A Survey. IEEE Multimedia, 2025. https://scholars.cityu.edu.hk/ws/portalfiles/portal/326543339/273200502.pdf
