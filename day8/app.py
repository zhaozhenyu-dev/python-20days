import streamlit as st
import time

st.title("我的第一个 AI 网页")

# 5.3 用 session_state 记住历史：只在第一次访问时创建空列表
# "messages" 是字典 st.session_state 里的一个键，它的值是一个列表
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 先把历史记录一条条显示出来
for msg in st.session_state["messages"]:
    st.write(msg)

# 聊天输入框：回车发送，发送后自动清空（不会像 text_input 那样重复触发）
user_input = st.chat_input("你：")

if user_input:
    # 5.2 加载状态：AI "思考" 时显示转圈
    with st.spinner("AI 思考中..."):
        time.sleep(2)                              # 模拟网络延迟
        reply = f"AI：收到你的消息：{user_input}"    # 模拟 AI 回复

    # 把用户消息和 AI 回复都存进历史列表
    st.session_state["messages"].append(f"你：{user_input}")
    st.session_state["messages"].append(reply)

    st.rerun()   # 立刻重新跑一遍脚本，让上面的 for 循环把新消息也显示出来（不会重复）
