# -*- coding: utf-8 -*-
"""检索 DSL。key=value 用逗号分隔；文本自由词做子串匹配。
   例：beat emotion=压抑,intensity=3,genre=古装
       persona 瘦高
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def parse(q):
    kv, free = {}, []
    for tok in (q or "").replace("，", ",").split(","):
        tok = tok.strip()
        if not tok: continue
        if "=" in tok:
            k, v = tok.split("=", 1); kv[k.strip()] = v.strip()
        else: free.append(tok)
    return kv, free

def _coerce(v):
    if v in ("true","True"): return True
    if v in ("false","False"): return False
    try: return int(v)
    except Exception: return v

def run(vault, q, limit=10):
    kv, free = parse(q)
    rows = lib.load(vault)
    out = []
    for r in rows:
        if any(r.get(k) != _coerce(v) for k, v in kv.items()): continue
        blob = " ".join(str(x) for x in r.values())
        if free and not all(w in blob for w in free): continue
        out.append(r)
    return out[:limit]
