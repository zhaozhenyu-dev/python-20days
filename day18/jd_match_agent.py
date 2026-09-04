"""
Day18：JD 匹配助手 —— 复用 Day16 的「通用 Agent 外壳」，只换求职插头。

复用关系（对照 Day16 agent_basic.py）：
- call_deepseek  : 直接从 day16 import（模型调用一行没重写）
- execute_tool    : 逻辑同 Day16，但查的是本文件的 TOOLS_IMPL（求职工具表）
- run_agent       : 逻辑同 Day16 主循环，额外接收 jd/resume 注入上下文
- TOOLS_IMPL/SCHEMA : 从 calculator/get_weather 换成 parse_profile/score_match

这就是 Day17 说的「外壳不动，只换工具」。
"""
import json
import os
import sys
import time

# 真复用 Day16 的模型调用函数
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day16"))
from agent_basic import call_deepseek

# 本文件的求职工具
from tools import parse_profile, score_match


# ───────────────────────── 工具登记表（求职版插头） ─────────────────────────
TOOLS_IMPL = {
    "parse_profile": parse_profile,
    "score_match": score_match,
}

# 给模型的"工具说明书"
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "parse_profile",
            "description": "把 JD 或简历原文解析成结构化档案 JSON。"
                           "source 传 'jd' 表示解析岗位要求，'resume' 表示解析候选人档案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "JD 或简历的原文文本"},
                    "source": {"type": "string", "description": "固定传 'jd' 或 'resume'"},
                },
                "required": ["text", "source"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_match",
            "description": "计算 JD 档案与简历档案的匹配度（0-100 分）。"
                           "jd 和 resume 都传 parse_profile 返回的 JSON 字符串。",
            "parameters": {
                "type": "object",
                "properties": {
                    "jd": {"type": "string", "description": "parse_profile(jd) 返回的结构化档案 JSON 字符串"},
                    "resume": {"type": "string", "description": "parse_profile(resume) 返回的结构化档案 JSON 字符串"},
                },
                "required": ["jd", "resume"],
            },
        },
    },
]


# ───────────────────────── 执行工具（带重试 + 降级，逻辑同 Day16） ─────────────────────────
def execute_tool(name, arguments, max_retry=2):
    """运行一个工具：失败重试，仍失败返回错误信息（不让整个 Agent 崩）。"""
    fn = TOOLS_IMPL.get(name)
    if fn is None:
        return f"未知工具：{name}"
    for attempt in range(1, max_retry + 1):
        try:
            return fn(**arguments)
        except Exception as e:
            if attempt == max_retry:
                return f"工具 {name} 执行失败（已重试 {max_retry} 次）：{e}"
            time.sleep(0.5)  # 简单退避，等一下再试


# ───────────────────────── Agent 主循环（ReAct，逻辑同 Day16） ─────────────────────────
def run_agent(question, jd, resume, api_key=None, max_rounds=6):
    """JD 匹配主入口。

    把 JD 原文 + 简历原文注入上下文，模型自己决定：
        先 parse_profile(jd) → parse_profile(resume) → score_match(...) → 综合报告
    """
    jd = jd or ""
    resume = resume or ""
    messages = [
        {"role": "system", "content": (
            "你是求职匹配助手。处理用户问题时：\n"
            "1) 先用 parse_profile 分别解析岗位 JD 和候选人简历，拿到结构化档案；\n"
            "2) 再用 score_match 传入两个档案的 JSON 计算匹配度；\n"
            "3) 最后用中文给出匹配报告：总分、命中技能、缺口技能、经验差距、提升建议。\n"
            "不要编造档案内容，一切以工具返回为准。"
        )},
        {"role": "user", "content": (
            f"岗位 JD：\n{jd}\n\n"
            f"候选人简历：\n{resume}\n\n"
            f"用户问题：{question}"
        )},
    ]
    for _ in range(max_rounds):
        data, err = call_deepseek(messages, tools=TOOLS_SCHEMA, api_key=api_key)
        if err:
            return f"模型调用出错：{err}"
        msg = data["choices"][0]["message"]

        # 情况 A：模型要调工具
        if msg.get("tool_calls"):
            messages.append(msg)  # 把模型的"调用意图"原样留进对话
            for call in msg["tool_calls"]:
                fname = call["function"]["name"]
                fargs = json.loads(call["function"]["arguments"])
                result = execute_tool(fname, fargs)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": str(result),
                })
            continue  # 继续循环，让模型看工具结果

        # 情况 B：模型直接给出最终答案
        return msg.get("content", "")

    return "已达到最大轮数，仍未收敛。"


if __name__ == "__main__":
    # 本地命令行快速演示
    demo_jd = """
    高级 Python 开发实习生
    要求：熟悉 Python、FastAPI、SQL；了解 LangChain/RAG；
    本科及以上；至少 1 年相关经验。
    职责：参与 AI 应用开发、接口联调、向量检索。
    """
    demo_resume = """
    赵振宇，某大学计算机专业本科在读。
    技能：Python、SQL、requests、Streamlit、pytest。
    做过 AI 周报助手、RAG 知识库、带工具调用的 Agent 项目。
    无正式工作经验（在校项目为主）。
    """
    print(run_agent(
        "我和这个岗位的匹配度怎么样？缺口在哪？",
        demo_jd, demo_resume,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    ))
