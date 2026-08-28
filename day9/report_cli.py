import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def generate_weekly_report(notes: str) -> str:
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "你是一个职场周报助手。请把用户给出的一周工作流水，"
        "整理成标准周报，使用 Markdown 格式，包含三个小节："
        "## 本周完成、## 下周计划、## 问题与风险。"
        "每条用简短的要点，不要啰嗦。"
    )
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": notes},
        ],
        "temperature": 0.3,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print("把本周工作流水粘进来（一行一条，空行结束）：")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    notes = "\n".join(lines)
    report = generate_weekly_report(notes)
    print("\n===== 你的周报 =====\n")
    print(report)
