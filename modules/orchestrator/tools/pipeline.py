#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""film-pipeline-orchestrator · 状态机主控

  init      建项目骨架
  status    当前阶段 / 门禁状态
  run S1..S7  执行某阶段
  gate G1..G5 单跑某道门
  advance   过门则推进到下一阶段（门禁不过则拒绝）
  all       从当前阶段一路跑到底，遇门禁失败停机

设计纪律：
  · 门禁只判定，不修改内容
  · 审计只报不改（自动改写会引入新的不一致，且人会停止思考）
  · 每次 run 都写回 project.json，随时可中断续跑
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (STAGES, STAGE_NAME, GATE_AFTER, load, save, state,
                    logline, cfg, ok, warn, bad, die)
import timing, shootability, emotion, density, promptbuild, gates, cost, html_build

# ---------------- 阶段实现 ----------------
def S0(p, args):
    """立项：锁美学模板、画幅、目标片长"""
    aid = p["project"].get("aesthetic_id")
    tpl = next((t for t in cfg("aesthetic-templates.json")["templates"] if t["id"] == aid), None)
    if not tpl: die(f"美学模板 {aid} 不存在（见 config/aesthetic-templates.json）")
    shared = cfg("aesthetic-templates.json")["_shared_forbid_block"]
    p["aesthetic"] = dict(tpl)
    fb = list(dict.fromkeys(shared + tpl["light_doctrine"]["forbidden"]))  # 去重：禁令重复会白吃注意力预算
    p["aesthetic"]["forbid_block"] = fb
    ok(f"美学锁定：{tpl['name']} · 色板 {'/'.join(tpl['palette_60_30_10'])}")
    ok(f"焦距教条：{tpl['lens_doctrine']}")
    return True

def S1(p, args):
    """故事：计秒 + 可拍审计 + 情绪轨迹推导（三遍编译的第三遍）"""
    for s in p.get("scenes", []):
        if s.get("beats") and not s.get("timing_sec_locked"):
            sec, _ = timing.scene_seconds(s); s["timing_sec"] = sec
        r = shootability.audit_scene(s)
        if not r["passed"]:
            for f in r["flags"]:
                bad(f"第{s['no']}场 [{f['code']}] 命中「{f['hit']}」")
                print(f"    原因：{f['why']}")
                print(f"    改写：{f['fix']}")
        good, msg = emotion.build_track(s)
        (ok if good else warn)(f"第{s['no']}场 {s.get('timing_sec','?')}s · {msg}")
    ok(f"全片 {timing.project_runtime(p)}s / 目标 {p['project'].get('target_runtime_sec','?')}s")
    return True

def S2(p, args):
    """选角：core_lock 与 voice_prompt 双锁。优先命中 Persona Vault。"""
    for c in p.get("cast", []):
        src = "Persona Vault" if c.get("persona_vault_ref") else "本片新建"
        miss = [k for k in ("core_lock","voice_prompt","handle_desc_zh") if not c.get(k)]
        (ok if not miss else warn)(f"{c['id']} · {src}" + (f" · 缺 {miss}" if miss else " · 双锁齐备"))
    return True

def S3(p, args):
    """资产：为缺规格的资产生成 LIRA 规格占位（模型路由由类型决定）"""
    ROUTE = {"cast":"soul-cinema", "locations":"soul-cinema", "props":"nano-banana-pro"}
    asp = p["project"].get("aspect", "16:9")
    n = 0
    for key in ("cast","locations","props"):
        for it in p.get(key, []):
            if it.get("asset_specs"): continue
            base = {"model": ROUTE[key], "aspect": asp,
                    "views": 2 if key == "locations" else 1,
                    "prompt": f"[LIRA 80–150词待填] {it.get('handle_desc_zh','')[:60]}"}
            specs = [base]
            for v in it.get("states", [])[1:]:
                specs.append(dict(base, variant=v))
            it["asset_specs"] = specs; n += len(specs)
    ok(f"生成 {n} 条资产规格占位（模型已路由，提示词待 LIRA 填充）")
    # 覆盖度 gap
    need = {}
    for s in p.get("scenes", []):
        for cid in s.get("cast_present", []) + s.get("props_present", []) + [s.get("location_id")]:
            if cid: need.setdefault(cid, []).append(s["no"])
    have = {x["id"] for k in ("cast","locations","props") for x in p.get(k, [])}
    gap = {k: v for k, v in need.items() if k not in have}
    if gap: warn(f"资产缺口（场次引用但库中无）：{gap}")
    else:   ok("场次×资产覆盖度无缺口")
    return True

def S4(p, args):
    """分镜：密度计算 + 走位图检查"""
    for s in p.get("scenes", []):
        n, reasons = density.compute(s)
        s["planned_prompt_count"] = n
        ok(f"第{s['no']}场 {s.get('timing_sec')}s → {n} 条  ({'; '.join(reasons[1:-1]) or '无触发器'})")
        if len(s.get("cast_present", [])) >= 2 and not s.get("blocking_svg"):
            warn(f"  第{s['no']}场 缺走位俯视图（G4 将拦截）")
    return True

def S5(p, args):
    """提示词：五段式编译"""
    out = []
    for s in p.get("scenes", []):
        prs, _ = promptbuild.build_scene_prompts(p, s)
        out += prs
    p["prompts"] = out
    ok(f"生成 {len(out)} 条提示词，平均 {round(sum(len(x['text_zh']) for x in out)/max(1,len(out)))} 字")
    return True

def S6(p, args):
    """出货：HTML 分镜表 + 提示词包 + 成本报告"""
    from audit import run as arun
    f = arun(p); c = cost.report(p)
    outdir = args.out or "out"
    os.makedirs(os.path.join(outdir, "prompts"), exist_ok=True)
    for pr in p["prompts"]:
        with open(os.path.join(outdir, "prompts", pr["id"] + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(pr["text_zh"])
    html_build.build(p, os.path.join(outdir, "Shotlist.html"), f, c)
    with open(os.path.join(outdir, "cost_report.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=2)
    ok(f"提示词包 {len(p['prompts'])} 条 → {outdir}/prompts/")
    ok(f"分镜表 → {outdir}/Shotlist.html")
    ok(f"成本报告 → {outdir}/cost_report.json  预估 ${c['total_usd_est']}")
    return True

def S7(p, args):
    """回填：统计失败模式与 E[尝试次数]"""
    logs = [(q["id"], x) for q in p.get("prompts", []) for x in q.get("generation_log", [])]
    if not logs:
        warn("尚无 generation_log。用 `pipeline.py log <prompt_id> pass|fail <mode>` 回填"); return True
    from collections import Counter
    c = Counter(x["failure_mode"] for _, x in logs if x["verdict"] == "fail" and x.get("failure_mode"))
    passes = sum(1 for q in p["prompts"] if any(x["verdict"] == "pass" for x in q.get("generation_log", [])))
    ok(f"E[尝试次数] = {round(len(logs)/max(1,passes),2)}（样本 {len(logs)} 次 / 通过 {passes} 条）")
    for m, n in c.most_common():
        print(f"    {m:24s} {n:3d} 次  {'█'*min(n,30)}")
    if len(logs) >= 20:
        ok("样本 ≥20，成本模型已切换为实测值")
    return True

RUN = {"S0":S0,"S1":S1,"S2":S2,"S3":S3,"S4":S4,"S5":S5,"S6":S6,"S7":S7}

# ---------------- 门禁 ----------------
def run_gates(p, stage, strict=True):
    allp = True
    for gid in GATE_AFTER.get(stage, []):
        passed, res = gates.run(p, gid)
        g = cfg("gates.json")[gid]
        print(f"\n── 门禁 {gid} {g['name']} ──")
        for r in res:
            (ok if r["pass"] else bad)(f"{r['check']}: {r['detail']}")
        state(p)["gates"][gid] = {"pass": passed, "detail": res}
        if not passed:
            allp = False
            bad(f"{gid} {g['name']} 未通过 —— 停机")
        else:
            ok(f"{gid} {g['name']} 通过")
    return allp

# ---------------- CLI ----------------
def cmd_init(a):
    p = {"project":{"id":a.id,"title":a.title,"type":a.type,
                    "target_runtime_sec":a.runtime,"aspect":a.aspect,
                    "aesthetic_id":a.aesthetic,"controlling_idea":a.idea or ""},
         "aesthetic":{}, "cast":[], "locations":[], "props":[], "scenes":[], "prompts":[],
         "_state":{"stage":"S0","gates":{},"log":[]}}
    save(p, a.file); ok(f"已建 {a.file}（阶段 S0）")

def cmd_status(a):
    p = load(a.file); st = state(p)
    print(f"项目：{p['project'].get('title')}  阶段：{st['stage']} {STAGE_NAME[st['stage']]}")
    print(f"场次 {len(p.get('scenes',[]))} · 角色 {len(p.get('cast',[]))} · 提示词 {len(p.get('prompts',[]))}")
    for gid, v in st.get("gates", {}).items():
        print(("  ✔ " if v["pass"] else "  ✖ ") + gid + " " + cfg("gates.json")[gid]["name"])

def cmd_run(a):
    p = load(a.file); st = state(p)
    stg = a.stage or st["stage"]
    print(f"▶ {stg} {STAGE_NAME[stg]}\n")
    RUN[stg](p, a)
    passed = run_gates(p, stg)
    logline(p, f"run {stg} gates={'pass' if passed else 'FAIL'}")
    if passed and STAGES.index(stg) < len(STAGES)-1:
        st["stage"] = STAGES[STAGES.index(stg)+1]
        print(f"\n→ 推进至 {st['stage']} {STAGE_NAME[st['stage']]}")
    save(p, a.file)
    sys.exit(0 if passed else 2)

def cmd_gate(a):
    p = load(a.file); passed, res = gates.run(p, a.gid)
    for r in res: (ok if r["pass"] else bad)(f"{r['check']}: {r['detail']}")
    sys.exit(0 if passed else 2)

def cmd_all(a):
    p = load(a.file); st = state(p)
    i = STAGES.index(st["stage"])
    for stg in STAGES[i:]:
        print(f"\n{'='*58}\n▶ {stg} {STAGE_NAME[stg]}\n{'='*58}")
        RUN[stg](p, a)
        if not run_gates(p, stg):
            st["stage"] = stg; save(p, a.file)
            bad(f"\n停机于 {stg}。修复后重跑：pipeline.py run {stg}")
            sys.exit(2)
        if STAGES.index(stg) < len(STAGES)-1:
            st["stage"] = STAGES[STAGES.index(stg)+1]
        save(p, a.file)
    ok("\n全片跑通。")

def cmd_log(a):
    p = load(a.file)
    pr = next((x for x in p["prompts"] if x["id"] == a.prompt_id), None)
    if not pr: die(f"无提示词 {a.prompt_id}")
    lg = pr.setdefault("generation_log", [])
    lg.append({"attempt": len(lg)+1, "model": a.model, "verdict": a.verdict,
               "failure_mode": a.mode, "note": a.note or ""})
    if a.verdict == "pass":
        pr["cost"] = {"attempts": len(lg), "usd": round(len(lg)*cfg("cost-model.json")["unit_cost_usd"]["video_15s"],2)}
    save(p, a.file); ok(f"{a.prompt_id} 第{len(lg)}次 {a.verdict} {a.mode or ''}")

def main():
    ap = argparse.ArgumentParser(prog="pipeline.py")
    ap.add_argument("--file", default="project.json")
    ap.add_argument("--out", default="out")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("--id", required=True); i.add_argument("--title", required=True)
    i.add_argument("--type", default="feature"); i.add_argument("--runtime", type=int, default=0)
    i.add_argument("--aspect", default="21:9"); i.add_argument("--aesthetic", required=True)
    i.add_argument("--idea", default=""); i.set_defaults(func=cmd_init)
    s = sub.add_parser("status"); s.set_defaults(func=cmd_status)
    r = sub.add_parser("run"); r.add_argument("stage", nargs="?", choices=STAGES); r.set_defaults(func=cmd_run)
    g = sub.add_parser("gate"); g.add_argument("gid", choices=["G1","G2","G3","G4","G5"]); g.set_defaults(func=cmd_gate)
    a = sub.add_parser("all"); a.set_defaults(func=cmd_all)
    l = sub.add_parser("log"); l.add_argument("prompt_id"); l.add_argument("verdict", choices=["pass","fail"])
    l.add_argument("mode", nargs="?"); l.add_argument("--model", default="seedance-2.0")
    l.add_argument("--note", default=""); l.set_defaults(func=cmd_log)
    args = ap.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
