# -*- coding: utf-8 -*-
"""库健康：完备度 / 撞库 / 陈旧度 / 覆盖度热力。库不维护就会腐烂。"""
import sys, os, datetime, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

TH = lib.cfg("health-thresholds.json")["health"]
REQ = {"persona": ["core_lock","voice_prompt","handle_desc_zh","asset_specs"],
       "location": ["handle_desc_zh","views","palette"],
       "prop": ["handle_desc_zh","asset_specs"]}

def completeness(v):
    rows = lib.load(v)
    if not rows: return 1.0, []
    weak = []
    tot = 0
    for r in rows:
        have = sum(1 for k in REQ[v] if r.get(k))
        tot += have/len(REQ[v])
        if have < len(REQ[v]):
            weak.append((r["id"], [k for k in REQ[v] if not r.get(k)]))
    return round(tot/len(rows), 3), weak

def collisions(v):
    rows = lib.load(v); out = []
    for a, b in itertools.combinations(rows, 2):
        s = lib.sim(a.get("handle_desc_zh",""), b.get("handle_desc_zh",""))
        if s >= TH["collision_max"]:
            out.append((a["id"], b["id"], round(s,3)))
    return out

def stale(v):
    cut = (datetime.date.today() - datetime.timedelta(days=TH["staleness_days"])).isoformat()
    return [r["id"] for r in lib.load(v) if (r.get("last_seen") or "9999") < cut]

def coverage():
    """覆盖度热力：每个库按类型/维度的分布，看哪里是空的"""
    from collections import Counter
    b = lib.load("beat")
    return {"beat_by_genre": dict(Counter(x["genre"] for x in b)),
            "beat_by_emotion": dict(Counter(x["emotion"] for x in b)),
            "beat_by_shot": dict(Counter(x["shot"] for x in b)),
            "persona_projects": dict(Counter(len(r.get("used_in",[])) for r in lib.load("persona"))),
            "location_projects": dict(Counter(len(r.get("used_in",[])) for r in lib.load("location")))}
