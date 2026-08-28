import streamlit as st
import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def generate_weekly_report(notes: str) -> str:
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "你是一个职场周报助手。请把用户给出的一周工作流水，"
        "整理成标准周报，使用 Markdown 格式，包含三个小节："
        "## 本周完成、## 下周计划、## 问题与风险。"
    )
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": notes},
        ],
        "temperature": 0.3,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


st.title("AI 周报助手")

notes = st.text_area("粘贴本周工作流水（一行一条）：", height=200, key="notes")
if st.button("生成周报"):
    if notes.strip():
        with st.spinner("AI 整理中..."):
            report = generate_weekly_report(notes)
        st.markdown(report)
        st.download_button("下载周报", report, file_name="weekly_report.md")
    else:
        st.warning("先写点工作内容再生成哦")
