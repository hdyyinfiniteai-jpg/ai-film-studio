# -*- coding: utf-8 -*-
"""G2 可拍门。剧本层是全链路最便宜的拦截点：这里删一行 = 下游省N次抽卡。"""
import re

RULES = [
  ("reflection", r"(镜子|铜镜|镜中|玻璃倒影|水面倒影|倒影|反光|抛光|不锈钢面|屏幕映出)",
   "反射需模型同时维护正景与反射景两套一致性，镜中必然是另一个人（FM-001 硬崩）",
   "改为影子/墙上剪影，或让反射面出画外只留声音"),
  ("reenter_frame", r"(走出画面.{0,12}(又|再|重新).{0,6}(回|进|入)|出画.{0,10}入画)",
   "离框=隐含剪辑，再入画按新角色处理，必然身份漂移（FM-002）",
   "让角色全程留在画内；或拆成两条提示词并在第二条完整重述句柄"),
  ("offscreen_state", r"(换好了衣服|已经换上|不知何时(受了伤|拿着|多了)|手里(多了|已经有))",
   "模型不记忆画外事件，上一镜无血下一镜有血 = 两个人",
   "状态变化必须在画内发生，或在新提示词里重新完整声明该状态"),
  ("biomechanics", r"(扭腰|发力|重心下沉|借力|腰马合一|寸劲|卸力|翻身而起)",
   "模型不理解力学链，会生成关节反向的畸形",
   "只写可观测结果：『他的肩先动，随后整个人向左倾』"),
  ("unobservable", r"(闻到|嗅到|想起|回忆起|心里(想|明白)|暗自|意识到自己|尝到)",
   "不可观测 = 不可拍",
   "转成外部行为：『鼻翼张开一次，随即屏住呼吸』"),
  ("chain_destruction", r"(连环|接二连三地(倒|炸)|多米诺|依次倒塌|波及)",
   "需物理引擎级因果，模型只能生成同时发生的混乱",
   "拆成独立镜头，每镜只拍一个破坏事件的结果"),
  ("legible_text", r"(上面写着|字迹|落款|读道|信上写|牌匾上的字|标题写着)",
   "文字必错（FM: text_in_frame）",
   "写明『无可辨识文字』，需要文字时后期贴"),
]

def audit_scene(scene):
    text = scene.get("raw_text") or " ".join(
        b.get("text","") for b in scene.get("beats", []))
    flags = []
    for code, pat, why, fix in RULES:
        m = re.search(pat, text)
        if m:
            flags.append({"code":code, "hit":m.group(0), "why":why, "fix":fix})
    named = len(scene.get("cast_present", []))
    if named > 3:
        flags.append({"code":"too_many_named",
            "hit":f"{named}名有名角色",
            "why":"第4个角色开始句柄互串（FM handle_contamination）",
            "fix":"拆镜头，或让第4人以背影/局部/无名群众出现"})
    scene["ai_shootability"] = {"passed": len(flags)==0, "flags": flags}
    return scene["ai_shootability"]
