import requests

s = requests.Session()
s.trust_env = False

try:
    resp = s.get("https://v1.hitokoto.cn/", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    print(f"状态码: {resp.status_code}")
    print(f"句子: {data['hitokoto']}")
    print(f"出处: {data['from']}")
except requests.exceptions.RequestException as e:
    print("请求出问题了，稍后再试试：", e)
