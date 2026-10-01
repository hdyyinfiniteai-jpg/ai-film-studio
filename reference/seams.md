# 三条焊缝的技术细节

> 融合不是把三个 CLI 包一层。真正的工作在这三个接合点上。

## 焊缝 1 · 参数总线

**方向严格单向：C → A/B。**

```
C library/codex/events.jsonl  ─┬─→ A config/cost-model.json  (baseline_attempts)
各片 generation_log           ─┘   B config/risk-table.json  (mult + n)
```

**为什么必须单向**：如果 A 的成本模型能写回 C，就会出现「用估计值算出的成本
被当作实测数据入库」，几轮之后库里全是自己生成的噪音。库只接受生成结果，
不接受任何推算值。

**阈值**
| 参数 | 门槛 | 不达标时 |
|---|---|---|
| E[尝试次数] | 通过样本 ≥20 | 保持基线 3.0，界面标「估计」 |
| 风险系数 mult | 单模式 n ≥15 | 保持初始值，界面标「拍脑袋」 |

实测系数公式：`mult = 1.0 + (该模式占比 × 1.2)`。
占比越高的失败模式越贵 —— 因为它更可能在本条里发生。

## 焊缝 2 · 微表演接合

**状态词映射**：A 的 `emotion_track[].state`（从价值极性推导，如「平稳/失控/冻结」）
不是 C 句库的索引维度（「愤怒/压抑/震惊」）。`enrich.STATE2EMO` 做转换。

**区段对齐**：一条提示词可能覆盖多个节拍。必须与 `promptbuild` 的切片逻辑一致：

```python
per = max(1, len(track) // n_prompts)
seg = track[idx*per:(idx+1)*per]
if idx == n_prompts-1: seg = track[idx*per:]   # 末条吃掉余数
b = seg[-1]     # 取落点状态
```

**取落点而非起点**：微表演描述人物最终停在哪里，不是从哪里出发。
第3场「囚禁→自由」若取起点会拿到「恐惧」，取落点才是「释然」。

**类型硬护栏**：
```python
pool = [b for b in beats if b["genre"] in (target, "通用")] or beats
```
喜剧节拍落进古装戏是灾难，评分再高也不许。护栏优先于评分。

**决策叠加**：只在该条覆盖到 `mask_crack_beat` 时才加裂开标记与延迟指令。
每条都贴等于没贴。

## 焊缝 3 · 状态所有权

同一份 `project.json`，三方各写各的字段，互不覆盖：

| 字段 | 所有者 | 谁读 |
|---|---|---|
| `cast/locations/props/aesthetic` | C | A、B |
| `scenes[].beats/timing_sec/emotion_track` | A | B、bus |
| `scenes[].ai_shootability/value_polarity` | A | B |
| `scenes[].focal_character` | **B 覆写 A 的初值** | A |
| `scenes[].mask_crack_beat/perf_direction` | B | bus |
| `scenes[].mapping_override` | B | A |
| `planned_prompt_count` | A 算，B 可改 | A |
| `prompts[]` | A | bus、C |
| `prompts[].beat_refs` | bus | C |
| `prompts[].generation_log` | 人工回填 | C、bus |
| `director_policy` | B | — |
| `_checkout` | C | 看板 |

**唯一的写冲突是 `focal_character`** —— A 从剧本推一个初值，B 的
`STORY_VALUE_OWNER` 卡可以改。B 后跑，B 赢。这是有意的：
「摄影机跟谁」是导演决定，不是编译器决定。
