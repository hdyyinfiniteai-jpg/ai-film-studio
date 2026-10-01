# -*- coding: utf-8 -*-
"""入库：把一部片的 project.json 拆成可跨项目复用的原子件。
   纪律：只入库『去项目化』的部分——角色本体入库，本片的场次归属不入库。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def _match(rows, desc, name, thr=0.88):
    for r in rows:
        if name and r.get("name") == name: return r, 1.0
        s = lib.sim(r.get("handle_desc_zh",""), desc)
        if s >= thr: return r, s
    return None, 0.0

def run(project_path, dry=False):
    p = json.load(open(project_path, encoding="utf-8"))
    pid = p["project"]["id"]; report = {"new":[], "merged":[], "skipped":[]}

    for key, vault, prefix in (("cast","persona","PV"), ("locations","location","LV"), ("props","prop","PP")):
        rows = lib.load(vault)
        for it in p.get(key, []):
            desc = it.get("handle_desc_zh","")
            if not desc:
                report["skipped"].append((vault, it["id"], "无句柄描述")); continue
            hit, s = _match(rows, desc, it.get("name"))
            if hit:
                hit.setdefault("used_in", [])
                if pid not in hit["used_in"]: hit["used_in"].append(pid)
                hit["last_seen"] = lib.today()
                report["merged"].append((vault, it["id"], hit["id"], round(s,3)))
                continue
            rec = {"id": it.get("persona_vault_ref") or lib.next_id(vault, prefix),
                   "name": it.get("name", it["id"]), "src_id": it["id"],
                   "handle_desc_zh": desc, "used_in": [pid],
                   "first_seen": lib.today(), "last_seen": lib.today()}
            if vault == "persona":
                rec.update({"core_lock": it.get("core_lock",""),
                            "voice_prompt": it.get("voice_prompt",""),
                            "voice_identity": it.get("voice_identity", {}),
                            "states": it.get("states", []),
                            "asset_specs": it.get("asset_specs", [])})
            if vault == "location":
                rec.update({"type": it.get("type",""), "views": it.get("views", {}),
                            "light_profile": it.get("light_profile", {}),
                            "palette": it.get("palette", []),
                            "asset_specs": it.get("asset_specs", [])})
            if vault == "prop":
                rec.update({"asset_specs": it.get("asset_specs", [])})
            rows.append(rec); report["new"].append((vault, it["id"], rec["id"]))
        if not dry: lib.save(vault, rows)

    # 美学：本片美学若不在模板库中，入库
    a = p.get("aesthetic", {})
    if a.get("id"):
        T = lib.aesthetics()
        if not any(t["id"] == a["id"] for t in T["templates"]):
            T["templates"].append({k: a[k] for k in a if not k.startswith("_")})
            if not dry:
                json.dump(T, open(os.path.join(lib.LIB,"aesthetics","templates.json"),"w",encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            report["new"].append(("aesthetic", a["id"], a["id"]))

    # 生成日志 → codex events
    for pr in p.get("prompts", []):
        for e in pr.get("generation_log", []):
            if e.get("verdict") == "fail" and e.get("failure_mode"):
                if not dry:
                    lib.add("events", {"project": pid, "prompt": pr["id"],
                                       "mode": e["failure_mode"], "at": lib.today()})
                report["new"].append(("event", pr["id"], e["failure_mode"]))
    return report
