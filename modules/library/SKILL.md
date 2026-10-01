---
name: studio-library
description: >
  AI 影视资产库与复利引擎。不先做流程，先做可复用资产的复利——
  把五套 skill 的产物拆成跨项目复用的原子件，做一个越用越快的库。
  五个库：演员库 personas、场景库 locations、道具库 props、
  微节拍句库 beats（中文，按情绪×强度×体位×景别×类型索引）、
  失败档案 codex（唯一零边际成本、跨全部项目通用的库）。
  覆盖：入库与撞库自动合并、检索 DSL、新片借出预填、库健康三指标、
  覆盖度热力找空洞、复利报表（复用率与第N部片边际成本）。
  当用户提到以下任何内容时触发：资产复用、演员库、场景库、微表演句库、
  失败模式统计、防御句 ROI、这个角色以前用过吗、能不能复用、
  新片开局预填、库健康、第N部片能省多少、抽卡失败记录。
  即使用户只说"这个人物我之前做过"、"帮我找一段压抑的古装表演描述"、
  "又崩了记一下"、"我下部片能省多少"，也应立即触发。
  与 film-pipeline-orchestrator / director-console 共享 project.json。
  不要用于：角色从零定人（转 persona-forge-portrait-master）、
  单片生产（转 orchestrator）。
---

# studio-library · 资产复利引擎

方向 A 优化单个项目。方向 B 优化决策质量。
**方向 C 优化的是第 N 个项目。**

Hell Grind 用两周 $50 万拍了 95 分钟。但如果他们拍第二部同世界观的片，
成本不会是 $50 万 —— 因为角色、场景、美学、失败模式知识全都能复用。

## 五个库

| 库 | 内容 | 边际成本 | 通用性 |
|---|---|---|---|
| `personas` | 演员本体：Soul ID / core_lock / 声纹卡 / 状态变体 / 一致性契约 | 高 | 同世界观 |
| `locations` | 场景：主视图+反打+细节 / 光线档案 / 色板 | 中 | 同题材 |
| `props` | 道具：句柄描述 / 规格 | 低 | 同题材 |
| `beats` | 中文微表演句库，五维索引 | 低 | **全类型通用** |
| `codex` | 失败模式 + 防御句 + 实测 ROI | **零** | **全项目通用** |

**先建 codex。** 它是唯一一个零边际成本、跨全部项目通用的库 ——
今天开始记，下个月就省钱。

## 复利如何产生

实测（本包 examples 可复现）：

```
 # 项目          资产  复用   复用率   资产成本   vs首片
 1 xingming       4    0      0%      59.2     1.0x
 2 xingming2      5    3     60%      32.8    0.55x
```

第 2 部片复用率 60%，资产成本降到首片的 55%。
估计曲线 `{1:1.00, 2:0.65, 3:0.45, 5:0.35, 10:0.30}` —— 实测会覆盖它。

## 三条纪律

1. **只入库去项目化的部分。** 角色本体入库；本片的场次归属、服装状态、
   走位图不入库 —— 那些是项目数据不是资产。
2. **撞库自动合并，不新建。** 句柄描述文本相似度 ≥0.88 视为同一资产。
   否则库会长出三个"沈砚"，一致性从根上就废了。
3. **库不维护会腐烂。** `health` 每月跑一次：完备度 / 撞库 / 陈旧度 / 覆盖度空洞。

## 用法

```bash
cd tools
python3 vault.py ingest ../examples/xingming.json        # 一部片跑完就入库
python3 vault.py find persona "瘦高"                      # 检索
python3 vault.py beat "emotion=隐忍,genre=古装"           # 微节拍句库
python3 vault.py beat "emotion=尴尬" --ensemble           # 群戏错开建议
python3 vault.py checkout ../new.json --id p2 --title "《续》" \
    --aesthetic cold-court-noir --persona PV-0142 --location LV-0001
python3 vault.py codex log hand_chaos --project p2       # 抽卡失败记一行
python3 vault.py codex stats                             # 失败分布 + 防御句 ROI
python3 vault.py health                                  # 库健康 + 覆盖度热力
python3 vault.py compound                                # 复利报表
```

## 检索 DSL

```
key=value,key=value    结构化过滤
自由词                  全字段子串匹配
混合                    emotion=压抑,intensity=3,古装
```

微节拍五维：`emotion · intensity(1-3) · posture · speaking · shot · genre`

## 与 persona-forge / persona-casting 的关系

**personas 库就是你的 Persona Vault。** 本 skill 不定人 ——
遇到库中没有的角色，转 `persona-forge-portrait-master` 定人，
完成后 `ingest` 回库。

对齐只需两个字段：`core_lock`（50–70 词英文，每条提示词都带）
和 `voice_prompt`（逐字锁定不改）。

## 微节拍句库：原五套 skill 完全没有的东西

ACTING 的 MICRO_BEATS 是一份**目录**，不可检索，且是英文。
本库改造为五维索引的中文成品句，可直接粘贴。

**种子库 51 条，其中古装 8 条、喜剧 6 条** —— 原库这两个类型是零。
`health` 会自动报告哪些类型偏薄。

写作纪律（写新句时必须遵守）：
- 只写可观测肌肉动作，禁一切情绪形容词
- 状态而非过渡，禁「逐渐」
- 身体与台词矛盾时标 `contradiction=true`
- 群戏调用必须错开：同情绪不同强度，或同强度不同延迟

## 已知限制

- **短期见效最慢。** 第一部片不会更快，只会更慢（要额外做入库）。
  复利从第二部开始。
- 撞库阈值 0.88 是拍脑袋的。同一世界观里两个刻意相似的角色会误合并 ——
  `health` 会报出来，人工确认。
- `codex` 的失败率数字目前全是估计。样本 <15 时界面标「样本不足」。
