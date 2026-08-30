import pytest
from unittest.mock import patch
from report_cli import generate_weekly_report


def test_returns_string():
    # 伪造一份 DeepSeek 返回结构（就是 Day6 剥洋葱那层）
    fake = {"choices": [{"message": {"content": "## 本周完成\n- 写了周报"}}]}
    with patch("report_cli.requests.post") as mock_post:
        mock_post.return_value.json.return_value = fake
        result = generate_weekly_report("周一写代码")
    assert isinstance(result, str)      # 结果必须是字符串
    assert "本周完成" in result         # 周报得含"本周完成"段


def test_empty_notes_still_works():
    fake = {"choices": [{"message": {"content": "## 本周完成\n- 无"}}]}
    with patch("report_cli.requests.post") as mock_post:
        mock_post.return_value.json.return_value = fake
        result = generate_weekly_report("")
    assert isinstance(result, str)      # 空流水也不能崩


def test_function_call_api_with_notes():
    fake = {"choices": [{"message": {"content": "ok"}}]}
    with patch("report_cli.requests.post") as mock_post:
        mock_post.return_value.json.return_value = fake
        generate_weekly_report("测试流水")
        sent = mock_post.call_args.kwargs["json"]
        assert sent["messages"][1]["content"] == "测试流水"  # 流水真传进 user 消息
