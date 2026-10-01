# studio-library 快速上手

```bash
cd examples
python3 ../tools/vault.py ingest xingming.json      # 第一部片入库
python3 ../tools/vault.py compound                  # 此时只有一行，复用率 0%
python3 ../tools/vault.py checkout new.json --id p2 --title "《新片》" \
    --aesthetic cold-court-noir --persona PV-0142 --location LV-0001
# 补上缺口资产 → 跑产线 → 再 ingest → compound 就能看到复利
```

## 今天就该做的一件事

```bash
python3 tools/vault.py codex log hand_chaos --project 你的项目
```

每次抽卡失败记一行。**这是唯一零边际成本、跨全部项目通用的库**，
也是三个方向里唯一"今天开始记、下个月就省钱"的东西。

其余四个库都要绑定具体项目才生效，急不来。

## 微节拍句库怎么用

```bash
python3 tools/vault.py beat "emotion=隐忍,genre=古装"
python3 tools/vault.py beat "emotion=尴尬" --ensemble    # 群戏错开建议
```

检索结果可直接粘进提示词的 `【微表演】` 槽位 ——
那正是 `film-pipeline-orchestrator` 故意留空的地方。

## 三个 skill 的接法

```
studio-library  checkout   →  新片 project.json（已带演员/场景/美学）
orchestrator    run S1     →  场次数据
director-console deal/apply →  导演判断
orchestrator    all        →  出片
studio-library  ingest     →  新资产回库，复利 +1
```
