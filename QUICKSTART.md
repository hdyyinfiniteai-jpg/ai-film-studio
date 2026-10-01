# ai-film-studio 快速上手

```bash
cd examples
python3 ../tools/studio.py --file project.json compile
python3 ../tools/studio.py --file project.json --deck deck.json decide
python3 ../tools/studio.py --file project.json --deck deck.json --genre 古装 build
python3 ../tools/studio.py --file project.json --out out ship
python3 ../tools/studio.py --file project.json close
python3 ../tools/studio.py --file project.json --deck deck.json board
```

`examples/project.json` 是《刑名·终》三场，已跑通全流程，可直接复现。

## 开新片

```bash
python3 tools/studio.py new --id p4 --title "《新片》" \
    --aesthetic cold-court-noir --persona PV-0142 --location LV-0001 \
    --idea "控制性理念" --runtime 60
```

命中库的资产直接带进来。**没填控制性理念的话，compile 会直接拒绝执行** ——
那不是 bug，没有它无法判定价值运动，整条链断在起点。

## 顺序为什么是这个

```
new     ← C 先出手，因为复用决定了这部片的起点成本
compile ← A 把剧本变成数据；门禁在这里拦掉最贵的错误（剧本层）
decide  ← B 在数据基础上做判断，不是在空白上做判断
build   ← 三方汇合：A 的骨架 + C 的句库 + B 的决策
ship    ← A 出货
close   ← C 回收 + 参数回流，让下一部更便宜
```

**decide 必须在 compile 之后。** 没有价值运动和情绪轨迹，决策卡问不出好问题。

## 单独用子系统

```bash
python3 modules/orchestrator/tools/pipeline.py --help
python3 modules/console/tools/console.py --help
python3 modules/library/tools/vault.py --help
```

接口不变。但单独用会丢掉参数总线和微表演接合。
