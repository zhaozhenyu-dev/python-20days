import os
import requests

key = os.environ.get("DEEPSEEK_API_KEY")
if key is None:
    print("没找到 Key！先在终端执行: source ~/.zshrc")
    exit()

s = requests.Session()
s.trust_env = False

def ask(messages):
    try:
        resp = s.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "deepseek-chat",
                "messages": messages,     
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]  
    except requests.exceptions.Timeout:
        print("请求超时，这轮跳过")
        return None        # None = 失败的暗号
    except requests.exceptions.RequestException as e:
        print("请求出错:", e)
        return None
    except KeyError:
        print("响应格式不对")
        return None

messages = []                  
print("开始聊天吧！输入 exit 退出")

while True:
    q = input("你：")
    if q == "exit":
        print("再见！")
        break

    messages.append({"role": "user", "content": q})    
    answer = ask(messages)                             

    if answer is None:                                
        continue                                      

    messages.append({"role": "assistant", "content": answer})   
    print("AI：", answer)
