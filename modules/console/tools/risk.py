# -*- coding: utf-8 -*-
"""风险与成本预判。方向B与普通『给你几个选项』的唯一区别：选项后面挂着工程后果。
   诚实纪律：样本不足时必须标注『拍脑袋』——否则导演会信任一个猜出来的数字。"""
import json, os
CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
R = json.load(open(os.path.join(CFG, "risk-table.json"), encoding="utf-8"))
P = json.load(open(os.path.join(CFG, "policy-defaults.json"), encoding="utf-8"))

CONF_MIN_N = 15

def measured(p):
    """从 project.json 的 generation_log 计算实测 E[尝试]；样本不足返回 None"""
    logs = [x for q in p.get("prompts", []) for x in q.get("generation_log", [])]
    passes = sum(1 for q in p.get("prompts", []) if any(x["verdict"] == "pass" for x in q.get("generation_log", [])))
    if passes >= 20:
        return round(len(logs) / passes, 2), len(logs)
    return None, len(logs)

def risk_line(codes, p=None):
    """返回 (等级, 说明, 置信度)"""
    if not codes:
        return "低", "无已知高风险因素", "基线"
    mult, labels, ns = 1.0, [], []
    for c in codes:
        r = R["risks"].get(c)
        if not r: continue
        mult *= r["mult"]; labels.append(r["label"]); ns.append(r["n"])
    lvl = "高" if mult >= 1.35 else "中" if mult >= 1.15 else "低"
    conf = "实测" if ns and min(ns) >= CONF_MIN_N else "拍脑袋"
    return lvl, "、".join(labels) + f"（系数 ×{round(mult,2)}）", conf

def cost_delta(opt, base_prompts=1, p=None):
    """该选项相对基线的成本增量（美元）"""
    e, _ = measured(p or {})
    base = e or R["baseline_attempts"]
    unit = R["unit_cost_usd"]
    eff = opt.get("effect", {})
    n = base_prompts + (eff.get("prompts") if isinstance(eff.get("prompts"), int) else 0)
    n = max(0, n)
    mult = eff.get("cost_mult", 1.0)
    for c in opt.get("risk", []):
        mult *= R["risks"].get(c, {}).get("mult", 1.0)
    return round(n * base * mult * unit - base_prompts * base * unit, 2)

def impact(card, opts, base_prompts=1, p=None):
    """影响面评分——决定这张卡是必答/托管/自动"""
    W = P["impact_weights"]
    costs = [cost_delta(o, base_prompts, p) for o in opts]
    spread = max(costs) - min(costs)
    struct = max(o.get("effect", {}).get("structure", 0) for o in opts)
    prm = max(abs(o.get("effect", {}).get("prompts", 0)) if isinstance(o.get("effect", {}).get("prompts"), int) else 0
              for o in opts)
    irr = any(o.get("effect", {}).get("irreversible") for o in opts)
    s = struct * W["structure"] + spread / W["cost_usd_per_point"] + prm / W["prompts_affected_per_point"]
    if irr: s += W["irreversible_bonus"]
    if card.get("scope") == "project": s += 4.0
    return round(s, 2), round(spread, 2)
