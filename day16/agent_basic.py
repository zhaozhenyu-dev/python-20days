"""
Day16：带工具的 Agent —— 手写 ReAct + function calling
工具：calculator（计算器） + get_weather（天气查询）
硬指标：工具调用失败必须重试 + 降级，不能让整个 Agent 崩。
"""
import json
import os
import time
import requests

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ───────────────────────── 1. 调模型（支持工具） ─────────────────────────
def call_deepseek(messages, tools=None, api_key=None):
    """和 Day14 的 call_deepseek 几乎一样，只是多支持 tools 参数。"""
    key = api_key or os.getenv("DEEPSEEK_API_KEY") or ""
    if not key:
        return None, "缺少 DEEPSEEK_API_KEY"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
    }
    if tools:
        payload["tools"] = tools
    try:
        r = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, f"调用 DeepSeek 失败：{e}"


# ───────────────────────── 2. 工具：计算器 ─────────────────────────
_ALLOWED = set("0123456789+-*/(). ")
def calculator(expression):
    """只算四则运算，字符集受限，杜绝代码注入。"""
    expr = expression.strip()
    if not expr or set(expr) - _ALLOWED:
        return f"表达式非法：{expr!r}"
    try:
        # 空环境 eval：不能调任何函数，只能做四则运算
        result = eval(expr, {"__builtins__": {}}, {})
        return f"{expr} = {result}"
    except Exception as e:
        return f"计算失败：{e}"


# ───────────────────────── 3. 工具：天气查询（真实 API + 降级） ─────────────────────────
def get_weather(city):
    """调 Open-Meteo 真实天气，失败降级到模拟数据（不崩）。"""
    # 清洗：模型偶尔会把“的天气”“天气”等后缀一起传进来，这里剥掉
    city = city.strip()
    for suffix in ("的天气", "天气", "的气温", "气温"):
        if city.endswith(suffix):
            city = city[: -len(suffix)]
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "zh"},
            timeout=8,
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return f"找不到城市：{city}"
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=8,
        )
        wx.raise_for_status()
        cw = wx.json()["current_weather"]
        return f"{city}：{cw['temperature']}°C，风速 {cw['windspeed']} km/h"
    except Exception as e:
        # 降级：不崩，给模拟值，并说明原因
        return f"[降级] {city} 实时天气暂不可用，模拟：22°C 晴（原因：{e}）"


# ───────────────────────── 4. 工具登记表 ─────────────────────────
TOOLS_IMPL = {
    "calculator": calculator,
    "get_weather": get_weather,
}

# 给模型的"工具说明书"：名字 / 干嘛 / 参数长啥样
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算一个四则运算表达式，如 (23+7)*4",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的当前天气。仅接收纯城市名，不要包含“的天气”“天气”等后缀。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "纯城市名，如 杭州、北京、上海（不要带“的天气”等后缀）"}
                },
                "required": ["city"],
            },
        },
    },
]


# ───────────────────────── 5. 执行工具（带重试 + 降级） ─────────────────────────
def execute_tool(name, arguments, max_retry=2):
    """运行一个工具：失败重试，仍失败返回错误信息（不让整个 Agent 崩）。"""
    fn = TOOLS_IMPL.get(name)
    if fn is None:
        return f"未知工具：{name}"
    for attempt in range(1, max_retry + 1):
        try:
            return fn(**arguments)
        except Exception as e:
            if attempt == max_retry:
                return f"工具 {name} 执行失败（已重试 {max_retry} 次）：{e}"
            time.sleep(0.5)  # 简单退避，等一下再试


# ───────────────────────── 6. Agent 主循环（ReAct） ─────────────────────────
def run_agent(question, api_key=None, max_rounds=5):
    messages = [
        {"role": "system", "content": "你是一个助手，必要时调用工具回答问题。能直接答就直接答。"},
        {"role": "user", "content": question},
    ]
    for _ in range(max_rounds):
        data, err = call_deepseek(messages, tools=TOOLS_SCHEMA, api_key=api_key)
        if err:
            return f"模型调用出错：{err}"
        msg = data["choices"][0]["message"]

        # 情况 A：模型要调工具
        if msg.get("tool_calls"):
            messages.append(msg)  # 把模型的"调用意图"原样留进对话
            for call in msg["tool_calls"]:
                fname = call["function"]["name"]
                fargs = json.loads(call["function"]["arguments"])
                result = execute_tool(fname, fargs)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                })
            continue  # 继续循环，让模型看工具结果

        # 情况 B：模型直接给出最终答案
        return msg.get("content", "")

    return "已达到最大轮数，仍未收敛。"


if __name__ == "__main__":
    q = input("你的问题：")
    print(run_agent(q, api_key=os.getenv("DEEPSEEK_API_KEY")))
