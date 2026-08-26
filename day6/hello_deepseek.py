import os
import requests

key = os.environ.get("DEEPSEEK_API_KEY")
if key is None:
    print("没找到 Key！先在终端执行: source ~/.zshrc")
    exit()

s = requests.Session()
s.trust_env = False

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
    resp.raise_for_status()         

    data = resp.json()               
    answer = data["choices"][0]["message"]["content"]   

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
