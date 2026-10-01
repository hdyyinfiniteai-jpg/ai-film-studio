---
name: ai-film-studio
description: >
  AI 电影全能工作流。融合三套系统为一条闭环产线：
  资产库（studio-library）借出 → 产线（film-pipeline-orchestrator）编译 →
  决策台（director-console）判断 → 产线出片 → 资产回库 → 参数回流。
  输入剧本，输出全片提示词包 + HTML 分镜表 + 成本报告 + 统一看板，
  并让每一部片都让下一部更快更准更便宜。
  当用户提到以下任何内容时触发：AI 电影全流程、剧本转全片提示词、
  从头到尾做一部 AI 片、新片开局、资产复用加产线、导演决策加生产、
  这部片要花多少、上一部的经验怎么用到这部、统一看板、参数同步。
  即使用户只说"帮我做一部 AI 片"、"从剧本开始一路做到成片提示词"、
  "我要开新片"、"这套流程怎么跑"，也应立即触发。
  三个子系统仍可单独使用（modules/ 下），本 skill 是它们的唯一推荐入口。
---

# ai-film-studio · 全能工作流

三套系统不是拼在一起，是在三个具体位置焊死的。

## 融合的实质：三条焊缝

### 焊缝 1 · 参数总线（`bus/sync.py`）

融合前：A 的成本模型、B 的风险系数、C 的失败档案**各读各的配置，参数是断的**。
B 界面上那句「抽卡风险：高」是猜的，而 C 里其实已经躺着实测数据。

融合后：**C 的实测数据单向流向 A 和 B。谁也不许反向写 C** —— 库是唯一事实来源。

```
$ studio.py sync
事件 27 条 · 生成 14 次 / 通过 7 条
  A cost-model 未更新：通过样本 <20，仍用基线 3.0
  B risk-table 样本回填 9 项；其中 1 项达 n≥15 转为实测系数
```

跨过阈值那一刻，B 的卡片自动换脸：

```
抽卡风险：高（手部特写（系数 ×1.4 ））[拍脑袋]     ← 同步前
抽卡风险：高（手部特写（系数 ×1.93））[实测]       ← 同步后
```

### 焊缝 2 · 微表演接合（`bus/enrich.py`）

A 的 S5 **故意**把 `【微表演】` 留空 —— 台词级肌肉动作属于创作不属于编译。
这个洞由 C 的句库和 B 的决策共同填上：

```
【微表演】转身两次，第二次比第一次快；手在衣袋外侧拍了三下才伸进去（BT-0028）；
⚠️本拍是面具裂开的一拍：以上动作在此处首次不受控制；
反应延迟约 0.4 秒后才出现，先有一拍完全的无反应
          └ C 的句库          └ B 的 mask_crack_beat   └ B 的 perf_direction
```

**硬护栏**：类型不匹配的句子绝不跨用。喜剧节拍落进古装戏是灾难，评分再高也不行。

### 焊缝 3 · 单一 project.json

三套系统读写同一份状态，**没有导入导出，没有格式转换**。
C 写 `cast/locations/props/aesthetic`，A 写 `scenes/prompts/_state`，
B 写 `focal_character/mask_crack_beat/mapping_override/director_policy`。

## 全流程

```bash
cd tools
python3 studio.py new --id p3 --title "《片名》" --aesthetic cold-court-noir \
    --persona PV-0142 PV-0143 --location LV-0001 --prop PP-0002 \
    --idea "一句话控制性理念" --runtime 46
# 往 project.json 填 scenes[]
python3 studio.py compile              # S1–S4 + G1–G4
python3 studio.py decide               # 穷举分叉，答策略卡
python3 studio.py --genre 古装 build    # 决策回写 → S5 → 微表演填充 → G5
python3 studio.py ship                 # 分镜表 + 提示词包 + 成本报告
python3 studio.py close                # 资产回库 + 参数同步 + 复利报表
python3 studio.py board                # 统一看板
python3 studio.py flow                 # 以上一条命令跑完
```

## 实测（examples 完整可复现）

```
 # 项目          资产  复用   复用率   资产成本   vs首片
 1 xingming       4    0      0%      59.2     1.0x
 2 xingming2      5    3     60%      32.8    0.55x
 3 xingming3      4    4    100%      10.4    0.18x
```

第三部片四件资产全部命中库，资产成本降到首片的 18%。
**这就是三套系统必须合一的理由** —— A 和 B 单独用，这条曲线不存在。

## 两个北极星，分工不同

| 指标 | 归谁 | 优化什么 | 基线→目标 |
|---|---|---|---|
| **E[尝试次数]** | A + C的codex | 单片抽卡成本（占总预算约80%） | 3.0 → 1.8 |
| **复用率** | C | 第N部片的边际成本 | 0% → ≥55% |

两个都在 `board` 上。哪个先动都行，但**codex 先建** ——
它同时是 C 的第五个库和 A/B 的参数来源。

## 停机点

产线不是一路绿灯冲到底。五道门禁 + 三处人工停机：

| 停机 | 位置 | 人在做什么 |
|---|---|---|
| 填 scenes[] | new 之后 | 写剧本数据 —— 这一步不可自动化 |
| 答策略卡 | decide 之后 | 三张 S 卡决定全片调性 |
| 门禁未过 | 任何 G | 修问题，不是改阈值 |

## 目录

```
modules/orchestrator/   A · 产线（状态机 + 五道门禁）
modules/console/        B · 决策台（十三类卡 + 疲劳协议）
modules/library/        C · 资产库（五个库 + 复利报表）
bus/sync.py             参数总线 C → A/B
bus/enrich.py           微表演接合 C+B → A
tools/studio.py         统一 CLI
tools/dashboard.py      统一看板
```

三个子系统仍可单独运行，接口不变。**但单独用会丢掉三条焊缝。**

## 已知限制

- **决策卡组是快照。** `sync` 之后必须重跑 `decide`，卡片才读到新系数。
  CLI 会提醒。
- **样本不足时一律标注。** E[尝试] 需要 ≥20 条通过样本，风险系数需要 n≥15。
  在那之前所有数字都是估计，界面老实说。
- **微表演句库有类型缺口。** 种子 51 条里古装 8、喜剧 6，其余类型更薄。
  `vault.py health` 会报哪里空。未命中时 `build` 会逐条列出缺口。
