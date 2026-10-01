# -*- coding: utf-8 -*-
"""卡片生成器：从 project.json 穷举分叉。系统不替你选，只把选项摆出来并说清后果。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import risk
CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
CAT = json.load(open(os.path.join(CFG, "card-catalog.json"), encoding="utf-8"))
POL = json.load(open(os.path.join(CFG, "policy-defaults.json"), encoding="utf-8"))

def _has_turn(s):  return s.get("value_polarity") in ("+ → −", "− → +")
def _flat(s):      return s.get("value_polarity") == "平衡" or s.get("value_in") == s.get("value_out")

WHEN = {"has_turn": _has_turn, "polarity_flat": _flat,
        "has_insert": lambda s: bool(s.get("insert_shots")),
        "is_last": lambda s: s.get("_is_last", False)}

def _dyn_opts(card, p, s):
    """动态选项：从项目数据生成"""
    if card.get("dynamic") == "cast_present":
        out = []
        for i, cid in enumerate(s.get("cast_present", [])):
            nm = next((c.get("name", c["id"]) for c in p.get("cast", []) if c["id"] == cid), cid)
            out.append({"k": "ABCD"[i], "label": nm, "value": cid,
                        "why": f"摄影机全程跟 {nm} 的情绪走；他的每一次状态变化决定运镜",
                        "effect": {"structure": 1}, "risk": []})
        return out
    if card.get("dynamic") == "beats":
        n = len(s.get("emotion_track", [])) or 3
        return [{"k": "ABCD"[i], "label": f"第{i+1}拍", "value": i+1,
                 "why": ["最早——一开始就让观众看见裂缝",
                         "中段——转折点上裂开，最标准",
                         "最后——撑到最后一刻才碎，代价最大也最狠"][min(i,2)],
                 "effect": {"structure": 1 if i == n-1 else 0}, "risk": []}
                for i in range(n)]
    return card.get("opts", [])

def _fmt(t, s, extra):
    d = dict(s or {}); d.update(extra or {})
    try: return t.format(**d)
    except Exception: return t

def generate(p):
    scenes = sorted(p.get("scenes", []), key=lambda x: x["no"])
    if scenes: scenes[-1]["_is_last"] = True
    out = []
    for card in CAT["cards"]:
        if card.get("scope") == "project":
            opts = card.get("opts", [])
            imp, spread = risk.impact(card, opts, len(p.get("prompts", [])) or 20, p)
            out.append(_mk(card, None, opts, p, imp, spread, {}))
            continue
        for s in scenes:
            w = card.get("when")
            if w and not WHEN[w](s): continue
            extra = {"camera_default": (s.get("emotion_track") or [{}])[-1].get("camera", "—"),
                     "n_prompts": s.get("planned_prompt_count", "?"),
                     "insert": (s.get("insert_shots") or [""])[0]}
            opts = _dyn_opts(card, p, s)
            if not opts: continue
            base = s.get("planned_prompt_count", 1)
            imp, spread = risk.impact(card, opts, base, p)
            out.append(_mk(card, s, opts, p, imp, spread, extra))
    out.sort(key=lambda c: -c["impact"])
    return out

def _mk(card, s, opts, p, imp, spread, extra):
    base = (s or {}).get("planned_prompt_count", 1)
    o2 = []
    for o in opts:
        lvl, why, conf = risk.risk_line(o.get("risk", []), p)
        o2.append({**o, "risk_level": lvl, "risk_why": why, "risk_conf": conf,
                   "cost_delta": risk.cost_delta(o, base, p)})
    F = POL["fatigue"]
    lvl = card["level"]
    if lvl in ("A", "B"):
        lvl = "A" if imp >= F["impact_threshold_must"] else ("B" if imp >= F["impact_threshold_delegate"] else "C")
    return {
        "cid": card["id"] + (f"@{s['no']}" if s else ""),
        "type": card["id"], "level": lvl, "stage": card["stage"],
        "scene": (s or {}).get("no"), "slug": (s or {}).get("slug", ""),
        "q": _fmt(card["q"], s, extra),
        "note": card.get("note", ""), "depends": card.get("depends"),
        "opts": o2, "impact": imp, "cost_spread": spread,
        "presets": card.get("presets", {}),
    }

def recommend(card, p):
    """推荐 = 与控制性理念的对齐，不是与成本的对齐。系统给理由，不替你选。"""
    ci = p.get("project", {}).get("controlling_idea", "")
    if not ci: return None, ""
    hi = max(card["opts"], key=lambda o: o.get("effect", {}).get("structure", 0))
    if hi.get("effect", {}).get("structure", 0) == 0: return None, ""
    return hi["k"], f"控制性理念是「{ci}」——{hi['label']} 更直接地把它可视化"
