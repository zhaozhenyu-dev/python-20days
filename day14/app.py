"""
Day14 项目 2（RAG 知识库助手）Streamlit 在线 demo
=================================================
运行：streamlit run day14/app.py
部署：把本仓库连到 Streamlit Cloud，新建 app 指向 day14/app.py，
      在 App Settings → Secrets 里加 DEEPSEEK_API_KEY = "sk-xxx" 即可。
检索优先语义向量，失败自动降级 TF-IDF；答案由 DeepSeek 生成并标 [编号] 出处。
"""
import os
import streamlit as st

from rag_lib import answer, split_docs  # 纯逻辑库，见 rag_lib.py

HERE = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE = os.path.join(HERE, "knowledge.txt")


@st.cache_resource
def load_knowledge():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        return f.read()


def get_api_key():
    # Streamlit Cloud 用 secrets；本地用环境变量
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return os.getenv("DEEPSEEK_API_KEY", "")


def main():
    st.set_page_config(page_title="项目2 · RAG 求职资料助手", page_icon="📚")
    st.title("📚 项目 2：RAG 求职资料助手")
    st.caption("基于你的课程资料问答，答案带 [编号] 出处 ｜ 语义向量检索(主) + TF-IDF(兜底)")

    text = load_knowledge()
    api_key = get_api_key()

    if not api_key:
        st.warning("⚠️ 尚未配置 DEEPSEEK_API_KEY：检索仍可演示，但答案生成会失败。"
                   "部署后在 Streamlit Cloud 的 Secrets 里加该变量即可。")

    q = st.text_input("问点什么（试试：RAG 为什么能缓解幻觉 / 周报助手怎么用）",
                      placeholder="输入你的问题…")

    if st.button("提问", type="primary") or q:
        if not q.strip():
            st.info("先输入一个问题～")
            return
        with st.spinner("检索资料 + 生成答案中…"):
            ans, hits, mode, err = answer(q, text, api_key=api_key)

        st.success(f"检索方式：{mode}")
        st.subheader("📌 答案")
        if ans:
            st.write(ans)
        else:
            st.error(f"答案生成失败：{err}")

        st.subheader(f"🔎 命中的资料块（{len(hits)} 块）")
        for i, c in enumerate(hits, 1):
            with st.expander(f"[{i}] {c[:40]}…"):
                st.write(c)

    st.divider()
    st.caption("赵振宇 · 20 天冲刺 250 项目 2 ｜ 技术栈：fastembed(bge-small-zh) + FAISS + DeepSeek(OpenAI 兼容)")


if __name__ == "__main__":
    main()
