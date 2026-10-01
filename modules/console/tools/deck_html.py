# -*- coding: utf-8 -*-
"""HTML 决策台。卡片按影响面排序，每个选项挂着后果。点选即记录。"""
import html, json

CSS = """
:root{--bg:#101214;--panel:#181c20;--line:#272d33;--fg:#e7e9eb;--dim:#8d959d;
--acc:#c86a2e;--red:#e05252;--yel:#d8a13a;--grn:#4a9d6b;--mono:ui-monospace,Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.65 -apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
header{padding:22px 30px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:9}
h1{margin:0;font-size:18px;letter-spacing:.05em}
.sub{color:var(--dim);font-size:12px;margin-top:6px}
.bar{display:flex;gap:8px;padding:12px 30px;border-bottom:1px solid var(--line);flex-wrap:wrap;align-items:center}
.bar button{background:transparent;border:1px solid var(--line);color:var(--dim);padding:5px 13px;
border-radius:99px;cursor:pointer;font-size:12px}
.bar button.on{color:var(--fg);border-color:var(--acc);background:rgba(200,106,46,.1)}
main{padding:22px 30px 90px;max-width:900px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;margin-bottom:16px;overflow:hidden}
.card.answered{opacity:.55}
.chd{padding:14px 18px;border-bottom:1px solid var(--line)}
.lv{display:inline-block;font-family:var(--mono);font-size:10px;padding:2px 7px;border-radius:3px;
border:1px solid var(--line);color:var(--dim);margin-right:8px}
.lv.S{color:var(--acc);border-color:var(--acc)}.lv.A{color:var(--red);border-color:var(--red)}
.lv.B{color:var(--yel);border-color:var(--yel)}
.locked{font-size:11px;color:var(--dim);font-family:var(--mono)}
.q{font-size:15px;font-weight:600;margin:8px 0 0}
.opt{padding:13px 18px;border-top:1px solid var(--line);cursor:pointer}
.opt:hover{background:rgba(255,255,255,.025)}
.opt.sel{background:rgba(200,106,46,.1);border-left:2px solid var(--acc)}
.ol{font-weight:600;font-size:13.5px}.ow{color:var(--dim);font-size:12.5px;margin-top:3px}
.tags{margin-top:7px;display:flex;gap:7px;flex-wrap:wrap}
.t{font-family:var(--mono);font-size:10.5px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);color:var(--dim)}
.t.hi{color:var(--red);border-color:var(--red)}.t.md{color:var(--yel);border-color:var(--yel)}
.t.lo{color:var(--grn);border-color:var(--grn)}
.t.guess{color:#7a6a4a;border-color:#5a4d36}
.note{color:#b08a5a;font-size:12px;margin-top:5px}
.rec{padding:11px 18px;border-top:1px solid var(--line);font-size:12.5px;color:var(--acc);background:rgba(200,106,46,.05)}
.meta{padding:9px 18px;border-top:1px solid var(--line);font-size:11px;color:var(--dim);font-family:var(--mono)}
.hid{display:none}
@media print{body{background:#fff;color:#000}.bar{display:none}.card{break-inside:avoid;border-color:#ccc}}
"""

JS = """
const A=JSON.parse(document.getElementById('ans').textContent);
function pick(cid,k,el){
 A[cid]=k; el.parentNode.querySelectorAll('.opt').forEach(o=>o.classList.remove('sel'));
 el.classList.add('sel'); el.closest('.card').classList.add('answered');
 document.getElementById('cnt').textContent=Object.keys(A).length;
}
function flt(l,b){document.querySelectorAll('.bar button').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');
 document.querySelectorAll('.card').forEach(c=>c.classList.toggle('hid',l!=='*'&&c.dataset.lv!==l));}
function exp(){const o=[];document.querySelectorAll('.card').forEach(c=>{
 const k=A[c.dataset.cid]; if(k) o.push(c.dataset.cid+' = '+k);});
 navigator.clipboard.writeText(o.map(x=>'console.py answer '+x.replace(' = ',' ')).join('\\n'))
 .then(()=>alert('已复制 '+o.length+' 条作答命令，粘进终端即可落盘'));}
"""

def build(p, deck, path="DecisionDeck.html"):
    ans = deck.get("answers", {})
    cs = deck.get("cards", [])
    parts = []
    for c in cs:
        a = ans.get(c["cid"], {})
        opts = []
        for o in c["opts"]:
            rl = {"高":"hi","中":"md","低":"lo"}.get(o["risk_level"], "")
            cd = o["cost_delta"]
            tags = (f"<span class='t'>成本 {'+' if cd>=0 else ''}${cd}</span>"
                    f"<span class='t {rl}'>抽卡风险 {o['risk_level']}</span>")
            if o["risk_conf"] == "拍脑袋":
                tags += "<span class='t guess'>置信度：拍脑袋（样本&lt;15）</span>"
            note = f"<div class='note'>代价：{html.escape(o['note'])}</div>" if o.get("note") else ""
            sel = " sel" if a.get("k") == o["k"] else ""
            opts.append(f"""<div class="opt{sel}" onclick="pick('{c['cid']}','{o['k']}',this)">
<div class="ol">{o['k']}) {html.escape(o['label'])}</div>
<div class="ow">{html.escape(o['why'])}</div>
<div class="tags">{tags}</div>{note}</div>""")
        rk, rw = None, ""
        try:
            import cards as C; rk, rw = C.recommend(c, p)
        except Exception: pass
        rec = f"<div class='rec'>【推荐】{rk} —— {html.escape(rw)}</div>" if rk else ""
        note = f"<div class='rec' style='color:var(--dim);background:none'>{html.escape(c['note'])}</div>" if c.get("note") else ""
        where = f"第{c['scene']}场 {html.escape(c['slug'])}" if c["scene"] else "全片策略"
        lock = f" · 已答 {a.get('k')}" + ("（托管）" if a.get("auto") else "") if a else ""
        parts.append(f"""<div class="card{' answered' if a else ''}" data-cid="{c['cid']}" data-lv="{c['level']}">
<div class="chd"><span class="lv {c['level']}">{c['level']}</span>
<span class="locked">{c['cid']} · {where} · 影响面 {c['impact']} · 成本跨度 ±${c['cost_spread']}{lock}</span>
<div class="q">{html.escape(c['q'])}</div></div>
{''.join(opts)}{rec}{note}</div>""")

    pj = p.get("project", {})
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(pj.get('title','决策台'))} · 导演决策台</title><style>{CSS}</style></head><body>
<header><h1>{html.escape(pj.get('title','未命名'))} · 导演决策台</h1>
<div class="sub">控制性理念：{html.escape(pj.get('controlling_idea','（未填）'))}</div>
<div class="sub">分叉 {len(cs)} · 已决 <span id="cnt">{len(ans)}</span> ·
系统穷举选项并预判后果，但不替你选</div></header>
<div class="bar">
<button class="on" onclick="flt('*',this)">全部</button>
<button onclick="flt('S',this)">S 策略</button>
<button onclick="flt('A',this)">A 必答</button>
<button onclick="flt('B',this)">B 托管</button>
<button onclick="flt('C',this)">C 自动</button>
<button onclick="exp()">导出作答命令</button>
<button onclick="window.print()">打印</button></div>
<main>{''.join(parts)}</main>
<script id="ans" type="application/json">{json.dumps({k:v['k'] for k,v in ans.items()})}</script>
<script>{JS}</script></body></html>"""
    open(path, "w", encoding="utf-8").write(doc)
    return path
