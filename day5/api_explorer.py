import requests

s = requests.Session()
s.trust_env = False

BASE = "https://httpbin.org"


def explore_get(name, age):
    """GET 请求，带查询参数"""
    try:
        params = {"name": name, "age": age}
        resp = s.get(f"{BASE}/get", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print("GET 请求结果：")
        print(f"  最终 URL: {data['url']}")
        print(f"  回显参数: {data['args']}")
        return True
    except requests.exceptions.RequestException as e:
        print("GET 请求出错：", e)
        return False


def explore_post(content):
    """POST 请求，带 JSON 体"""
    try:
        payload = {"content": content}
        resp = s.post(f"{BASE}/post", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print("POST 请求结果：")
        print(f"  收到的 JSON: {data['json']}")
        return True
    except requests.exceptions.RequestException as e:
        print("POST 请求出错：", e)
        return False


if __name__ == "__main__":
    explore_get("振宇", 20)
    print("-" * 40)
    explore_post("Hello API")
