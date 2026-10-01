# -*- coding: utf-8 -*-
"""借出：新片开局时，从库里预填 project.json。复利就发生在这一步。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def _to_cast(r):
    return {"id": r.get("src_id") or r["id"].lower(), "name": r.get("name"),
            "persona_vault_ref": r["id"], "core_lock": r.get("core_lock",""),
            "voice_prompt": r.get("voice_prompt",""),
            "voice_identity": r.get("voice_identity", {}),
            "handle_desc_zh": r["handle_desc_zh"], "states": r.get("states", []),
            "asset_specs": r.get("asset_specs", [])}

def _to_loc(r):
    return {"id": r.get("src_id") or r["id"].lower(), "name": r.get("name"),
            "vault_ref": r["id"], "type": r.get("type",""),
            "handle_desc_zh": r["handle_desc_zh"], "views": r.get("views", {}),
            "light_profile": r.get("light_profile", {}), "palette": r.get("palette", []),
            "asset_specs": r.get("asset_specs", [])}

def _to_prop(r):
    return {"id": r.get("src_id") or r["id"].lower(), "name": r.get("name"),
            "vault_ref": r["id"], "handle_desc_zh": r["handle_desc_zh"],
            "asset_specs": r.get("asset_specs", [])}

def run(out_path, title, pid, aesthetic_id, personas=(), locations=(), props=(),
        idea="", runtime=0, aspect="21:9", ptype="short"):
    T = lib.aesthetics()
    tpl = next((t for t in T["templates"] if t["id"] == aesthetic_id), None)
    if not tpl: raise SystemExit(f"✖ 美学模板 {aesthetic_id} 不在库中")
    aes = dict(tpl)
    aes["forbid_block"] = list(dict.fromkeys(T["_shared_forbid_block"] + tpl["light_doctrine"]["forbidden"]))

    idx = {v: {r["id"]: r for r in lib.load(v)} for v in ("persona","location","prop")}
    hit, miss = [], []
    cast, locs, prs = [], [], []
    for ids, v, conv, box in ((personas,"persona",_to_cast,cast),
                              (locations,"location",_to_loc,locs),
                              (props,"prop",_to_prop,prs)):
        for i in ids:
            r = idx[v].get(i)
            if r: box.append(conv(r)); hit.append((v, i))
            else: miss.append((v, i))

    p = {"project":{"id":pid,"title":title,"type":ptype,"target_runtime_sec":runtime,
                    "aspect":aspect,"aesthetic_id":aesthetic_id,"controlling_idea":idea},
         "aesthetic": aes, "cast": cast, "locations": locs, "props": prs,
         "scenes": [], "prompts": [], "_state":{"stage":"S0","gates":{},"log":[]},
         "_checkout":{"from_library": True, "hit":[h[1] for h in hit], "miss":[m[1] for m in miss]}}
    json.dump(p, open(out_path,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    return hit, miss, aes
