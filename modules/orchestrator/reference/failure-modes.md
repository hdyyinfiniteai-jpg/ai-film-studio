# 失败模式库（16 类固定枚举）

> 与 `seedance-director-master` 的 12 类知识库同源，此处为扩展版：**加了实测统计层**。
> 不要维护两份词库 —— 模式定义以此为准，seedance 那份升级为引用。

```
handle_contamination  句柄污染      identity_drift     身份漂移
pose_contamination    姿态污染      light_spill        光线越界
wide_distortion       广角畸变      floating_prop      道具漂浮
god_rays              上帝之光      empty_bg           背景空洞
hand_chaos            手部混乱      scale_mismatch     尺度错配
camera_wild           运镜失控      spurious_cut       伪剪辑
focus_drift           焦点漂移      perf_flat          表演扁平
prompt_ignored        指令忽略      other              其他
```

## 症状 → 根因判定树

```
"人物看起来不对"
 ├ 是同一个人但气质变了？       → perf_flat
 ├ 五官明显不同？
 │   ├ 该角色在本条中离过框？   → identity_drift
 │   └ 本条有 3 个以上角色？    → handle_contamination
 └ 姿势像参考图不像剧本？       → pose_contamination
```

## 防御句必须做 A/B —— 大量 ⚠️ 是安慰剂

```
FM hand_chaos
├ 无防御：                       n=20  失败 8   40%
├ v1「⚠️手指数量正确」：          n=15  失败 6   40%  ← 废话防御句
└ v2 点名五指姿态 + 四条禁令：     n=18  失败 3   17%  ← 有效
```

不做对照，你会积累一堆越写越长但没用的警告 —— 而且它们还会吃掉注意力预算，
反过来触发 `prompt_ignored`。

## 提升进通用 STYLE_BLOCK 的判据（三条全满足）

1. 样本 n ≥ 15
2. 防御后失败率降幅 ≥ 15 个百分点
3. 该模式出现在 ≥30% 的提示词中（否则局部加就够）

**第 3 条最容易被忽略**：通用块每加一句，所有提示词的注意力预算都被吃掉一点。

## 北极星指标

```
E[尝试次数] = 总生成次数 / 通过条数
基线 3.0 → 目标 1.8。每降 0.1，全片算力成本约降 3%。
```

Hell Grind 公开数据：约 80% 预算是算力。**这是产线唯一真正的降本杠杆。**
