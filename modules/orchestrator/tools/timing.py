# -*- coding: utf-8 -*-
"""节拍计秒。中文语速常数 —— 原俄语常数不适用中文，偏差可达20%。"""
import re
from common import cfg

T = cfg("zh-timing.json")

_PUNCT = set(" \t\n，。！？、；：（）《》…—.,!?;:\"'()[]“”‘’")

def _strip(t):
    return "".join(c for c in t if c not in _PUNCT)

def dialogue_sec(text, mode="normal"):
    n = len(_strip(text))
    return round(n / T["speech_rate_cps"].get(mode, 4.5), 2)

def scene_seconds(scene):
    """scene['beats'] = [{'type':'dialogue','text':..,'mode':..} | {'type':'action','text':..}
                         | {'type':'silence'|'beat_pause'|'comedy_hold'|'entrance_exit'|'transition'}]"""
    nd = T["non_dialogue_sec"]; total = 0.0; detail = []
    for b in scene.get("beats", []):
        t = b.get("type")
        if t == "dialogue":
            s = dialogue_sec(b["text"], b.get("mode", scene.get("speech_mode","normal")))
        elif t == "action":
            lines = max(1, b.get("lines", 1 + len(b.get("text",""))//24))
            s = nd["action_line"] * lines
        else:
            s = nd.get(t, 1.0) * b.get("count", 1)
        total += s
        detail.append({"type": t, "sec": round(s,2), "text": b.get("text","")[:24]})
    return round(total, 1), detail

def project_runtime(p):
    return round(sum(s.get("timing_sec", 0) for s in p.get("scenes", [])), 1)
