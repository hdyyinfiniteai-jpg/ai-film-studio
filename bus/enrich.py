# -*- coding: utf-8 -*-
"""提示词增强 —— 三套系统在这里交汇。

orchestrator 的 S5 故意把【微表演】留空（台词级肌肉动作属于创作不属于编译）。
本模块用两个来源把它填上：
   C 的 beats 库   → 可观测肌肉动作成品句（按情绪×强度×体位×景别×类型检索）
   B 的导演决策    → 面具在第几拍裂开 / 反应向内还是向外 / 延迟还是即时
"""
import os, json, re
import paths as P

PLACEHOLDER = "〈待 ACTING 模块填充"

def _beats():
    p = os.path.join(P.LIBR, "library", "beats", "beats.jsonl")
    if not os.path.exists(p): return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def _pick(beats, emotion, shot, genre, speaking, used, intensity=None):
    # 硬护栏：类型不匹配的句子绝不跨用——喜剧节拍落进古装戏是灾难，
    # 评分再高也不行。只允许目标类型与「通用」。
    pool = [b for b in beats if b["genre"] in (genre, "通用")] or beats
    def score(b):
        s = 0
        if b["emotion"] == emotion: s += 6
        if b["shot"] == shot: s += 2
        if b["genre"] == genre: s += 3
        elif b["genre"] == "通用": s += 1
        if b["speaking"] == speaking: s += 1
        if intensity and b["intensity"] == intensity: s += 2
        if b["contradiction"]: s += 1          # 身体与台词矛盾是加分项
        if b["id"] in used: s -= 10            # 同一片内不重复用同一句
        return s
    c = max(pool, key=score) if pool else None
    return c if c and score(c) > 4 else None

STATE2EMO = {
    "平稳":"冷漠","失控":"慌张","混乱":"慌张","收拢":"决意","开放":"喜悦","冻结":"震惊",
    "封闭":"压抑","松动":"释然","上扬":"喜悦","下沉":"悲伤","平静":"冷漠","震惊":"震惊",
    "活动":"警觉","静止":"隐忍","舒展":"释然","收缩":"恐惧","靠近":"喜悦","排斥":"轻蔑",
    "压抑":"压抑","释放":"决意","挺立":"决意","塌陷":"羞耻","松弛":"疲惫","警觉":"警觉",
    "稳定":"冷漠",
}

def run(project_path, genre="通用", dry=False):
    p = P.jload(project_path)
    beats = _beats()
    used, filled, missed = set(), 0, []
    scenes = {s["no"]: s for s in p.get("scenes", [])}

    for pr in p.get("prompts", []):
        if PLACEHOLDER not in pr["text_zh"]: continue
        s = scenes.get(pr["scene"], {})
        track = s.get("emotion_track") or []
        idx = int(re.search(r"-p(\d+)$", pr["id"]).group(1)) - 1
        n_pr = s.get("planned_prompt_count") or 1
        # 与 promptbuild 的切片一致：一条提示词可能覆盖多拍
        per = max(1, len(track) // n_pr) if track else 1
        seg = track[idx*per:(idx+1)*per] or ([track[-1]] if track else [])
        if idx == n_pr - 1 and track: seg = track[idx*per:] or [track[-1]]
        b = seg[-1] if seg else {}          # 取落点状态：微表演描述人物最终停在哪
        state = b.get("state", "稳定")
        emo = STATE2EMO.get(state, state)
        shot = "CU" if any(k in pr.get("tag","") for k in ("CU","ECU")) else "MS"
        speaking = "对白" in pr["text_zh"] or True

        # B 的决策接入
        d = (s.get("perf_direction") or {})
        inten = 3 if d.get("PERF_VARIANT_1", "").startswith("向内") else None
        crack = s.get("mask_crack_beat")

        hit = _pick(beats, emo, shot, genre, speaking, used, inten)
        if not hit:
            missed.append((pr["id"], emo, shot, genre)); continue
        used.add(hit["id"])
        line = hit["text"]
        extras = []
        beats_in = {x.get("beat") for x in seg}
        if crack and crack in beats_in:
            extras.append("⚠️本拍是面具裂开的一拍：以上动作在此处首次不受控制")
        if d.get("PERF_VARIANT_2", "").startswith("延迟") and (
                (crack and crack in beats_in) or (not crack and idx == 0)):
            extras.append("反应延迟约 0.4 秒后才出现，先有一拍完全的无反应")
        txt = f"{line}（{hit['id']}）" + ("；" + "；".join(extras) if extras else "")
        pr["text_zh"] = re.sub(r"【微表演】〈[^〉]*〉", "【微表演】" + txt, pr["text_zh"])
        pr["char_count"] = len(pr["text_zh"])
        pr.setdefault("beat_refs", []).append(hit["id"])
        filled += 1

    if not dry: P.jsave(p, project_path)
    return filled, missed, used
