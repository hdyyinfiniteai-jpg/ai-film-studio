---
name: film-pipeline-orchestrator
description: >
  AI 电影全片生产编排器。输入已定稿剧本，输出全片提示词包 + HTML 分镜表 + 成本报告。
  以有状态机的单一 skill 编排五个内部模块（故事/表演/资产/分镜/提示词），
  八个阶段、五道门禁，跑不过门禁不许进下一阶段。
  当用户提到以下任何内容时触发：全片提示词生产、AI 电影产线、剧本转分镜表、
  批量生成视频提示词、分镜表 HTML、提示词一致性审计、抽卡成本估算、
  场次计秒、AI 可拍性检查、价值运动转摄影机运动、生成结果回填、失败模式统计。
  即使用户只说"帮我把这个剧本做成全片提示词"、"这部片要花多少算力"、
  "帮我检查这批提示词有没有冲突"、"这场戏该拆几条"、"这个剧本能不能用AI拍"，
  也应立即触发。
  不要用于：剧本创作本身（转 premium-series-creator / film-screenplay-master）、
  单条提示词起草或诊断（转 seedance-director-master / av-prompt-master）、
  角色定人与演员库（转 persona-forge-portrait-master / persona-casting-master）。
---

# film-pipeline-orchestrator

一条命令跑通全片。五套原 skill 降级为内部模块，本 skill 是唯一入口。

## 核心纪律（违反即产线失效）

1. **唯一真相源**：所有状态在 `project.json`。任何阶段都不重读剧本原文。
2. **门禁只判定，不修改**。艺术判断在人手里，工程检查在机器手里。
3. **审计只报不改**。自动改写会引入新的不一致，而且人会停止思考。
4. **随时可中断续跑**。每个 stage 结束即落盘，`status` 可查，`run <stage>` 可重跑。
5. **一致性靠字符串比对，不靠记忆**。人在第 50 条之后就记不住句柄写过什么。

## 状态机

| 阶段 | 名称 | 内部模块 | 出口门禁 |
|---|---|---|---|
| S0 | 立项 · 美学与目标锁定 | aesthetic-templates | — |
| S1 | 故事 · 场次编译 | SCREENWRITER | **G1 结构门 · G2 可拍门** |
| S2 | 选角 · 角色锁与声纹 | ACTING（+ Persona Vault） | — |
| S3 | 资产 · 规格铸造 | LIRA | **G3 资产门** |
| S4 | 分镜 · 走位与情绪轨迹 | SHOTLIST-BUILDER | **G4 走位门** |
| S5 | 提示词 · 生成 | SEEDANCE | **G5 出货门** |
| S6 | 出货 · HTML + 提示词包 + 成本 | — | — |
| S7 | 回填 · 失败学与成本核算 | generation-codex | — |

## 五道门禁

**G1 结构门** — 控制性理念非空 / 每场价值 in→out 非空 / 价值对命中词库 /
片长在目标 ±10% / 极性不平（呼吸场 ≤15%，同极性不连续 4 场以上）

**G2 可拍门** — 七类硬禁令 + 有名角色 ≤3。**剧本层是全链路最便宜的拦截点。**

**G3 资产门** — 每角色有 core_lock 与 voice_prompt / 每地点 ≥2 视图 /
每道具有规格 / 色板 60-30-10 已锁

**G4 走位门** — 多人场次有走位俯视图 / 每场有 emotion_track

**G5 出货门** — 十二项跨提示词一致性审计（句柄漂移 / 服装断裂 / 空间冲突 /
焦距违教条 / 光源违教条 / 镜头数未声明 / 字数超限 / ⚠️密度 /
情绪形容词残留 / 眼神三件套 / 条件式转变 / 道具链）

## 用法

```bash
cd tools

# 建项目
python3 pipeline.py init --id xingming --title "《刑名》" \
  --type short --runtime 42 --aspect 21:9 \
  --aesthetic cold-court-noir \
  --idea "当自律成为唯一的信仰，它就会变成出卖你的那把刀。"

# 填 scenes[] / cast[] / locations[] / props[]（见 examples/project.json）

python3 pipeline.py all              # 一路跑到底，遇门禁停机
python3 pipeline.py status           # 当前阶段与门禁状态
python3 pipeline.py run S1           # 重跑某阶段
python3 pipeline.py gate G5          # 单跑某道门
python3 pipeline.py log sc14-p1 fail hand_chaos    # 回填生成结果
python3 pipeline.py run S7           # 看失败模式分布与 E[尝试次数]
```

退出码：`0` 通过，`2` 门禁未过。可直接接 CI。

## 阶段输入要求

**S1 之前必须有的**：`project.controlling_idea`（一句话）。**没有它拒绝执行** ——
无法判定价值运动，整条链断在起点。

**scenes[] 每场必填**：`no / slug / value_in / value_out / focal_character /
cast_present / location_id / beats[]`

`beats[]` 是计秒输入：
```json
{"type":"dialogue","text":"册子是你取的？","mode":"normal|period|argument|monologue|comedy"}
{"type":"action","text":"沈砚整了整袖口。","lines":1}
{"type":"silence|beat_pause|comedy_hold|entrance_exit|transition"}
```

## 本 skill 不做什么

- **不写剧本**。它只编译已定稿的剧本，一个字的台词都不写。
- **不定人**。角色本体转 persona-forge；本 skill 只做"本片需要什么规格"的翻译。
- **不替你做审美决定**。`mapping_override` 永远开着，反用映射只要求你写一句理由。
- **不自动改写提示词**。审计给修补句，粘不粘由你定。

## 边界与已知限制

- S5 输出的是**工程正确的骨架**：镜头声明、句柄自声明、焦距、摄影机节拍、
  风格与禁令块全部保证正确。**微表演层是留空的**（`【微表演】〈待填〉`），
  这是有意的 —— 台词级的肌肉动作需要读具体台词，属于创作而非编译。
  用 `scene.micro_beats = {"1": "...", "2": "..."}` 填入，或交 ACTING 模块处理。
- 成本模型在 `generation_log` 样本 <20 时用基线 3.0；≥20 自动切实测值。
  **样本不足时的美元数字是量级参考，不是预算依据。**
- 门禁阈值在 `config/gates.json`。它们目前是建议值，
  **跑满三个月后应当用 S7 的实测分布覆盖**。

## 文件

```
config/   aesthetic-templates · value-camera-map · value-taxonomy · gates · cost-model · zh-timing
schema/   project.schema.json
tools/    pipeline(状态机) · timing · shootability · emotion · density · promptbuild · audit · gates · cost · html_build
reference/ 五个内部模块的压缩规则 + 失败模式库
examples/ 《刑名》三场完整可跑样例
```
