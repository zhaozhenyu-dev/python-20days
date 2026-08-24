import requests

s = requests.Session()
s.trust_env = False


def get_hitokoto():
    """请求一言 API，成功返回句子字符串，失败返回 None"""
    try:
        resp = s.get("https://v1.hitokoto.cn/", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return f"{data['hitokoto']}  ——《{data['from']}》"
    except requests.exceptions.Timeout:
        print("等太久了，服务器没理我")
        return None
    except requests.exceptions.RequestException as e:
        print("请求出问题了：", e)
        return None


while True:
    result = get_hitokoto()          # ① 调用函数拿结果

    if result is not None:           # ② 拿到东西才打印
        print("-" * 30)
        print(result)

    choice = input("再来一句？(y/n)：").lower().strip()
    if choice != "y":
        break

print("拜拜！")
