# -*- coding: utf-8 -*-
"""复利报表。方向C的北极星不是 E[尝试次数]，是【复用率】与【第N部片边际成本】。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

C = lib.cfg("health-thresholds.json")["compounding"]
U = C["unit_cost_usd"]

def projects():
    s = set()
    for v in ("persona","location","prop"):
        for r in lib.load(v): s.update(r.get("used_in", []))
    return sorted(s)

def reuse_rate(pid):
    """该片用到的资产里，有多少是在它之前就已入库的"""
    hit = tot = 0
    order = projects()
    if pid not in order: return None, 0, 0
    rank = order.index(pid)
    for v in ("persona","location","prop"):
        for r in lib.load(v):
            if pid not in r.get("used_in", []): continue
            tot += 1
            earlier = [x for x in r["used_in"] if x in order and order.index(x) < rank]
            if earlier: hit += 1
    return (round(hit/tot, 3) if tot else None), hit, tot

def asset_cost(pid):
    """本片的资产生成成本：命中库的算变体价，新建的算全价"""
    cost = 0.0; detail = {"new":0,"reused":0}
    order = projects(); rank = order.index(pid) if pid in order else 0
    for v, kn, kv in (("persona","persona_new","persona_variant"),
                      ("location","location_new","location_view"),
                      ("prop","prop_new","prop_new")):
        for r in lib.load(v):
            if pid not in r.get("used_in", []): continue
            earlier = [x for x in r["used_in"] if x in order and order.index(x) < rank]
            if earlier: cost += U[kv]; detail["reused"] += 1
            else:       cost += U[kn]; detail["new"] += 1
    return round(cost, 2), detail

def report():
    out = []
    base = None
    for i, pid in enumerate(projects(), 1):
        rr, hit, tot = reuse_rate(pid)
        c, d = asset_cost(pid)
        if base is None: base = c or 1
        out.append({"n": i, "project": pid, "assets": tot, "reused": hit,
                    "reuse_rate": rr, "asset_cost_usd": c,
                    "vs_first": round(c/base, 2) if base else None, **d})
    return {"rows": out, "estimate_curve": C["estimate_curve"],
            "north_star": lib.cfg("health-thresholds.json")["north_star"]}
