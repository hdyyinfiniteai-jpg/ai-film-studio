# -*- coding: utf-8 -*-
"""共享层：路径、读写、状态机定义。所有模块只经此访问 project.json。"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG  = os.path.join(ROOT, "config")

STAGES = ["S0","S1","S2","S3","S4","S5","S6","S7"]
STAGE_NAME = {
    "S0":"立项 · 美学与目标锁定",
    "S1":"故事 · 场次编译（SCREENWRITER）",
    "S2":"选角 · 角色锁与声纹（ACTING）",
    "S3":"资产 · 规格铸造（LIRA）",
    "S4":"分镜 · 走位与情绪轨迹（SHOTLIST）",
    "S5":"提示词 · 生成（SEEDANCE）",
    "S6":"出货 · HTML分镜表 + 提示词包 + 成本报告",
    "S7":"回填 · 失败学与成本核算",
}
GATE_AFTER = {"S1":["G1","G2"], "S3":["G3"], "S4":["G4"], "S5":["G5"]}

def cfg(name):
    with open(os.path.join(CFG, name), encoding="utf-8") as f:
        return json.load(f)

def load(path="project.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save(p, path="project.json"):
    p.setdefault("_meta", {})["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def state(p):
    return p.setdefault("_state", {"stage":"S0", "gates":{}, "log":[]})

def logline(p, msg):
    state(p)["log"].append(f"{datetime.datetime.now().strftime('%m-%d %H:%M')} {msg}")

def die(msg, code=1):
    print(f"✖ {msg}", file=sys.stderr); sys.exit(code)

def ok(msg):    print(f"✔ {msg}")
def warn(msg):  print(f"▲ {msg}")
def bad(msg):   print(f"✖ {msg}")

def find_scene(p, no):
    for s in p.get("scenes", []):
        if s["no"] == no: return s
    return None

def aesthetic(p):
    return p.get("aesthetic") or {}
