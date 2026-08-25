import os
import requests

# ---------- 第 1 步：从环境变量读 key ----------
key = os.environ.get("DEEPSEEK_API_KEY")
if key is None:
    print("没找到 Key！先在终端执行: source ~/.zshrc")
    exit()

# ---------- 第 2 步：准备会话（绕开系统代理） ----------
s = requests.Session()
s.trust_env = False

# ---------- 第 3 步：发请求 + 异常处理 ----------
try:
    resp = s.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "用一句话解释什么是API"}
            ]
        },
        timeout=30,
    )
    resp.raise_for_status()          # 状态码不是 2xx 就主动抛异常

    data = resp.json()               # 拆包裹：JSON 文本 → 字典
    answer = data["choices"][0]["message"]["content"]   # 剥洋葱取答案

    # ---------- 第 4 步：打印结果 ----------
    print("状态码:", resp.status_code)
    print("模型:", data["model"])
    print("本次消耗 token:", data["usage"]["total_tokens"])
    print("-" * 30)
    print("回答:", answer)

except requests.exceptions.Timeout:
    print("请求超时，检查网络后重试")
except requests.exceptions.RequestException as e:
    print("请求出错:", e)
except KeyError:
    print("响应格式不对，打印原始内容看看:", data)
