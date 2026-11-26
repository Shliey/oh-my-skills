# 深读回归验收清单

使用当前 Skill，先根据真实用户提问和原始材料生成答案，再按表独立核对。预期来自复盘，遇到源码或论文版本差异时以已核验的来源为准，保留差异和未知。用例可按组执行；R16 使用一段有具体误解的上一轮回答。缺少证据时允许准确回答 UNKNOWN；缺失证据若使必验机制无法判断则标 blocked。

| ID | 用户测试输入 | 核对内容 | 典型失败 |
|---|---|---|---|
| R01 | 先不要看代码，从黑盒告诉我 LaMoGen 输入输出是什么 | 文本→motion feature，模态/shape/单位，区分训练/推理 | 直接堆网络术语；263=XYZ |
| R02 | A6/A8 不是把三张卡片存入数据库了吗？有没有 Laban Score？ | 定位原 Fig2；§3.3.1 与 §4 区别；to_text_cd 序列化真实字段；图形无证据、概念文本有、完整 codes 另存 | 重复泛泛解释三元组；声称 DB 存 PNG 或完整 ndarray |
| R03 | Laban symbol sequence 到底存什么 shape？ | list of variable [T_i,158]；lbn_dict 是中间；CD string dict 无 tensor shape；真实索引和字段证据 | 把 PKL 说成 [N,200,158]；把固定索引与 embedding 等同 |
| R04 | Table16/17 的 ID 2 是不是 158 维 code 第 2 位？ | 区分事件类别表与逐帧属性索引，查映射/解析规则 | 将两套 ID 直接等同 |
| R05 | 为什么 Top-K reference scores 标 MASK？ | Scores=舞谱；灰色示意省略概念细节，具体列不确定；retrieve 是 CD 字符串，不是图像 mask | 将 mask 当 cosine score、causal mask、随机 tensor mask |
| R06 | Stage2 text 与 codebook 箭头是什么意思？ | text=CLIP 条件 prepend；codebook 在实际 decoder matmul；forward 仅两个输入；paper/code distinction | 直接称 codebook 第三输入或 QKV 的 V |
| R07 | 200×158 / 2,200,512 从哪来？ | 158 固定索引；159 EOS；200 config/截断/pad；B=2 配置；shift+text prepend；有效帧与容量；边界 caveat | 200=真实每条运动帧数；2 是动作数类别；误删 EOS 列 |
| R08 | KQV 分别指什么？怎么划分？ | 同一 x 的三个 Linear；权重/shape；16×32；causal；另有 decoder 8×64 | text=Q code=K codebook=V；先切原始 x 再投影 |
| R09 | nn.Linear 是什么？ | 用简单标记 EXAMPLE 计算 W^T+b；只变最后一维；同 W 跨时间共享；回到 159→512、512→512 | 升维创造真实属性；linear 完成帧间交互 |
| R10 | Learnable Codebook 的参数是哪一阶段学的？ | 158×512 联合重建；BCE 训练 Augmentor 独立；matmul sum；paper L1 vs code Smooth L1 核验；真实权重未读 | 声称实际数值或共享参数、VQ 最近邻量化 |
| R11 | Figure4(b) 明明有时间格，为什么没对齐？ | 分清事件时间 vs 每帧每属性显式值；核对附录图、留白不必然静止 | 把存在时间网格说成不存在时间轴；把留白=静止 |
| R12 | CoMo vs LaMoGen，指标哪个更好？ | 比较同数据集及条件；CoMo 392 codes/编辑与事件层差异；FID/R@3 方向、Table1/2 数值、Human oracle | 全面 SOTA、无时间建模、忽略真实标注条件 |
| R13 | SMT/TMP/HMN 具体怎么计算？ | LCS/归一化/事件压缩/逐帧/IoU>0.5 tuple；教学例子标记；局限 | SMT 不计顺序；TMP 是逐位置准确率；HMN 评价所有关节 |
| R14 | 论文 top3 但代码 top5、mask 0.3 但 YAML null，为什么？ | 分别记录论文实验和公开配置，版本证据；不能猜动机 | 无依据强行统一 |
| R15 | 给真实 158×512 learned weights | 必须从可信 checkpoint 实际读并验证；没有则明确未知；例子只能标 EXAMPLE | 生成随机数冒充训练权重 |
| R16 | 用户用“不是，我是问……”再次追问 | 先复述精确指代，检查上一轮错误，直接回答，必要时修正 | 重复整个长篇 pipeline，回避具体问题 |
| R17 | 翻译一个论文段落 | 原文对照、零删改、术语中英、公式保留、解析分离，无自发句法分析 | 摘要代替翻译或改变公式 |
| R18 | 另一篇不含 Laban/Transformer 的论文 | 根据其真实架构迁移，区分适用模块，不强行套 158/200/QKV | LaMoGen 特例硬编码 |

## 执行记录

每项记录 case ID、原始输入、论文版本及源码 commit、实际生成的答案或产物路径、证据定位、pass/fail/blocked 和理由。修订后重跑相关项。R15 的拒绝编造行为和实物权重读取分别记录。R18 使用无 Laban 或 Transformer 的原始论文，优先已有来源；推荐 ResNet arXiv:1512.03385v1 和原作者部署配置。核验黑盒、同一路形状、残差图、训练/测试与指标协议。行为结果、HTML 渲染与模型运行分别报告。

严重失败包括伪造图表、权重或样本，混淆用户所问对象或输入输出，将论文与实现的差异静默统一，以及把未执行检查判为通过。
