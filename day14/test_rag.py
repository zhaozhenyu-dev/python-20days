"""
Day14 项目 2 的 pytest 测试（CI 会跑这一份）
==========================================
只测「纯逻辑、不联网、不依赖 langchain」的部分：
  - TF-IDF 切分 / 向量 / 余弦 / 检索（兜底链路）
  - DeepSeek 调用的 prompt 拼接（用 mock 拦掉真实网络）
语义向量那条链路需要下载模型 + 装 langchain，留给本地/线上验证，不进 CI。
"""
import os
from unittest import mock

import rag_lib


SAMPLE = """RAG 是检索增强生成。它先检索资料，再让大模型根据资料回答，能缓解幻觉。
周报助手能把手写流水账变成格式化的周报。输入流水账，输出三段式周报。
DeepSeek 提供 OpenAI 兼容的对话接口，用 requests 调 chat/completions 即可。"""


def test_tokenize_chinese_and_english():
    toks = rag_lib.tokenize("调用 DeepSeek API 接口")
    assert "deepseek" in toks
    assert "接" in toks and "口" in toks  # 中文按字


def test_chunk_text_size():
    chunks = rag_lib.chunk_text("一二三四五六七八九十", size=4)
    assert chunks == ["一二三四", "五六七八", "九十"]


def test_tfidf_vectors_normalized():
    vecs = rag_lib.tfidf_vectors(["周报助手 格式化 周报", "DeepSeek 接口 调用"])
    for v in vecs:
        norm = sum(x * x for x in v.values()) ** 0.5
        assert abs(norm - 1.0) < 1e-6  # 已 L2 归一化


def test_cosine_identical_is_one():
    v = rag_lib.tfidf_vectors(["周报 助手"])[0]
    assert abs(rag_lib.cosine(v, v) - 1.0) < 1e-6


def test_retrieve_tfidf_finds_relevant_block():
    chunks = [
        "DeepSeek 提供 OpenAI 兼容接口，用 requests 调用。",
        "周报助手把手写流水账变成格式化周报。",
        "RAG 通过检索资料缓解大模型幻觉。",
    ]
    scored = rag_lib.retrieve_tfidf(chunks, "怎么调用 DeepSeek", top_k=1)
    assert scored[0][0] == 0  # 命中第 0 块（DeepSeek 那块）


def test_call_deepseek_builds_correct_request():
    """用 mock 拦截 requests.post，验证 prompt 拼对了、且只据资料答。"""
    fake_resp = mock.Mock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {
        "choices": [{"message": {"content": "资料中未提及"}}]
    }
    with mock.patch.object(rag_lib.requests, "post", return_value=fake_resp) as m:
        ans, err = rag_lib.call_deepseek(
            "RAG 是什么", "[1] RAG 是检索增强生成。", api_key="sk-test"
        )
    assert ans == "资料中未提及"
    assert err is None
    # 断言：请求体里确实把「资料」和「问题」都拼进去了
    sent = m.call_args.kwargs["json"]
    user_msg = sent["messages"][1]["content"]
    assert "[1] RAG 是检索增强生成。" in user_msg
    assert "RAG 是什么" in user_msg
    assert sent["model"] == "deepseek-chat"


def test_call_deepseek_no_key_returns_error():
    os.environ.pop("DEEPSEEK_API_KEY", None)
    ans, err = rag_lib.call_deepseek("问题", "上下文", api_key=None)
    assert ans is None
    assert "DEEPSEEK_API_KEY" in err
