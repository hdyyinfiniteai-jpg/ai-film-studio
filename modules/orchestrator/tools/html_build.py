# -*- coding: utf-8 -*-
"""S6：HTML 分镜表。HOUSE_CSS/JS 固化在此，保证团队标准件一致。"""
import json, html

CSS = """
:root{--bg:#0f1113;--panel:#16191d;--line:#262b31;--fg:#e6e8ea;--dim:#8b949e;
--accent:#c86a2e;--red:#e05252;--yellow:#d8a13a;--green:#4a9d6b;--mono:ui-monospace,"SF Mono",Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.6 -apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
header{padding:20px 28px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:9}
h1{margin:0;font-size:19px;letter-spacing:.04em}
.meta{color:var(--dim);font-size:12px;margin-top:6px}
.bar{display:flex;gap:8px;flex-wrap:wrap;padding:14px 28px;border-bottom:1px solid var(--line)}
.bar input,.bar select{background:var(--panel);border:1px solid var(--line);color:var(--fg);
padding:6px 10px;border-radius:4px;font-size:13px}
main{padding:20px 28px 80px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;margin-bottom:14px;overflow:hidden}
.card h2{margin:0;padding:12px 16px;font-size:13px;font-weight:600;border-bottom:1px solid var(--line);
display:flex;justify-content:space-between;align-items:center;gap:12px}
.tag{font-family:var(--mono);font-size:11px;color:var(--accent);font-weight:400}
.pill{font-size:11px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);color:var(--dim)}
pre{margin:0;padding:16px;white-space:pre-wrap;font-family:var(--mono);font-size:12.5px;line-height:1.75;color:#d3d7db}
.foot{display:flex;gap:14px;padding:10px 16px;border-top:1px solid var(--line);font-size:11px;color:var(--dim);align-items:center}
button{background:transparent;border:1px solid var(--line);color:var(--dim);padding:4px 12px;
border-radius:4px;cursor:pointer;font-size:11px}button:hover{color:var(--fg);border-color:var(--accent)}
.red{color:var(--red)}.yellow{color:var(--yellow)}.green{color:var(--green)}
.hid{display:none}
@media print{body{background:#fff;color:#000}.bar,button{display:none}.card{break-inside:avoid;border-color:#ccc}
pre{color:#000}header{position:static}}
"""

JS = """
function flt(){
 const q=document.getElementById('q').value.trim();
 const s=document.getElementById('sc').value;
 document.querySelectorAll('.card').forEach(c=>{
  const okq=!q||c.innerText.includes(q);
  const oks=!s||c.dataset.scene===s;
  c.classList.toggle('hid',!(okq&&oks));});
}
function cp(b){const t=b.closest('.card').querySelector('pre').innerText;
 navigator.clipboard.writeText(t).then(()=>{b.textContent='已复制';setTimeout(()=>b.textContent='复制提示词',1200)})}
function cpall(){const t=[...document.querySelectorAll('.card:not(.hid) pre')].map(p=>p.innerText).join('\\n\\n———\\n\\n');
 navigator.clipboard.writeText(t).then(()=>alert('已复制 '+document.querySelectorAll('.card:not(.hid)').length+' 条'))}
"""

def build(p, path="Shotlist.html", findings=None, costrep=None):
    pj = p.get("project", {})
    scenes = sorted({str(x["scene"]) for x in p.get("prompts", [])}, key=int)
    parts = []
    for pr in p.get("prompts", []):
        s = next((x for x in p["scenes"] if x["no"] == pr["scene"]), {})
        wd = pr.get("warning_density", {})
        parts.append(f"""
<div class="card" data-scene="{pr['scene']}">
 <h2><span>第{pr['scene']}场 · {html.escape(s.get('slug',''))} <span class="tag">{html.escape(pr['id'])}</span></span>
 <span><span class="pill">{html.escape(pr.get('tag',''))}</span>
 <span class="pill">{pr.get('duration_sec','')}s</span>
 <span class="pill">{pr.get('lens_mm','')}mm</span></span></h2>
 <pre>{html.escape(pr['text_zh'])}</pre>
 <div class="foot"><span>{pr.get('char_count',len(pr['text_zh']))} 字</span>
 <span>镜头 {pr.get('shot_count',1)}</span>
 <span>⚠️ {wd.get('single',0)} / ⚠️⚠️⚠️ {wd.get('triple',0)}</span>
 <span>{html.escape(s.get('value_in',''))} → {html.escape(s.get('value_out',''))}</span>
 <button onclick="cp(this)">复制提示词</button></div>
</div>""")

    fh = ""
    if findings:
        rows = "".join(f"<li class='{ 'red' if f['level']=='红' else 'yellow'}'>[{f['level']}] "
                       f"{html.escape(f['msg'])} — {len(f['prompts'])} 条</li>" for f in findings)
        fh = f"<div class='card'><h2>一致性审计</h2><pre><ul style='margin:0;padding-left:18px'>{rows}</ul></pre></div>"
    ch = ""
    if costrep:
        ch = (f"<div class='card'><h2>成本报告</h2><pre>"
              f"提示词 {costrep['prompt_count']} 条 · 资产图 {costrep['asset_image_count']} 张\n"
              f"E[尝试次数] {costrep['baseline_E_attempts']}\n"
              f"视频预估 ${costrep['video_usd_est']} · 图像预估 ${costrep['image_usd_est']}\n"
              f"合计预估 ${costrep['total_usd_est']} · 实际已花 ${costrep['actual_usd']}\n"
              f"北极星：{costrep['north_star']}</pre></div>")

    opts = "".join(f"<option value='{s}'>第{s}场</option>" for s in scenes)
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(pj.get('title','分镜表'))} · 分镜提示词表</title><style>{CSS}</style></head><body>
<header><h1>{html.escape(pj.get('title','未命名'))} · 分镜提示词表</h1>
<div class="meta">{pj.get('aspect','')} · {pj.get('type','')} · 美学 {pj.get('aesthetic_id','')} ·
共 {len(p.get('prompts',[]))} 条 · 目标 {pj.get('target_runtime_sec','?')}s</div></header>
<div class="bar"><input id="q" placeholder="搜索…" oninput="flt()">
<select id="sc" onchange="flt()"><option value="">全部场次</option>{opts}</select>
<button onclick="cpall()">复制当前全部</button>
<button onclick="window.print()">打印</button></div>
<main>{fh}{ch}{''.join(parts)}</main><script>{JS}</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path
