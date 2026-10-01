# -*- coding: utf-8 -*-
"""参数总线 —— 这是三套系统真正的融合点。

融合前：A 的成本模型、B 的风险系数、C 的失败档案各读各的配置，参数是断的。
融合后：C 积累的实测数据单向流向 A 和 B。
        谁也不许反向写 C —— 库是唯一的事实来源。
"""
import os, json
from collections import Counter
import paths as P

MIN_N = 15

def collect(project_paths):
    """从库事件 + 各片 generation_log 汇总失败分布与 E[尝试次数]"""
    ev = []
    epath = os.path.join(P.LIBR, "library", "codex", "events.jsonl")
    if os.path.exists(epath):
        ev = [json.loads(l) for l in open(epath, encoding="utf-8") if l.strip()]
    modes = Counter(e["mode"] for e in ev)

    attempts = passes = 0
    for pp in project_paths:
        if not os.path.exists(pp): continue
        p = P.jload(pp)
        for pr in p.get("prompts", []):
            lg = pr.get("generation_log", [])
            attempts += len(lg)
            if any(x.get("verdict") == "pass" for x in lg): passes += 1
    e_att = round(attempts / passes, 2) if passes >= 20 else None
    return modes, e_att, attempts, passes

def apply(modes, e_att, dry=False):
    """写回 A 的 cost-model 与 B 的 risk-table。样本不足则不动，并如实说明。"""
    out = []
    # --- A: baseline_attempts ---
    cm_path = os.path.join(P.ORCH, "config", "cost-model.json")
    cm = P.jload(cm_path)
    if e_att:
        old = cm["baseline_attempts"]; cm["baseline_attempts"] = e_att
        cm["_measured"] = True
        if not dry: P.jsave(cm, cm_path)
        out.append(f"A cost-model.baseline_attempts {old} → {e_att}（实测）")
    else:
        out.append(f"A cost-model 未更新：通过样本 <20，仍用基线 {cm['baseline_attempts']}")

    # --- B: risk mult + n ---
    rt_path = os.path.join(P.CONS, "config", "risk-table.json")
    rt = P.jload(rt_path)
    total = sum(modes.values()) or 1
    changed = 0
    for code, r in rt["risks"].items():
        fm = r.get("fm")
        if not fm: continue
        n = modes.get(fm, 0)
        r["n"] = n
        if n >= MIN_N:
            share = modes[fm] / total
            r["mult"] = round(1.0 + share * 1.2, 2)   # 占比越高，该风险越贵
            changed += 1
    if e_att: rt["baseline_attempts"] = e_att
    if not dry: P.jsave(rt, rt_path)
    out.append(f"B risk-table 样本回填 {len(rt['risks'])} 项；其中 {changed} 项达 n≥{MIN_N} 转为实测系数")
    if not changed:
        out.append(f"   （所有模式样本 <{MIN_N}，界面继续显示『拍脑袋』——这是诚实，不是缺陷）")
    return out
