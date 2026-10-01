# -*- coding: utf-8 -*-
"""断4修复：价值极性 → 情绪轨迹 → 摄影机指令。推导，不询问。"""
from common import cfg

MAP = cfg("value-camera-map.json")

def lookup(vin, vout):
    for e in MAP["pairs"]:
        if e["in"] == vin and e["out"] == vout: return e
    for e in MAP["pairs"]:            # 反向对，极性取反
        if e["in"] == vout and e["out"] == vin:
            r = dict(e); r["emotion"] = e["emotion"][::-1]
            r["camera"] = e["camera"][::-1]; r["shots"] = e["shots"][::-1]
            r["polarity"] = "− → +" if e["polarity"] == "+ → −" else "+ → −"
            return r
    return None

def polarity(vin, vout):
    e = lookup(vin, vout)
    return e["polarity"] if e else "?"

def build_track(scene):
    """写入 scene['emotion_track']；返回 (ok, msg)"""
    ov = scene.get("mapping_override")
    e = lookup(scene["value_in"], scene["value_out"])
    if not e:
        return False, f"映射表无 {scene['value_in']}→{scene['value_out']}，请指定最接近的一行或申请入库"
    T = scene.get("timing_sec", 15.0)
    focal = scene.get("focal_character","")
    n = len(e["camera"])
    track = []
    for i in range(n):
        track.append({
            "t": round(T * i / n, 1),
            "focal": focal,
            "state": e["emotion"][min(i, len(e["emotion"])-1)],
            "camera": e["camera"][i],
            "shot": e["shots"][min(i, len(e["shots"])-1)],
            "beat": i+1,
        })
    scene["emotion_track"] = track
    scene["value_polarity"] = e["polarity"]
    if ov:
        # 覆写仍然生成轨迹（否则 G4 必挂），但标记出来：反用是选择，不是遗忘
        for b in track: b["overridden"] = True
        return True, f"{scene['value_in']}→{scene['value_out']} → {n} 拍【人工覆写：{ov.get('reason','')[:24]}】"
    return True, f"{scene['value_in']}→{scene['value_out']} ({e['polarity']}) → {n} 拍"
