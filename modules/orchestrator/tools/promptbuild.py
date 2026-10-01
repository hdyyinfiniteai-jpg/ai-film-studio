# -*- coding: utf-8 -*-
"""S5：把 scene + emotion_track + 资产句柄 + 美学模板 编译成中文 Seedance 提示词。
   五段式：镜头声明 / 句柄自声明 / 时间轴事件 / 微表演 / 风格与禁令。"""
from common import aesthetic
import density

EYE_LIFE = "眼球有极细微的不规则跳视；眨眼不规律，一次较慢一次极快；瞳孔上有一枚清晰的实际光源反射点"

def _handles(p, scene):
    m, i = {}, 1
    for cid in scene.get("cast_present", []):
        m[f"@image{i}"] = cid; i += 1
    if scene.get("location_id"):
        m[f"@image{i}"] = scene["location_id"]; i += 1
    for pr in scene.get("props_present", []):
        m[f"@image{i}"] = pr; i += 1
    return m

def _desc(p, key, cid):
    for it in p.get(key, []):
        if it["id"] == cid: return it
    return {}

def _style_block(p):
    a = aesthetic(p)
    ld = a.get("light_doctrine", {})
    src = "、".join(ld.get("allowed_sources", []))
    fb  = "、".join(dict.fromkeys(ld.get("forbidden", []) + a.get("forbid_block", [])))
    pal = "、".join(a.get("palette_60_30_10", []))
    return (f"【风格】光源仅来自：{src}。摄影机位于{'暗侧' if ld.get('camera_side')=='shadow_side' else ld.get('camera_side','主光侧')}。"
            f"色板 60/30/10：{pal}。大气：{ld.get('atmosphere','')}。调色参照：{'、'.join(a.get('grade_refs',[]))}。\n"
            f"【禁止】{fb}。")

def build_scene_prompts(p, scene):
    n, reasons = density.compute(scene)
    track = scene.get("emotion_track") or []
    a = aesthetic(p); lens = a.get("lens_doctrine", {})
    hmap = _handles(p, scene)
    per = max(1, len(track) // n) if track else 1
    prompts = []
    for k in range(n):
        seg = track[k*per:(k+1)*per] if track else []
        if k == n-1 and track: seg = track[k*per:] or [track[-1]]
        shot = (seg[0]["shot"] if seg else "MS")
        focal_lens = lens.get("emotion" if shot in ("CU","ECU") else
                              "dialogue" if shot in ("MS","OTS") else "wide", 50)
        lines = []
        lines.append(f"【镜头】本条包含 {max(1,len(seg))} 个镜头，切换点严格发生在下列编号节拍处；除此之外不得有任何剪辑。")
        lines.append("【出场】" + "；".join(
            f"{h}={_desc(p,'cast',c).get('handle_desc_zh') or _desc(p,'locations',c).get('handle_desc_zh') or _desc(p,'props',c).get('handle_desc_zh') or c}"
            for h,c in hmap.items()))
        lines.append(f"【焦距】{focal_lens}mm，无光学畸变。")
        for j, b in enumerate(seg or [{"beat":1,"camera":"静止","state":"稳定","focal":scene.get('focal_character','')}], 1):
            lines.append(f"节拍{b['beat']}（{b.get('t',0)}s）：摄影机——{b['camera']}。"
                         f"焦点角色 {b['focal']} 处于「{b['state']}」的可观测状态。")
        if len(seg) >= 2:
            lines.append(f"However, when 节拍{seg[1]['beat']} 的触发事件发生时，{seg[0]['focal']} "
                         f"的状态由「{seg[0]['state']}」切换为「{seg[-1]['state']}」——只写肌肉动作，不写情绪。")
        lines.append("【微表演】" + (scene.get("micro_beats", {}).get(str(k+1))
            or "〈待 ACTING 模块填充：只写可观测肌肉动作，禁情绪形容词；"
               "至少1处身体与台词矛盾；反应必须错开，禁同步〉"))
        if shot in ("CU","ECU"):
            lines.append("【眼神】" + EYE_LIFE + "。")
        lines.append(_style_block(p))
        txt = "\n".join(lines)
        prompts.append({
            "id": f"sc{scene['no']}-p{k+1}",
            "scene": scene["no"],
            "tag": f"[{shot} · {scene['value_in']}→{scene['value_out']} · {k+1}/{n}]",
            "duration_sec": round(scene.get("timing_sec",15)/n, 1),
            "shot_count": max(1, len(seg)),
            "handles": hmap,
            "text_zh": txt,
            "char_count": len(txt),
            "lens_mm": focal_lens,
            "generation_log": [],
        })
    return prompts, reasons
