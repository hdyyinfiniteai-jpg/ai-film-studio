# director-console 快速上手

```bash
cd examples
python3 ../tools/console.py deal        # 先看分叉总量与分流
python3 ../tools/console.py show STRAT_INSERT
python3 ../tools/console.py answer STRAT_INSERT A
# ... 答完 S 级策略卡，重新 deal，场次卡数量会明显下降
python3 ../tools/console.py auto
python3 ../tools/console.py apply --prune
python3 ../tools/console.py render      # → DecisionDeck.html
```

## 先答策略卡，这不是建议是流程

策略卡（S 级）答完之前不要碰场次卡。三张 S 卡答完，
大量 B/C 级场次卡会被自动预填 —— 这是决策预算的主要来源。

## 与产线的交接

```
orchestrator run S1  →  console deal/answer/apply  →  orchestrator all
```

两者共享 `project.json`。示例里的 `project.json` 就是从
`06_film-pipeline-orchestrator/examples/` 拿过来跑过 S1–S4 的。

## 一件容易误解的事

`console.py apply` **默认不删场次**，即使你在 STORY_BREATHER 卡上选了"删掉"。
必须加 `--prune`。删场是不可逆的，不该默认发生。
