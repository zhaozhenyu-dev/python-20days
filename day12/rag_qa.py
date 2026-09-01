"""
Day12 RAG 知识库：生成 + 引用（自包含版）
复用 Day11 的检索基线（切分 / TF-IDF 向量 / 余弦检索），
新增第四步：把检索到的 top-k 块拼进 prompt，调 DeepSeek 生成"带出处"的答案。

运行（需先设好 DeepSeek key）：
    export DEEPSEEK_API_KEY=sk-xxx
    cd ~/python-20days
    python3 day12/rag_qa.py
"""

import os
import math
import re
import requests
from collections import Counter


# ============ 以下 4 个函数是 Day11 的检索基线（原样复用）============

def tokenize(text):
    """把文本变成"词"列表：英文/数字按词，中文按字。"""
    return re.findall(r"[a-zA-Z0-9]+|[一-鿿]", text.lower())


def chunk_text(text, size=300):
    """切分：每 size 个字符切一块。"""
    return [text[i:i + size] for i in range(0, len(text), size)]


def tfidf_vectors(docs):
    """把一批文档变成 TF-IDF 向量（{词: 权重} 字典，已 L2 归一化）。"""
    N = len(docs)
    df = Counter()
    per_doc = []
    for d in docs:
        c = Counter(tokenize(d))
        per_doc.append(c)
        for t in c:
            df[t] += 1
    vecs = []
    for c in per_doc:
        length = sum(c.values()) or 1
        vec = {}
        for t, cnt in c.items():
            tf = cnt / length
            idf = math.log((N + 1) / (df[t] + 1)) + 1
            vec[t] = tf * idf
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1
        vec = {t: v / norm for t, v in vec.items()}
        vecs.append(vec)
    return vecs


def cosine(a, b):
    """两个已归一化向量的余弦相似度 = 共同词权重乘积之和。"""
    return sum(a[t] * b[t] for t in set(a) & set(b))


def retrieve(chunks, question, top_k=3):
    """检索：把问题和每个块都向量化，按余弦相似度取最像的 top_k 块。"""
    vecs = tfidf_vectors(chunks)
    qvec = tfidf_vectors([question])[0]
    scored = [(i, cosine(qvec, vecs[i])) for i in range(len(vecs))]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]          # 返回 [(块号, 相似度), ...]


# ============ 以下 2 个函数是 Day12 新增：生成 + 引用 ============

def build_prompt(question, chunks, scored):
    """拼提示词：给每块贴 [编号]，命令模型只据资料答并标来源。"""
    lines = [
        "你是一个严谨的课程资料助手。下面是你【能用的唯一资料】，每段有编号。",
        "请只根据资料回答用户问题；如果资料里没有相关信息，就明确说'资料中未提及'。",
        "回答时，在依据的句子后面用 [编号] 标注来源。\n",
        "【资料】",
    ]
    for rank, (idx, score) in enumerate(scored, start=1):
        lines.append(f"[{rank}] {chunks[idx]}")
    lines.append("\n【用户问题】")
    lines.append(question)
    lines.append("\n【回答】")
    return "\n".join(lines)


def generate_answer(question, chunks, top_k=3):
    """RAG 第四步：检索 top-k 块 → 拼 prompt → 调 DeepSeek → 返回(答案, 被引块)。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY，请先 export 你的 key")

    scored = retrieve(chunks, question, top_k=top_k)
    prompt = build_prompt(question, chunks, scored)

    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是严谨的课程助手，回答必带 [编号] 出处。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    answer = resp.json()["choices"][0]["message"]["content"]

    # 回显被引用的原块，方便用户核对（"引用"三件套最后一步）
    cited = [(rank, idx, score) for rank, (idx, score) in enumerate(scored, start=1)]
    return answer, cited


def baseline_answer(question):
    """无引用对照组：不喂任何资料，直接把问题丢给 DeepSeek（纯凭模型记忆回答）。
    用来和 generate_answer 对比——看 RAG 的'依据资料 + 标出处'到底带来什么差别。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY，请先 export 你的 key")
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个乐于助人的助手。"},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ============ 演示：有引用 vs 无引用 对比 ============

if __name__ == "__main__":
    with open("day12/knowledge.txt", encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text, size=300)

    questions = ["周报助手怎么用", "怎么调用 DeepSeek API", "RAG 为什么能缓解幻觉"]

    for q in questions:
        print(f"\n========== 问：{q} ==========")

        print("\n----- 【A】有引用（RAG 知识库：先检索资料再答）-----")
        try:
            ans, cited = generate_answer(q, chunks, top_k=2)
            print(ans)
            print("--- 引用来源 ---")
            for rank, idx, score in cited:
                print(f"  [{rank}] 块{idx}（相似度 {score:.3f}）：{chunks[idx][:34]}...")
        except Exception as e:
            print(f"调用失败：{e}")

        print("\n----- 【B】无引用（直接问 DeepSeek，不喂资料）-----")
        try:
            base = baseline_answer(q)
            print(base)
        except Exception as e:
            print(f"调用失败：{e}")
