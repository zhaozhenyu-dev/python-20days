"""
Day18：Streamlit 演示骨架（JD 匹配助手）

演示形态：两个文本框（JD / 简历）+ 一个问题 + 「匹配」按钮 → 输出匹配报告。
状态管理：用 st.session_state 缓存解析结果，避免重复解析。
异常兜底：任何环节出错都给友好提示，不白屏崩溃。
Day19 会为它写 Dockerfile 部署上线。
"""
import os
import sys

import streamlit as st

# 让 app.py 能 import 同目录的 jd_match_agent
sys.path.insert(0, os.path.dirname(__file__))
from jd_match_agent import run_agent, parse_profile  # noqa: E402


st.set_page_config(page_title="AI 求职助手 · JD 匹配", page_icon="🎯")
st.title("🎯 AI 求职助手 · JD 匹配")
st.caption("项目 3（Day18 MVP）· 复用 Day16 Agent 外壳 + 求职工具插头")

jd = st.text_area("岗位 JD", height=180, placeholder="粘贴岗位描述全文…")
resume = st.text_area("你的简历", height=180, placeholder="粘贴你的简历全文…")
question = st.text_input("想问的问题", "我和这个岗位的匹配度怎么样？缺口在哪？")

if st.button("匹配", type="primary"):
    if not jd.strip() or not resume.strip():
        st.warning("请先填好 JD 和简历～")
    else:
        # 状态管理：缓存解析结果，避免重复消耗 token
        cache_key = f"{hash(jd)}|{hash(resume)}"
        if st.session_state.get("cache_key") != cache_key:
            with st.spinner("预解析 JD / 简历…"):
                jd_profile = parse_profile(jd, "jd")
                resume_profile = parse_profile(resume, "resume")
            st.session_state["jd_profile"] = jd_profile
            st.session_state["resume_profile"] = resume_profile
            st.session_state["cache_key"] = cache_key

        with st.spinner("Agent 正在推理（解析 → 打分 → 出报告）…"):
            try:
                report = run_agent(
                    question, jd, resume,
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                )
                st.success("分析完成")
                st.markdown(report)
            except Exception as e:
                st.error(f"运行出错：{e}")

        # 折叠展示解析出的结构化档案（可核查，体现状态管理）
        with st.expander("查看解析出的结构化档案"):
            st.json(st.session_state.get("jd_profile", {}))
            st.json(st.session_state.get("resume_profile", {}))
