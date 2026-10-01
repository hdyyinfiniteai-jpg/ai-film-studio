# -*- coding: utf-8 -*-
"""总线：三个模块的路径解析。融合的前提是它们共享同一份 project.json。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "modules")
ORCH = os.path.join(M, "orchestrator")
CONS = os.path.join(M, "console")
LIBR = os.path.join(M, "library")

def use(mod):
    """把某模块的 tools 目录压到 sys.path 首位（模块内部用平铺 import）"""
    t = os.path.join(mod, "tools")
    while t in sys.path: sys.path.remove(t)
    sys.path.insert(0, t)
    return t

def purge(*mods):
    """清掉已加载的模块，避免三方同名模块互相污染"""
    names = set()
    for mod in mods:
        d = os.path.join(mod, "tools")
        if os.path.isdir(d):
            names |= {f[:-3] for f in os.listdir(d) if f.endswith(".py")}
    for n in names:
        sys.modules.pop(n, None)

def jload(p):  return json.load(open(p, encoding="utf-8"))
def jsave(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
