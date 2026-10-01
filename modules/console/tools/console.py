#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""director-console · 导演决策台

  deal      穷举分叉，按影响面排序，分流为 S/A/B/C 四级
  show      看一张完整卡（含每个选项的抽卡风险与成本影响）
  answer    作答，写入决策日志
  auto      把 B 级卡按策略卡默认批量托管（可随时翻牌改）
  apply     把已决卡写回 project.json
  profile   决策日志 → 导演偏好画像
  render    输出 HTML 决策台

纪律：
  · 系统穷举选项并预判后果，但绝不替你选
  · 选 B（反用映射）必须写一句理由 —— 反用是选择，不是遗忘
  · 样本 <15 的风险标签一律标『拍脑袋』
"""
import sys, os, json, argparse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cards as C, risk as R

DECK = "deck.json"

def _w(t):
    """东亚宽字符按2列计——否则中文卡片框全歪"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in t)

def _pad(t, w):
    """按显示宽度补齐；超宽则截断"""
    out, cur = "", 0
    for c in t:
        cw = _w(c)
        if cur + cw > w: break
        out += c; cur += cw
    return out + " " * (w - cur)

def _load(f):
    return json.load(open(f, encoding="utf-8"))
def _save(o, f):
    json.dump(o, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def _deck(a):
    if not os.path.exists(a.deck): return {"cards": [], "answers": {}, "log": []}
    return _load(a.deck)

def cmd_deal(a):
    p = _load(a.file); d = _deck(a)
    new = C.generate(p)
    keep = {x["cid"]: x for x in new}
    d["cards"] = list(keep.values())
    _save(d, a.deck)
    runtime = p.get("project", {}).get("target_runtime_sec", 0) or 1
    budget = max(3, round(runtime / 600 * C.POL["fatigue"]["must_answer_per_10min"]))
    lv = {}
    for c in d["cards"]: lv.setdefault(c["level"], []).append(c)
    print(f"分叉总数 {len(d['cards'])}")
    for k in "SABC":
        n = len(lv.get(k, []))
        print(f"  {k} {C.POL['levels'][k][:24]:26s} {n:3d} 张")
    must = [c for c in d["cards"] if c["level"] in ("S", "A") and c["cid"] not in d["answers"]]
    print(f"\n决策预算：{budget} 张必答卡（按 {runtime}s 片长）")
    if len(must) > budget:
        # 真降级，不是嘴上说说：超预算的 A 卡改为 B，进托管队列
        for c in must[budget:]:
            if c["level"] == "A": c["level"] = "B"; c["downgraded"] = True
        _save(d, a.deck)
        print(f"▲ 必答卡 {len(must)} 张超预算 —— 影响面最高的 {budget} 张留在必答，"
              f"其余 {len(must)-budget} 张已降级为托管（deal 后可 auto 批量预填，随时翻牌改）")
        must = must[:budget]
    print()
    for c in must[:budget]:
        tag = f"第{c['scene']}场" if c["scene"] else "全片"
        print(f"  [{c['level']}] {c['cid']:26s} 影响面 {c['impact']:5.2f}  ±${c['cost_spread']:<6} {tag}  {c['q'][:34]}")
    print(f"\n看卡：console.py show <cid>    作答：console.py answer <cid> A")

def _card(d, cid):
    return next((c for c in d["cards"] if c["cid"] == cid), None)

def cmd_show(a):
    p = _load(a.file); d = _deck(a); c = _card(d, a.cid)
    if not c: sys.exit(f"✖ 无此卡 {a.cid}")
    W = 76
    print("┌" + "─"*W + "┐")
    head = f" 决策卡 · {c['cid']}" + (f" · 第{c['scene']}场 {c['slug']}" if c['scene'] else " · 全片策略")
    print("│" + _pad(head, W) + "│")
    print("├" + "─"*W + "┤")
    print("│" + _pad(f" 【本卡要决定】{c['q']}", W) + "│")
    print("│" + " "*W + "│")
    for o in c["opts"]:
        print("│" + _pad(f"   {o['k']}) {o['label']}", W) + "│")
        print("│" + _pad(f"      · {o['why']}", W) + "│")
        cd = o["cost_delta"]
        print("│" + _pad(f"      · 成本影响：{'+' if cd>=0 else ''}${cd}", W) + "│")
        print("│" + _pad(f"      · 抽卡风险：{o['risk_level']}（{o['risk_why']}）[{o['risk_conf']}]", W) + "│")
        if o.get("note"): print("│" + _pad(f"      · 代价：{o['note']}", W) + "│")
        print("│" + " "*W + "│")
    k, why = C.recommend(c, p)
    if k: print("│" + _pad(f" 【推荐】{k} —— {why}", W) + "│")
    if c.get("note"): print("│" + _pad(f" 【note】{c['note']}", W) + "│")
    print("└" + "─"*W + "┘")
    if c["cid"] in d["answers"]:
        av = d["answers"][c["cid"]]
        print(f"已答：{av['k']}" + (f"  理由：{av['why']}" if av.get("why") else ""))

def cmd_answer(a):
    d = _deck(a); c = _card(d, a.cid)
    if not c: sys.exit(f"✖ 无此卡 {a.cid}")
    o = next((x for x in c["opts"] if x["k"] == a.k), None)
    if not o: sys.exit(f"✖ 无此选项 {a.k}")
    if o.get("effect", {}).get("irreversible") and not a.why:
        sys.exit("✖ 该选项不可逆（反用映射/结构性改动），必须用 --why 写一句理由")
    d["answers"][c["cid"]] = {"k": a.k, "label": o["label"], "why": a.why or "",
                              "cost_delta": o["cost_delta"], "risk": o["risk_level"],
                              "auto": False,
                              "at": datetime.datetime.now().isoformat(timespec="minutes")}
    d["log"].append({"cid": c["cid"], "type": c["type"], "k": a.k, "label": o["label"],
                     "why": a.why or "", "impact": c["impact"]})
    _save(d, a.deck)
    print(f"✔ {c['cid']} = {a.k} {o['label']}  (成本 {'+' if o['cost_delta']>=0 else ''}${o['cost_delta']})")

def cmd_auto(a):
    """B 级托管：按已答策略卡预填。不是自动化，是『先替你摆好，随时翻牌改』"""
    d = _deck(a); n = 0
    strat = {k: v for k, v in d["answers"].items() if k.startswith("STRAT_")}
    ins = strat.get("STRAT_INSERT", {}).get("k")
    for c in d["cards"]:
        if c["level"] not in ("B", "C") or c["cid"] in d["answers"]: continue
        k = None
        if c["type"] == "SHOT_INSERT" and ins: k = "A" if ins == "A" else "B"
        elif c["type"] == "CAM_OVERRIDE": k = "A"
        elif c["type"] == "SHOT_SPLIT":  k = "A"
        elif c["type"] == "PERF_VARIANT_2": k = "A"
        if not k: continue
        o = next((x for x in c["opts"] if x["k"] == k), None)
        if not o: continue
        d["answers"][c["cid"]] = {"k": k, "label": o["label"], "why": "托管：按策略卡默认",
                                  "cost_delta": o["cost_delta"], "risk": o["risk_level"],
                                  "auto": True, "at": datetime.datetime.now().isoformat(timespec="minutes")}
        n += 1
    _save(d, a.deck); print(f"✔ 托管 {n} 张（标记 auto=true，随时可翻牌改）")

def cmd_apply(a):
    p = _load(a.file); d = _deck(a); n = 0
    for cid, av in d["answers"].items():
        c = _card(d, cid)
        if not c: continue
        if c["scene"] is None:
            pre = c.get("presets", {}).get(av["k"], {})
            p.setdefault("director_policy", {}).update(pre); n += 1
            continue
        s = next((x for x in p["scenes"] if x["no"] == c["scene"]), None)
        if not s: continue
        o = next((x for x in c["opts"] if x["k"] == av["k"]), {})
        t = c["type"]
        if t == "STORY_VALUE_OWNER" and o.get("value"): s["focal_character"] = o["value"]; n += 1
        elif t == "PERF_MASK_CRACK" and o.get("value"): s["mask_crack_beat"] = o["value"]; n += 1
        elif t == "CAM_OVERRIDE" and av["k"] == "B":
            s["mapping_override"] = {"reason": av["why"]}; n += 1
        elif t == "SHOT_SPLIT":
            base = s.get("planned_prompt_count", 1)
            s["planned_prompt_count"] = max(1, base + (0 if av["k"] == "A" else (-1 if av["k"] == "B" else 1))); n += 1
        elif t == "SHOT_INSERT" and av["k"] == "B": s["insert_shots"] = []; n += 1
        elif t == "STORY_BREATHER" and av["k"] == "B": s["cut_me"] = True; n += 1
        elif t in ("PERF_VARIANT_1", "PERF_VARIANT_2"):
            s.setdefault("perf_direction", {})[t] = o.get("label"); n += 1
    cut = [s["no"] for s in p["scenes"] if s.get("cut_me")]
    if cut and a.prune:
        p["scenes"] = [s for s in p["scenes"] if not s.get("cut_me")]
        print(f"✔ 已删除呼吸场 {cut}（--prune）")
    elif cut:
        print(f"▲ 第{cut}场已判定删除，但未执行 —— 加 --prune 才真删（不可逆，故不默认）")
    _save(p, a.file); print(f"✔ 回写 {n} 项到 {a.file}")

def cmd_profile(a):
    d = _deck(a)
    if not d["log"]: sys.exit("尚无决策记录")
    from collections import Counter
    byt = {}
    for e in d["log"]: byt.setdefault(e["type"], Counter())[e["k"]] += 1
    print("导演偏好画像（决策日志沉淀）\n")
    lines = []
    for t, c in sorted(byt.items()):
        tot = sum(c.values()); k, n = c.most_common(1)[0]
        lab = next((e["label"] for e in d["log"] if e["type"] == t and e["k"] == k), k)
        pct = round(n/tot*100)
        conf = "稳定偏好" if tot >= 5 and pct >= 70 else "样本不足"
        print(f"  {t:22s} {lab:14s} {n}/{tot} ({pct}%)  {conf}")
        if conf == "稳定偏好": lines.append(f"- {t}：默认选「{lab}」")
    whys = [e for e in d["log"] if e["why"]]
    if whys:
        print("\n覆写理由（这些是你真正的作者性所在）：")
        for e in whys[:8]: print(f"  · {e['cid']}：{e['why']}")
    if lines:
        open("my-style.md","w",encoding="utf-8").write(
            "# 导演偏好画像\n\n> 由决策日志自动沉淀。下一部片可预填。\n\n" + "\n".join(lines) + "\n")
        print("\n✔ 已写出 my-style.md（下一部片开局直接预填）")

def cmd_render(a):
    import deck_html
    p = _load(a.file); d = _deck(a)
    path = deck_html.build(p, d, a.out)
    print(f"✔ 决策台 → {path}")

def main():
    ap = argparse.ArgumentParser(prog="console.py")
    ap.add_argument("--file", default="project.json"); ap.add_argument("--deck", default=DECK)
    ap.add_argument("--out", default="DecisionDeck.html")
    s = ap.add_subparsers(dest="c", required=True)
    s.add_parser("deal").set_defaults(func=cmd_deal)
    x = s.add_parser("show"); x.add_argument("cid"); x.set_defaults(func=cmd_show)
    x = s.add_parser("answer"); x.add_argument("cid"); x.add_argument("k")
    x.add_argument("--why", default=""); x.set_defaults(func=cmd_answer)
    s.add_parser("auto").set_defaults(func=cmd_auto)
    x = s.add_parser("apply"); x.add_argument("--prune", action="store_true"); x.set_defaults(func=cmd_apply)
    s.add_parser("profile").set_defaults(func=cmd_profile)
    s.add_parser("render").set_defaults(func=cmd_render)
    a = ap.parse_args(); a.func(a)

if __name__ == "__main__": main()
