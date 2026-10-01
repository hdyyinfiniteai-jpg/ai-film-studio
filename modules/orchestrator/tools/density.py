# -*- coding: utf-8 -*-
"""定量提示词密度：把 PROMPT_DENSITY 从定性变成可计算。
   N0 = ceil(T/15) → 拆分触发器+1 → 合并触发器−1 → 超字数再拆 → 不低于基线"""
import math
from common import cfg

TH = cfg("gates.json")["thresholds"]

def compute(scene, char_estimate=None):
    T = scene.get("timing_sec", 15.0)
    base = math.ceil(T / TH["shot_seconds_base"])
    n = base; reasons = [f"基线 ceil({T}/{TH['shot_seconds_base']}) = {base}"]

    # 拆分触发器
    if scene.get("value_polarity") in ("+ → −", "− → +"):
        n += 1; reasons.append("+1 价值极性翻转（摄影机基调切换点）")
    if scene.get("insert_shots"):
        n += len(scene["insert_shots"]); reasons.append(f"+{len(scene['insert_shots'])} 插入镜头需独立成镜")
    if scene.get("view_change_180"):
        n += 1; reasons.append("+1 视角变化超180°")
    if len(scene.get("cast_present", [])) >= 4:
        n += 1; reasons.append("+1 出现第4个有名角色")
    if scene.get("wardrobe_change"):
        n += 1; reasons.append("+1 服装/妆效状态变化")

    # 合并触发器
    if scene.get("continuous_tail"):
        n -= 1; reasons.append("−1 尾段情绪连续可合并")
    if scene.get("value_polarity") == "平衡":
        n -= 1; reasons.append("−1 呼吸场（无价值运动）")

    # 字数再拆
    if char_estimate and char_estimate / max(n,1) > TH["char_limit_zh"]:
        extra = math.ceil(char_estimate / TH["char_limit_zh"]) - n
        if extra > 0: n += extra; reasons.append(f"+{extra} 单条字数超 {TH['char_limit_zh']}")

    n = max(n, base)
    reasons.append(f"N_final = {n}")
    return n, reasons
