# -*- coding: utf-8 -*-
"""五道门禁。跑不过不许进下一阶段——把艺术判断和工程检查分开，人只在门禁处做决定。"""
from common import cfg, aesthetic
import timing, audit

G  = cfg("gates.json")
TH = G["thresholds"]
TAX = {tuple(x) for x in cfg("value-taxonomy.json")["pairs"]}

def _r(name, passed, detail=""):
    return {"check": name, "pass": bool(passed), "detail": detail}

def G1(p):
    r = []
    ci = p.get("project", {}).get("controlling_idea", "")
    r.append(_r("controlling_idea_present", bool(ci), ci or "缺控制性理念——无法判定价值运动"))
    sc = p.get("scenes", [])
    miss = [s["no"] for s in sc if not s.get("value_in") or not s.get("value_out")]
    r.append(_r("every_scene_has_value", not miss, f"缺价值的场次：{miss}" if miss else "全部已填"))
    off = [s["no"] for s in sc if (s.get("value_in"), s.get("value_out")) not in TAX
           and (s.get("value_out"), s.get("value_in")) not in TAX]
    r.append(_r("value_in_taxonomy", not off, f"不在词库的场次：{off}" if off else "全部命中词库"))
    tgt = p.get("project", {}).get("target_runtime_sec") or 0
    act = timing.project_runtime(p)
    okr = (not tgt) or abs(act - tgt) <= tgt * TH["runtime_tolerance"]
    r.append(_r("runtime_within_tolerance", okr, f"目标{tgt}s / 实际{act}s"))
    pol = [s.get("value_polarity") for s in sc]
    flat = pol.count("平衡")
    run = mx = 0; last = None
    for x in pol:
        run = run + 1 if x == last and x in ("+ → −", "− → +") else 1
        last = x; mx = max(mx, run)
    okp = (not sc) or (flat <= len(sc)*TH["flat_polarity_max_ratio"] and mx < TH["flat_polarity_run"]+1)
    r.append(_r("polarity_not_flat", okp,
                f"呼吸场{flat}/{len(sc)}，同极性最长连续{mx}场"))
    return r

def G2(p):
    bad = [s["no"] for s in p.get("scenes", []) if not s.get("ai_shootability", {}).get("passed")]
    return [_r("shootability_all_pass", not bad, f"未过可拍审计的场次：{bad}" if bad else "全部通过")]

def G3(p):
    r = []
    nc = [c["id"] for c in p.get("cast", []) if not c.get("core_lock")]
    r.append(_r("every_cast_has_core_lock", not nc, f"缺 core_lock：{nc}" if nc else "全部已锁"))
    nv = [c["id"] for c in p.get("cast", []) if not c.get("voice_prompt")]
    r.append(_r("every_cast_has_voice", not nv, f"缺 voice_prompt：{nv}" if nv else "全部已锁"))
    nl = [l["id"] for l in p.get("locations", []) if len(l.get("views", {})) < 2]
    r.append(_r("every_location_has_views", not nl, f"视图不足2个：{nl}" if nl else "主视图+反打齐备"))
    npp = [x["id"] for x in p.get("props", []) if not x.get("asset_specs")]
    r.append(_r("every_prop_has_spec", not npp, f"缺规格：{npp}" if npp else "全部有规格"))
    pal = aesthetic(p).get("palette_60_30_10", [])
    r.append(_r("palette_locked", len(pal) == 3, f"色板：{pal}"))
    return r

def G4(p):
    r = []
    nb = [s["no"] for s in p.get("scenes", [])
          if len(s.get("cast_present", [])) >= 2 and not s.get("blocking_svg")]
    r.append(_r("blocking_for_multichar", not nb, f"缺走位图：{nb}" if nb else "多人场次走位齐备"))
    ne = [s["no"] for s in p.get("scenes", []) if not s.get("emotion_track")]
    r.append(_r("emotion_track_present", not ne, f"缺情绪轨迹：{ne}" if ne else "全部已推导"))
    return r

def G5(p):
    f = audit.run(p)
    red = [x for x in f if x["level"] == "红"]
    r = [_r("consistency_no_red", not red, f"红项 {len(red)} 条" if red else "无红项")]
    for x in f:
        r.append(_r(x["code"], x["level"] != "红", f"[{x['level']}] {x['msg']} → {x['prompts'][:6]}"))
    return r

RUNNERS = {"G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5}

def run(p, gid):
    res = RUNNERS[gid](p)
    passed = all(x["pass"] for x in res)
    return passed, res
