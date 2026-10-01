#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""studio-library · 资产库 CLI

  ingest <project.json>          一部片跑完，把原子件入库（自动撞库合并）
  find <vault> "<query>"         检索。DSL: key=value,key=value 或自由词
  beat "<query>"                 微节拍句库检索（专用，带群戏错开）
  checkout <out.json> ...        新片开局，从库预填 project.json
  codex log <mode> [--project]   记一次抽卡失败
  codex stats                    失败模式分布 + 防御句 ROI
  health                         库健康：完备度/撞库/陈旧/覆盖度热力
  compound                       复利报表：复用率与第N部片边际成本

纪律：
  · 只入库去项目化的部分。角色本体入库，本片的场次归属不入库
  · 撞库用文本相似度自动检测（≥0.88 视为同一资产，合并而非新建）
  · 库不维护会腐烂 —— health 每月跑一次
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, ingest, query, checkout, health, compound

def ok(m): print(f"✔ {m}")
def warn(m): print(f"▲ {m}")

def c_ingest(a):
    r = ingest.run(a.project, a.dry)
    for v, src, nid in r["new"]:   print(f"  ＋ {v:9s} {src:22s} → {nid}")
    for v, src, hid, s in r["merged"]: print(f"  ≡ {v:9s} {src:22s} → 命中 {hid}（相似度 {s}）")
    for v, src, why in r["skipped"]: warn(f"  跳过 {v} {src}：{why}")
    ok(f"新增 {len(r['new'])} · 合并 {len(r['merged'])}" + ("（dry-run，未落盘）" if a.dry else ""))

def c_find(a):
    rows = query.run(a.vault, a.q, a.limit)
    if not rows: return warn("无命中")
    for r in rows:
        extra = f" · 用于 {r.get('used_in')}" if r.get("used_in") else ""
        print(f"  {r['id']}  {r.get('name') or r.get('emotion','')}  "
              f"{(r.get('handle_desc_zh') or r.get('text',''))[:44]}{extra}")
    ok(f"{len(rows)} 条")

def c_beat(a):
    rows = query.run("beat", a.q, a.limit)
    if not rows: return warn("无命中。试试放宽维度，或这是个该补库的缺口")
    for i, r in enumerate(rows):
        c = " [身体与台词矛盾]" if r.get("contradiction") else ""
        print(f"  {r['id']} {r['emotion']}·{r['intensity']}·{r['posture']}·"
              f"{'说话' if r['speaking'] else '不说话'}·{r['shot']}·{r['genre']}{c}")
        print(f"      {r['text']}")
    if a.ensemble and len(rows) >= 2:
        print("\n  群戏错开建议（禁同步反应）：")
        for i, r in enumerate(rows[:3]):
            print(f"    角色{i+1}：{r['id']}，延迟 {i*0.4:.1f}s 起反应")
    ok(f"{len(rows)} 条")

def c_checkout(a):
    hit, miss, aes = checkout.run(a.out, a.title, a.id, a.aesthetic,
        a.persona or [], a.location or [], a.prop or [],
        a.idea, a.runtime, a.aspect, a.type)
    for v, i in hit:  print(f"  ✔ {v:9s} {i}  命中库，成本≈变体价")
    for v, i in miss: print(f"  ✖ {v:9s} {i}  不在库中，需新建")
    n = len(hit) + len(miss)
    rate = round(len(hit)/n, 2) if n else 0
    ok(f"预填 {a.out} · 美学 {aes['name']} · 命中 {len(hit)}/{n}（复用率 {rate}）")
    if miss: warn("缺口资产：新建后记得 ingest 回库，下一部就是命中")

def c_codex(a):
    if a.sub == "log":
        lib.add("events", {"project": a.project or "-", "prompt": a.prompt or "-",
                           "mode": a.mode, "at": lib.today()})
        ok(f"记录 {a.mode}")
        return
    from collections import Counter
    ev = lib.load("events"); cx = lib.load("codex")
    if not ev: return warn("尚无事件。每次抽卡失败记一行——这是唯一零边际成本、跨全部项目通用的库")
    c = Counter(e["mode"] for e in ev)
    print(f"事件总数 {len(ev)}\n")
    for m, n in c.most_common():
        e = next((x for x in cx if x["code"] == m), {})
        conf = "实测" if n >= 15 else "样本不足"
        print(f"  {m:22s} {n:3d} 次 {'█'*min(n,28)}  [{conf}]  ROI {e.get('roi','?')}")
    print("\n防御句状态：")
    for e in cx:
        st = "已提升通用块" if e.get("promoted") else ("有防御句" if e.get("defense") else "无防御句")
        rate = f"{e['fail_rate']:.0%}→{e['defense_rate']:.0%}" if e.get("defense_rate") else "—"
        print(f"  {e['id']} {e['name']:8s} {st:12s} {rate}")
    print("\n提升判据（三条全满足）：样本 n≥15 · 降幅≥15个百分点 · 出现率≥30%")

def c_health(a):
    T = lib.cfg("health-thresholds.json")["health"]
    for v in ("persona","location","prop"):
        comp, weak = health.completeness(v)
        col = health.collisions(v); st = health.stale(v)
        flag = "✔" if comp >= T["completeness_min"] else "▲"
        print(f"{flag} {v:9s} 条目 {len(lib.load(v)):3d} · 完备度 {comp:.0%} "
              f"· 撞库 {len(col)} · 陈旧 {len(st)}")
        for i, ks in weak[:3]: print(f"      缺字段 {i}: {ks}")
        for x in col[:3]: print(f"      撞库 {x[0]} ≈ {x[1]} ({x[2]}) —— 应合并或明确区分")
    cov = health.coverage()
    print("\n覆盖度热力（找空洞）：")
    for k, v in cov.items():
        print(f"  {k}: {v}")
    b = cov["beat_by_genre"]
    thin = [g for g in ("古装","喜剧","都市","悬疑") if b.get(g, 0) < 8]
    if thin: print(f"\n▲ 微节拍库偏薄的类型：{thin} —— 这些是下次该补的缺口")

def c_compound(a):
    r = compound.report()
    if not r["rows"]: return warn("库中尚无项目。ingest 第一部片之后才有复利可算")
    print(f"{'#':>2} {'项目':<14}{'资产':>5}{'复用':>5}{'复用率':>8}{'资产成本':>10}{'vs首片':>8}")
    for x in r["rows"]:
        rr = f"{x['reuse_rate']:.0%}" if x["reuse_rate"] is not None else "—"
        print(f"{x['n']:>2} {x['project']:<14}{x['assets']:>5}{x['reused']:>5}{rr:>8}"
              f"{x['asset_cost_usd']:>10}{(str(x['vs_first'])+'x') if x['vs_first'] else '—':>8}")
    print(f"\n估计曲线（实测会覆盖）：{r['estimate_curve']}")
    print(f"北极星：{r['north_star']}")

def main():
    ap = argparse.ArgumentParser(prog="vault.py")
    s = ap.add_subparsers(dest="c", required=True)
    x = s.add_parser("ingest"); x.add_argument("project"); x.add_argument("--dry", action="store_true")
    x.set_defaults(func=c_ingest)
    x = s.add_parser("find"); x.add_argument("vault", choices=["persona","location","prop","beat","codex"])
    x.add_argument("q", nargs="?", default=""); x.add_argument("--limit", type=int, default=10)
    x.set_defaults(func=c_find)
    x = s.add_parser("beat"); x.add_argument("q", nargs="?", default="")
    x.add_argument("--limit", type=int, default=8); x.add_argument("--ensemble", action="store_true")
    x.set_defaults(func=c_beat)
    x = s.add_parser("checkout"); x.add_argument("out"); x.add_argument("--id", required=True)
    x.add_argument("--title", required=True); x.add_argument("--aesthetic", required=True)
    x.add_argument("--persona", nargs="*"); x.add_argument("--location", nargs="*")
    x.add_argument("--prop", nargs="*"); x.add_argument("--idea", default="")
    x.add_argument("--runtime", type=int, default=0); x.add_argument("--aspect", default="21:9")
    x.add_argument("--type", default="short"); x.set_defaults(func=c_checkout)
    x = s.add_parser("codex"); x.add_argument("sub", choices=["log","stats"])
    x.add_argument("mode", nargs="?"); x.add_argument("--project"); x.add_argument("--prompt")
    x.set_defaults(func=c_codex)
    s.add_parser("health").set_defaults(func=c_health)
    s.add_parser("compound").set_defaults(func=c_compound)
    a = ap.parse_args(); a.func(a)

if __name__ == "__main__": main()
