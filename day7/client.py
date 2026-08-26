# day7/client.py —— 客户端脚本：用 requests 调自己开的接口（反向调用）
import requests

resp = requests.post(
    "http://127.0.0.1:8000/notes",          # 调自己开的接口！
    json={"title": "反向调用", "content": "客户端调服务端"},
    timeout=10,
)
print(resp.status_code, resp.json())        # 实际返回: 200 {'msg': '收到笔记', 'id': 7, 'title': '反向调用'}
