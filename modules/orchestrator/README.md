# film-pipeline-orchestrator · 快速上手

```bash
cd tools
python3 pipeline.py init --id demo --title "《片名》" --type short \
  --runtime 42 --aspect 21:9 --aesthetic cold-court-noir \
  --idea "一句话控制性理念"
# 编辑 project.json 填 scenes[] / cast[] / locations[] / props[]
python3 pipeline.py all
```

产物在 `out/`：`Shotlist.html`（可筛选/可复制/可打印）、
`prompts/*.txt`（每条独立，便于批量投喂）、`cost_report.json`。

跑一遍完整样例：
```bash
cd examples && python3 ../tools/pipeline.py all
```

## 三个最容易踩的坑

1. **没填 controlling_idea** → S1 直接拒绝执行。这不是 bug，
   没有控制性理念就无法判定价值运动，整条链断在起点。
2. **价值对自造词** → G1 的 `value_in_taxonomy` 拦截。
   只能从 `config/value-taxonomy.json` 选，或加入词库（要写理由）。
3. **门禁阈值当真理** → `config/gates.json` 里的数字目前是建议值。
   跑满三个月，用 `pipeline.py run S7` 的实测分布覆盖它们。

## 关于 S5 输出的边界

提示词骨架的**工程部分全部保证正确**：镜头数声明、句柄自声明、焦距合教条、
摄影机节拍绑编号、风格与禁令块去重完整。

**微表演层留空**（`【微表演】〈待填〉`）。这是有意的 ——
台词级的肌肉动作需要读具体台词，属于创作不属于编译。
填入方式：`scene.micro_beats = {"1": "...", "2": "..."}`。
