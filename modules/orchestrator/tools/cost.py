# -*- coding: utf-8 -*-
"""成本模型。Hell Grind 公开数据：约80%预算是算力 ——
   降低 E[尝试次数] 是这条产线唯一真正的降本杠杆。"""
from common import cfg

C = cfg("cost-model.json")

def risk_tags(pr):
    t = pr["text_zh"]; tags = []
    if any(k in t for k in ["手指","手部","指节","握"]) and any(k in pr.get("tag","") for k in ["CU","ECU"]):
        tags.append("hand_closeup")
    if len(pr.get("handles", {})) >= 4: tags.append("three_plus_named")
    if any(k in t for k in ["奔跑","打斗","追逐","扑","撞"]): tags.append("fast_action")
    if pr.get("shot_count", 1) >= 3: tags.append("multi_shot_dialogue")
    if "WS" in pr.get("tag","") and len(pr.get("handles", {})) >= 2: tags.append("extreme_wide_named")
    if any(k in t for k in ["写着","字迹","牌匾"]): tags.append("text_in_frame")
    return tags

def expected_attempts(p, pr):
    logs = [x for q in p.get("prompts", []) for x in q.get("generation_log", [])]
    passes = sum(1 for q in p.get("prompts", []) if any(x["verdict"]=="pass" for x in q.get("generation_log", [])))
    base = round(len(logs)/passes, 2) if passes >= 20 else C["baseline_attempts"]
    m = 1.0
    for t in risk_tags(pr): m *= C["risk_multipliers"][t]
    return round(base * m, 2), base

def report(p):
    rows = []; total = 0.0; att_total = 0.0
    unit = C["unit_cost_usd"]["video_15s"]
    for pr in p.get("prompts", []):
        e, base = expected_attempts(p, pr)
        c = round(e * unit, 2)
        rows.append({"id": pr["id"], "risk": risk_tags(pr), "E_attempts": e, "usd": c})
        total += c; att_total += e
    imgs = sum(len(x.get("asset_specs", [])) for k in ("cast","locations","props") for x in p.get(k, []))
    img_cost = round(imgs * C["unit_cost_usd"]["image"] * 2.0, 2)
    actual = sum(x.get("cost", {}).get("usd", 0) for x in p.get("prompts", []))
    return {
        "prompt_count": len(rows),
        "asset_image_count": imgs,
        "baseline_E_attempts": round(att_total/max(1,len(rows)), 2),
        "video_usd_est": round(total, 2),
        "image_usd_est": img_cost,
        "total_usd_est": round(total + img_cost, 2),
        "actual_usd": round(actual, 2),
        "rows": sorted(rows, key=lambda r: -r["usd"])[:20],
        "north_star": "E[尝试次数] —— 基线3.0，目标1.8；每降0.1，算力成本约降3%",
    }
