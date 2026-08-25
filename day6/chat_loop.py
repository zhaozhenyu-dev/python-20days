import os
import requests

# ---------- 第 1 步：读 key ----------
key = os.environ.get("DEEPSEEK_API_KEY")
if key is None:
    print("没找到 Key！先在终端执行: source ~/.zshrc")
    exit()

# ---------- 第 2 步：准备会话 ----------
s = requests.Session()
s.trust_env = False


# ---------- 第 3 步：ask 函数——进去的是对话记录，出来的是回答 ----------
def ask(messages):
    try:
        resp = s.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "deepseek-chat",
                "messages": messages,     # 整本记录发过去
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]   # 只把答案递出去
    except requests.exceptions.Timeout:
        print("请求超时，这轮跳过")
        return None        # None = 失败的暗号
    except requests.exceptions.RequestException as e:
        print("请求出错:", e)
        return None
    except KeyError:
        print("响应格式不对")
        return None


# ---------- 第 4 步：主循环——聊天开始 ----------
messages = []                    # 对话记录本（上下文）
print("开始聊天吧！输入 exit 退出")

while True:
    q = input("你：")
    if q == "exit":
        print("再见！")
        break

    messages.append({"role": "user", "content": q})    # 1. 你的话进记录本
    answer = ask(messages)                             # 2. 整本记录发给 AI

    if answer is None:                                 # 3. 失败就不记这轮
        messages.pop()                                 #    把刚塞进去的问题撤回来
        continue                                       #    直接进入下一轮

    messages.append({"role": "assistant", "content": answer})   # 4. AI 的话进记录本
    print("AI：", answer)
