#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-film-studio · 统一工作流

  new       从资产库借出，建新项目（C）
  compile   场次编译 S1–S4 + 门禁 G1–G4（A）
  decide    穷举分叉、分流、托管（B）
  build     决策回写 → S5 → 微表演填充 → G5（A+B+C）
  ship      出货：HTML 分镜表 + 提示词包 + 成本报告（A）
  close     资产回库 + 参数同步（C→A/B）
  flow      全流程一条命令
  board     统一看板
  sync      只跑参数同步

融合的实质是三件事，不是三个 CLI 拼一起：
  1. 参数总线：C 的实测数据单向流向 A 的成本模型与 B 的风险系数
  2. 微表演接合：A 故意留空的槽位，由 C 的句库 + B 的决策共同填上
  3. 单一 project.json：三套系统读写同一份状态，没有导入导出
"""
import sys, os, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bus"))
import paths as P

def ok(m): print(f"✔ {m}")
def warn(m): print(f"▲ {m}")
def bad(m): print(f"✖ {m}")
def hr(t): print(f"\n{'='*62}\n▶ {t}\n{'='*62}")

def _run(mod, script, args, cwd=None):
    cmd = [sys.executable, os.path.join(mod, "tools", script)] + args
    return subprocess.run(cmd, cwd=cwd or os.getcwd())

# ---------------- 阶段 ----------------
def c_new(a):
    hr("新建 · 从资产库借出（studio-library）")
    args = [os.path.abspath(a.file), "--id", a.id, "--title", a.title,
            "--aesthetic", a.aesthetic, "--idea", a.idea,
            "--runtime", str(a.runtime), "--type", a.type, "--aspect", a.aspect]
    for k, v in (("--persona", a.persona), ("--location", a.location), ("--prop", a.prop)):
        if v: args += [k] + v
    r = _run(P.LIBR, "vault.py", ["checkout"] + args)
    if r.returncode: sys.exit(r.returncode)
    print("\n下一步：往 project.json 填 scenes[]，然后 studio.py compile")

def c_compile(a):
    hr("编译 · 场次数据与门禁（orchestrator S1–S4）")
    p = P.jload(a.file); p.setdefault("_state", {})["stage"] = "S0"; P.jsave(p, a.file)
    for st in ("S0", "S1", "S2", "S3", "S4"):
        r = _run(P.ORCH, "pipeline.py", ["--file", os.path.abspath(a.file), "run", st])
        if r.returncode == 2:
            bad(f"门禁停机于 {st}。修复后重跑 studio.py compile"); sys.exit(2)

def c_decide(a):
    hr("决策 · 导演在场（director-console）")
    d = os.path.abspath(a.deck); f = os.path.abspath(a.file)
    _run(P.CONS, "console.py", ["--file", f, "--deck", d, "deal"])
    if a.auto:
        _run(P.CONS, "console.py", ["--file", f, "--deck", d, "auto"])
        warn("已批量托管。策略卡（S级）建议人工作答后重跑 decide —— 托管值只是占位")
    print(f"\n作答：{sys.executable} {os.path.join(P.CONS,'tools','console.py')} "
          f"--file {f} --deck {d} answer <cid> <A|B>")

def c_build(a):
    hr("生产 · 决策回写 → 提示词 → 微表演填充 → 出货门")
    f = os.path.abspath(a.file); d = os.path.abspath(a.deck)
    if os.path.exists(d):
        args = ["--file", f, "--deck", d, "apply"] + (["--prune"] if a.prune else [])
        _run(P.CONS, "console.py", args)
    else:
        warn("无决策卡组，跳过回写（纯自动化模式）")
    r = _run(P.ORCH, "pipeline.py", ["--file", f, "run", "S5"])
    if r.returncode == 2:
        warn("G5 未过，先填微表演再复检")
    import enrich
    n, missed, used = enrich.run(f, a.genre)
    ok(f"微表演填充 {n} 条（句库 {len(used)} 句，本片内不重复）")
    for pid, emo, shot, gen in missed[:6]:
        warn(f"  {pid} 未命中：{emo}·{shot}·{gen} —— 这是句库该补的缺口")
    r = _run(P.ORCH, "pipeline.py", ["--file", f, "gate", "G5"])
    if r.returncode: bad("G5 出货门未通过"); sys.exit(2)
    ok("G5 出货门通过")

def c_ship(a):
    hr("出货 · 分镜表 + 提示词包 + 成本报告")
    _run(P.ORCH, "pipeline.py", ["--file", os.path.abspath(a.file),
                                 "--out", os.path.abspath(a.out), "run", "S6"])

def c_close(a):
    hr("收尾 · 资产回库 + 参数同步")
    _run(P.LIBR, "vault.py", ["ingest", os.path.abspath(a.file)])
    c_sync(a)
    _run(P.LIBR, "vault.py", ["compound"])

def c_sync(a):
    import sync
    projs = [os.path.abspath(a.file)]
    if a.also: projs += [os.path.abspath(x) for x in a.also]
    modes, e_att, att, ps = sync.collect(projs)
    print(f"\n事件 {sum(modes.values())} 条 · 生成 {att} 次 / 通过 {ps} 条"
          + (f" · E[尝试次数] {e_att}" if e_att else " · 样本不足，E[尝试] 仍用基线"))
    for line in sync.apply(modes, e_att, a.dry): print("  " + line)
    ok("参数总线已同步（C → A/B，单向）")
    if os.path.exists(a.deck):
        warn("决策卡组是同步前的快照 —— 重跑 studio.py decide 才会读到新系数")

def c_flow(a):
    for fn in (c_compile, c_decide, c_build, c_ship, c_close):
        fn(a)
    ok("\n全流程跑通。")

def c_board(a):
    import dashboard
    p = dashboard.build(a.file, a.deck, a.out_html)
    ok(f"看板 → {p}")

def main():
    ap = argparse.ArgumentParser(prog="studio.py")
    ap.add_argument("--file", default="project.json")
    ap.add_argument("--deck", default="deck.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--out-html", default="Studio.html")
    ap.add_argument("--genre", default="通用", help="微表演句库检索类型：通用/古装/喜剧/都市/悬疑")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--also", nargs="*", help="参数同步时一并统计的其他 project.json")
    s = ap.add_subparsers(dest="c", required=True)
    x = s.add_parser("new"); x.add_argument("--id", required=True); x.add_argument("--title", required=True)
    x.add_argument("--aesthetic", required=True); x.add_argument("--idea", default="")
    x.add_argument("--runtime", type=int, default=0); x.add_argument("--type", default="short")
    x.add_argument("--aspect", default="21:9"); x.add_argument("--persona", nargs="*")
    x.add_argument("--location", nargs="*"); x.add_argument("--prop", nargs="*")
    x.set_defaults(func=c_new)
    s.add_parser("compile").set_defaults(func=c_compile)
    x = s.add_parser("decide"); x.add_argument("--auto", action="store_true"); x.set_defaults(func=c_decide)
    x = s.add_parser("build"); x.add_argument("--prune", action="store_true"); x.set_defaults(func=c_build)
    s.add_parser("ship").set_defaults(func=c_ship)
    s.add_parser("close").set_defaults(func=c_close)
    s.add_parser("sync").set_defaults(func=c_sync)
    x = s.add_parser("flow"); x.add_argument("--auto", action="store_true")
    x.add_argument("--prune", action="store_true"); x.set_defaults(func=c_flow)
    s.add_parser("board").set_defaults(func=c_board)
    a = ap.parse_args()
    for k, d in (("auto", False), ("prune", False)):
        if not hasattr(a, k): setattr(a, k, d)
    a.func(a)

if __name__ == "__main__": main()
