# -*- coding: utf-8 -*-
"""G5 出货门 · 跨提示词一致性审计。十二项，只报不改。
   一致性靠字符串比对，不靠『我记得写过』——人在第50条之后就记不住了。"""
import re, difflib
from common import cfg, aesthetic

TH = cfg("gates.json")["thresholds"]
EMO_ADJ = ["愤怒地","悲伤地","紧张地","高兴地","痛苦地","恐惧地","焦虑地","失望地",
           "兴奋地","沮丧地","震惊地","不安地","激动地","难过地","开心地"]

def _sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def run(p):
    findings = []
    def F(level, code, msg, ids):
        findings.append({"level":level,"code":code,"msg":msg,"prompts":ids})

    prompts = p.get("prompts", [])
    a = aesthetic(p)
    lens_ok = set(a.get("lens_doctrine", {}).values())
    forbidden = a.get("light_doctrine", {}).get("forbidden", [])

    # 1 句柄漂移
    for role in p.get("cast", []) + p.get("locations", []) + p.get("props", []):
        base = role.get("handle_desc_zh","")
        if not base: continue
        drift = []
        for pr in prompts:
            for h, cid in pr.get("handles", {}).items():
                if cid != role["id"]: continue
                m = re.search(re.escape(h) + r"=([^；\n]*)", pr["text_zh"])
                if m and _sim(m.group(1), base) < TH["handle_similarity_min"]:
                    drift.append(pr["id"])
        if drift: F("红","handle_drift", f"{role['id']} 句柄描述漂移", drift)

    # 2 服装状态断裂
    prev = {}
    for s in sorted(p.get("scenes", []), key=lambda x: x["no"]):
        for cid, st in (s.get("wardrobe_state") or {}).items():
            if cid in prev and prev[cid] != st and not s.get("wardrobe_change"):
                F("红","wardrobe_break",
                  f"第{s['no']}场 {cid} 服装 {prev[cid]}→{st}，但无画内换装事件", [])
            prev[cid] = st

    # 3 空间关系冲突（同地点方位词矛盾）
    DIRS = ["左","右","门在左","门在右"]
    byloc = {}
    for pr in prompts:
        loc = next((c for h,c in pr.get("handles",{}).items()
                    if any(l["id"]==c for l in p.get("locations",[]))), None)
        if loc: byloc.setdefault(loc, []).append(pr)
    for loc, prs in byloc.items():
        sig = {}
        for pr in prs:
            for d in ["门在左","门在右"]:
                if d in pr["text_zh"]: sig.setdefault(d, []).append(pr["id"])
        if len(sig) > 1:
            F("红","space_conflict", f"{loc} 方位描述矛盾：{list(sig)}", sum(sig.values(), []))

    # 4 焦距违反教条
    bad = [pr["id"] for pr in prompts if lens_ok and pr.get("lens_mm") not in lens_ok]
    if bad: F("红","lens_doctrine", f"焦距不在美学模板允许值 {sorted(lens_ok)} 内", bad)

    # 5 光源违反教条
    bad = [pr["id"] for pr in prompts
           if any(w in pr["text_zh"].split("【禁止】")[0] for w in forbidden)]
    if bad: F("红","light_doctrine", "正文出现被禁止的光源词", bad)

    # 6 镜头数未声明
    bad = [pr["id"] for pr in prompts if "本条包含" not in pr["text_zh"]]
    if bad: F("红","shot_count_undeclared", "未声明镜头数 → FM-011 伪剪辑", bad)

    # 7 字数超限
    bad = [pr["id"] for pr in prompts if len(pr["text_zh"]) > TH["char_limit_zh"]]
    if bad: F("红","char_limit", f"超 {TH['char_limit_zh']} 字 → FM-016 后段被忽略", bad)

    # 8 ⚠️密度
    for pr in prompts:
        t3 = pr["text_zh"].count("⚠️⚠️⚠️")
        t1 = pr["text_zh"].count("⚠️") - t3*3
        pr["warning_density"] = {"single": t1, "triple": t3}
        if t1 > TH["warning_single_max"] or t3 > TH["warning_triple_max"]:
            F("黄","warning_density", f"{pr['id']} ⚠️密度超标 单{t1}/三重{t3}", [pr["id"]])

    # 9 情绪形容词残留
    bad = [pr["id"] for pr in prompts if any(w in pr["text_zh"] for w in EMO_ADJ)]
    if bad: F("红","emotion_adjective", "微表演出现情绪形容词 → FM-014 表演扁平", bad)

    # 10 眼神生命三件套
    bad = [pr["id"] for pr in prompts
           if any(k in pr.get("tag","") for k in ["CU","ECU"]) and "跳视" not in pr["text_zh"]]
    if bad: F("黄","eye_life", "近景缺眼神生命三件套（微跳视/眨眼质量/眼神光）", bad)

    # 11 条件式转变
    bad = [pr["id"] for pr in prompts
           if pr.get("shot_count",1) >= 2 and "However, when" not in pr["text_zh"]]
    if bad: F("黄","conditional_turn", "有情绪转折但缺 However, when 条件式结构", bad)

    # 12 道具链断裂
    for pr_ in p.get("props", []):
        pay = pr_.get("payoff_scene")
        if pay and not any(pr_["id"] in x.get("handles", {}).values()
                           for x in prompts if x["scene"] == pay):
            F("黄","prop_chain", f"{pr_['id']} 的 payoff 在第{pay}场，但该场提示词未出现该道具", [])

    # 按影响面排序
    findings.sort(key=lambda f: (f["level"] != "红", -len(f["prompts"])))
    return findings
