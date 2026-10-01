# -*- coding: utf-8 -*-
"""统一看板：一页看完三套系统的状态。"""
import os, sys, json, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bus"))
import paths as P

CSS = """
:root{--bg:#0f1113;--pn:#171b1f;--ln:#262c32;--fg:#e7e9eb;--dim:#8d959d;--acc:#c86a2e;
--red:#e05252;--yel:#d8a13a;--grn:#4a9d6b;--mono:ui-monospace,Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.65 -apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
header{padding:24px 32px;border-bottom:1px solid var(--ln)}
h1{margin:0;font-size:19px;letter-spacing:.05em}.sub{color:var(--dim);font-size:12px;margin-top:6px}
main{padding:24px 32px 80px;display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;max-width:1240px}
.c{background:var(--pn);border:1px solid var(--ln);border-radius:8px;overflow:hidden}
.c h2{margin:0;padding:13px 17px;font-size:12px;font-weight:600;letter-spacing:.08em;
border-bottom:1px solid var(--ln);color:var(--dim);text-transform:uppercase}
.b{padding:15px 17px}
.kv{display:flex;justify-content:space-between;padding:5px 0;font-size:13px;border-bottom:1px dashed #1f252a}
.kv:last-child{border:0}.kv b{font-weight:600;font-family:var(--mono)}
.big{font-size:30px;font-weight:600;font-family:var(--mono);line-height:1.1}
.cap{color:var(--dim);font-size:11.5px;margin-top:5px}
.g{color:var(--grn)}.y{color:var(--yel)}.r{color:var(--red)}.a{color:var(--acc)}
.bar{height:7px;background:#20262c;border-radius:99px;overflow:hidden;margin-top:7px}
.bar i{display:block;height:100%;background:var(--acc)}
.pill{display:inline-block;font-family:var(--mono);font-size:10px;padding:2px 7px;
border-radius:3px;border:1px solid var(--ln);color:var(--dim);margin:2px 4px 2px 0}
.wide{grid-column:1/-1}
table{width:100%;border-collapse:collapse;font-size:12.5px}
td,th{padding:6px 8px;border-bottom:1px solid #1f252a;text-align:left}
th{color:var(--dim);font-weight:500;font-size:11px}
td.n{font-family:var(--mono);text-align:right}
"""

def _jl(p):
    if not os.path.exists(p): return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def build(project, deck, out="Studio.html"):
    p = P.jload(project) if os.path.exists(project) else {}
    d = P.jload(deck) if os.path.exists(deck) else {"cards": [], "answers": {}}
    pj = p.get("project", {}); st = p.get("_state", {})
    lib = os.path.join(P.LIBR, "library")
    per = _jl(os.path.join(lib, "personas", "roster.jsonl"))
    loc = _jl(os.path.join(lib, "locations", "roster.jsonl"))
    prp = _jl(os.path.join(lib, "props", "roster.jsonl"))
    bts = _jl(os.path.join(lib, "beats", "beats.jsonl"))
    evs = _jl(os.path.join(lib, "codex", "events.jsonl"))
    cm  = P.jload(os.path.join(P.ORCH, "config", "cost-model.json"))
    rt  = P.jload(os.path.join(P.CONS, "config", "risk-table.json"))

    prompts = p.get("prompts", [])
    logs = [x for q in prompts for x in q.get("generation_log", [])]
    passes = sum(1 for q in prompts if any(x["verdict"] == "pass" for x in q.get("generation_log", [])))
    e_att = round(len(logs)/passes, 2) if passes else None
    gates = st.get("gates", {})
    ans = d.get("answers", {}); cards = d.get("cards", [])
    must = [c for c in cards if c["level"] in ("S","A")]
    done = [c for c in must if c["cid"] in ans]
    filled = sum(1 for q in prompts if q.get("beat_refs"))
    hitset = set((p.get("_checkout") or {}).get("hit", []))
    misset = set((p.get("_checkout") or {}).get("miss", []))
    reuse = round(len(hitset)/(len(hitset)+len(misset)), 2) if (hitset or misset) else None

    from collections import Counter
    mc = Counter(e["mode"] for e in evs)
    ev_rows = "".join(f"<tr><td>{html.escape(m)}</td><td class='n'>{n}</td>"
                      f"<td class='n'>{'实测' if n>=15 else '样本不足'}</td></tr>"
                      for m, n in mc.most_common(6)) or "<tr><td colspan=3>尚无事件</td></tr>"
    gate_rows = "".join(
        f"<div class='kv'><span>{g}</span><b class='{'g' if v.get('pass') else 'r'}'>"
        f"{'通过' if v.get('pass') else '未过'}</b></div>" for g, v in gates.items()) or "<div class='cap'>尚未跑门禁</div>"
    bg = Counter(b["genre"] for b in bts)
    genres = "".join(f"<span class='pill'>{g} {n}</span>" for g, n in bg.most_common())
    guess = sum(1 for r in rt["risks"].values() if r.get("n", 0) < 15)

    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(pj.get('title','AI Film Studio'))} · 统一看板</title><style>{CSS}</style></head><body>
<header><h1>{html.escape(pj.get('title','未命名'))} · AI Film Studio 看板</h1>
<div class="sub">{html.escape(pj.get('controlling_idea','（未填控制性理念）'))}</div>
<div class="sub">{pj.get('aspect','')} · {pj.get('type','')} · 美学 {pj.get('aesthetic_id','')} ·
阶段 {st.get('stage','—')}</div></header><main>

<div class="c"><h2>A · 产线</h2><div class="b">
<div class="big">{len(prompts)}</div><div class="cap">条提示词 · {len(p.get('scenes',[]))} 场 ·
目标 {pj.get('target_runtime_sec','?')}s</div>
<div style="margin-top:12px">{gate_rows}</div></div></div>

<div class="c"><h2>B · 决策</h2><div class="b">
<div class="big">{len(done)}<span style="font-size:16px;color:var(--dim)">/{len(must)}</span></div>
<div class="cap">必答卡已决 · 分叉总数 {len(cards)}</div>
<div class="bar"><i style="width:{round(len(done)/max(1,len(must))*100)}%"></i></div>
<div class="kv" style="margin-top:10px"><span>托管卡</span><b>{sum(1 for v in ans.values() if v.get('auto'))}</b></div>
<div class="kv"><span>覆写留痕</span><b class="a">{sum(1 for v in ans.values() if v.get('why') and not v.get('auto'))}</b></div>
</div></div>

<div class="c"><h2>C · 资产库</h2><div class="b">
<div class="big">{len(per)+len(loc)+len(prp)}</div><div class="cap">库中资产 ·
演员 {len(per)} / 场景 {len(loc)} / 道具 {len(prp)}</div>
<div class="kv" style="margin-top:10px"><span>本片复用率</span>
<b class="{'g' if (reuse or 0)>=.55 else 'y'}">{f'{reuse:.0%}' if reuse is not None else '—'}</b></div>
<div class="kv"><span>微节拍句</span><b>{len(bts)}</b></div>
<div style="margin-top:8px">{genres}</div></div></div>

<div class="c"><h2>总线 · 参数流</h2><div class="b">
<div class="kv"><span>E[尝试次数]</span><b class="{'g' if (e_att or 9)<2.2 else 'y'}">{e_att or '—'}</b></div>
<div class="kv"><span>A 成本模型基线</span><b>{cm['baseline_attempts']}{' 实测' if cm.get('_measured') else ' 估计'}</b></div>
<div class="kv"><span>B 风险系数拍脑袋项</span><b class="{'y' if guess else 'g'}">{guess}/{len(rt['risks'])}</b></div>
<div class="kv"><span>微表演已填充</span><b>{filled}/{len(prompts)}</b></div>
<div class="cap" style="margin-top:9px">C 的实测数据单向流向 A 与 B。谁也不许反向写 C。</div></div></div>

<div class="c wide"><h2>失败模式分布（北极星：E[尝试次数] 基线 3.0 → 目标 1.8）</h2><div class="b">
<table><tr><th>模式</th><th style="text-align:right">次数</th><th style="text-align:right">置信度</th></tr>
{ev_rows}</table></div></div>

</main></body></html>"""
    open(out, "w", encoding="utf-8").write(doc)
    return out
