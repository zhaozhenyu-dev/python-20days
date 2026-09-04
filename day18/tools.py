"""
Day18 工具实现：parse_profile（解析器） + score_match（打分器）

这是项目 3（JD 匹配助手）的两个"插头"，插进 Day16 的通用 Agent 外壳里。
- parse_profile 是 API 型工具：内部调一次 DeepSeek 做结构化提取，失败降级（不崩）。
- score_match 是确定性工具：纯函数算分，不调 LLM，结果可复现（不幻觉）。
"""
import json
import os
import re
import sys

# 复用 Day16 的模型调用函数（外壳不动，只换工具）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "day16"))
from agent_basic import call_deepseek


# ───────────────────────── 工具 1：parse_profile（API 型） ─────────────────────────
def _extract_json(text):
    """从模型回复里抠出 JSON：兼容裸 JSON / ```json 代码块 / 前后多余文字。"""
    if text is None:
        return None
    # 先试整段直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 再试抽 ```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 再试找第一个 { 到最后一个 } 的子串
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:
            pass
    return None


def parse_profile(text, source):
    """把自由文本（JD 或简历）解析成结构化档案。

    参数：
        text:   str  原文（JD 全文 / 简历全文）
        source: str  "jd" 提取岗位要求；"resume" 提取候选人档案
    返回：
        dict：{skills:[], experience_years:int, education:str,
               responsibilities:[], keywords:[], error?:str}
        失败时返回空骨架 + error 字段，不抛异常（降级）。
    """
    text = (text or "").strip()
    source = (source or "jd").lower()
    # 空输入直接降级，不去调模型浪费钱
    if not text:
        return {"skills": [], "experience_years": 0, "education": "",
                "responsibilities": [], "keywords": [],
                "error": "输入文本为空"}

    if source == "jd":
        sys_inst = ("你是招聘 JD 解析器。从岗位描述中提取结构化要求，"
                    "只输出 JSON，不要任何解释。")
        user_inst = (
            "请解析以下岗位 JD，输出 JSON：\n"
            "{\n"
            '  "skills": ["必须的技能/技术栈列表"],\n'
            '  "experience_years": 要求的最低工作年限(整数，无要求填0),\n'
            '  "education": "学历要求(如 本科/硕士/大专)，无要求填空串",\n'
            '  "responsibilities": ["岗位职责关键词"],\n'
            '  "keywords": ["其他重要关键词，如行业/证书"]\n'
            "}\n\nJD 原文：\n" + text
        )
    else:
        sys_inst = ("你是简历解析器。从候选人简历中提取结构化档案，"
                    "只输出 JSON，不要任何解释。")
        user_inst = (
            "请解析以下简历，输出 JSON：\n"
            "{\n"
            '  "skills": ["候选人掌握的技能/技术栈列表"],\n'
            '  "experience_years": 工作年限(整数，估算，无填0),\n'
            '  "education": "最高学历(如 本科/硕士/大专)",\n'
            '  "responsibilities": ["过往职责关键词"],\n'
            '  "keywords": ["其他关键词，如行业/项目"]\n'
            "}\n\n简历原文：\n" + text
        )

    messages = [
        {"role": "system", "content": sys_inst},
        {"role": "user", "content": user_inst},
    ]
    data, err = call_deepseek(messages, tools=None, api_key=None)
    if err:
        # 降级：模型调用失败也不崩，返回空骨架 + error
        return {"skills": [], "experience_years": 0, "education": "",
                "responsibilities": [], "keywords": [],
                "error": f"解析失败：{err}"}

    content = data["choices"][0]["message"].get("content", "")
    parsed = _extract_json(content)
    if not isinstance(parsed, dict):
        return {"skills": [], "experience_years": 0, "education": "",
                "responsibilities": [], "keywords": [],
                "error": "模型未返回合法 JSON"}

    # 规整字段，保证下游 score_match 拿到的结构稳定
    return {
        "skills": parsed.get("skills") or [],
        "experience_years": int(parsed.get("experience_years") or 0),
        "education": parsed.get("education") or "",
        "responsibilities": parsed.get("responsibilities") or [],
        "keywords": parsed.get("keywords") or [],
    }


# ───────────────────────── 工具 2：score_match（确定性型） ─────────────────────────
_EDU_RANK = {"博士": 4, "硕士": 3, "本科": 2, "大专": 1, "高中": 0, "": 0}


def _edu_rank(edu):
    """把学历字符串映射到等级数字；模糊匹配（包含关键字即可）。"""
    if not edu:
        return 0
    for k, v in _EDU_RANK.items():
        if k and k in edu:
            return v
    return 0


def score_match(jd, resume):
    """确定性计算 JD 与简历的匹配度。不调 LLM，结果可复现。

    参数：
        jd:     dict 或 JSON 字符串（来自 parse_profile 的 JD 档案）
        resume: dict 或 JSON 字符串（来自 parse_profile 的简历档案）
    返回：
        dict：{score:0-100, matched:[], missing:[], exp_gap:str,
               edu_ok:bool, advice:[]}
    """
    # 兼容模型把 dict 当 JSON 字符串传进来的情况
    if isinstance(jd, str):
        try:
            jd = json.loads(jd)
        except Exception:
            jd = {}
    if isinstance(resume, str):
        try:
            resume = json.loads(resume)
        except Exception:
            resume = {}
    jd = jd or {}
    resume = resume or {}

    jd_skills = set(s.strip().lower() for s in (jd.get("skills") or []) if s)
    res_skills = set(s.strip().lower() for s in (resume.get("skills") or []) if s)

    # 1) 技能匹配（权重 0.6）
    if jd_skills:
        matched = sorted(jd_skills & res_skills)
        missing = sorted(jd_skills - res_skills)
        skill_score = round(len(matched) / len(jd_skills) * 100)
    else:
        matched, missing, skill_score = [], [], 0

    # 2) 经验匹配（权重 0.25）
    jd_exp = int(jd.get("experience_years") or 0)
    res_exp = int(resume.get("experience_years") or 0)
    if res_exp >= jd_exp:
        exp_score = 100
        exp_gap = f"满足（简历 {res_exp} 年 ≥ 要求 {jd_exp} 年）"
    else:
        gap = jd_exp - res_exp
        exp_score = max(0, 100 - gap * 25)
        exp_gap = f"不足（简历 {res_exp} 年，差 {gap} 年，扣 {gap * 25} 分）"

    # 3) 学历匹配（权重 0.15）
    jd_rank = _edu_rank(jd.get("education") or "")
    res_rank = _edu_rank(resume.get("education") or "")
    edu_ok = res_rank >= jd_rank
    edu_score = 100 if edu_ok else 50

    # 综合加权
    score = round(skill_score * 0.6 + exp_score * 0.25 + edu_score * 0.15)

    # 生成建议
    advice = []
    if missing:
        advice.append("补齐缺失技能：" + "、".join(missing))
    if not edu_ok:
        advice.append(f"学历未达要求（简历 {resume.get('education') or '未知'} "
                      f"< 要求 {jd.get('education') or '未知'}），可突出项目经验弥补")
    if res_exp < jd_exp:
        advice.append("积累相关工作经验，或突出在校/实习项目中与岗位强相关的部分")
    if not advice:
        advice.append("核心要求基本满足，可在简历中强化与岗位关键词的对应表述")

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "exp_gap": exp_gap,
        "edu_ok": edu_ok,
        "advice": advice,
    }


if __name__ == "__main__":
    # 本地快速自测（确定性部分，不依赖网络）
    demo_jd = {"skills": ["python", "fastapi", "sql", "langchain"],
               "experience_years": 1, "education": "本科",
               "responsibilities": [], "keywords": []}
    demo_res = {"skills": ["python", "sql", "requests"],
                "experience_years": 0, "education": "本科",
                "responsibilities": [], "keywords": []}
    print("score_match 自测：")
    print(json.dumps(score_match(demo_jd, demo_res), ensure_ascii=False, indent=2))
