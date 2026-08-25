import os
import requests

key = os.environ.get("DEEPSEEK_API_KEY")
if key is None:
    print("没找到 Key！先在终端执行: source ~/.zshrc")
    exit()


s = requests.Session()
s.trust_env = False

SYSTEM_PROMPT = (
    "你是一个毒舌但专业的 AI 面试官，"
    "专门面试 Python 后端/AI 应用实习生岗位。"
    "你的风格：问题犀利、偶尔毒舌挖苦，但每个问题都专业且有价值，"
    "最后一定会给出改进建议。用简体中文回答。"
)

def ask(messages, temperature=2):
    try:
        resp = s.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        print("请求超时，这轮跳过")
        return None
    except requests.exceptions.RequestException as e:
        print("请求出错:", e)
        return None
    except KeyError:
        print("响应格式不对")
        return None

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}   
]
print("面试官已就位。输入 exit 结束面试。")

while True:
    q = input("你：")
    if q == "exit":
        print("面试结束，回去等通知吧。")
        break

    messages.append({"role": "user", "content": q})
    answer = ask(messages)

    if answer is None:
        messages.pop()
        continue

    messages.append({"role": "assistant", "content": answer})
    print("面试官：", answer)
