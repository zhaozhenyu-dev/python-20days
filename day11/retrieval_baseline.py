"""
Day11 检索基线：纯 Python 实现 TF-IDF + 余弦相似度（零依赖，无需安装任何库）。
对应 RAG 四步链的前三步：切分 → 向量化 → 检索（生成留 Day12）。
"""
import math
import re
from collections import Counter


def tokenize(text):
    """把文本变成"词"列表：英文/数字按词，中文按字（中文没有空格，按字最稳）。"""
    return re.findall(r"[a-zA-Z0-9]+|[一-鿿]", text.lower())


def chunk_text(text, size=300):
    """切分：每 size 个字符切一块。"""
    return [text[i:i + size] for i in range(0, len(text), size)]


def tfidf_vectors(docs):
    """把一批文档变成 TF-IDF 向量（每个向量是 {词: 权重} 的字典，已 L2 归一化）。"""
    N = len(docs)
    df = Counter()                      # 记录每个词在多少篇文档出现过
    per_doc = []
    for d in docs:
        c = Counter(tokenize(d))
        per_doc.append(c)
        for t in c:
            df[t] += 1

    vecs = []
    for c in per_doc:
        length = sum(c.values()) or 1   # 这篇文档的总词数（防除零）
        vec = {}
        for t, cnt in c.items():
            tf = cnt / length            # 词频：这个词在这篇里占比
            idf = math.log((N + 1) / (df[t] + 1)) + 1   # 逆文档频率：越少见的词越重要
            vec[t] = tf * idf
        norm = math.sqrt(sum(v * v for v in vec.values()))  # L2 归一化，方便直接点积=余弦
        if norm > 0:
            vec = {t: v / norm for t, v in vec.items()}
        vecs.append(vec)
    return vecs


def cosine(a, b):
    """两个已归一化向量的余弦相似度 = 共同词权重乘积之和。"""
    return sum(a[t] * b[t] for t in set(a) & set(b))


def retrieve(chunks, question, top_k=3):
    vecs = tfidf_vectors(chunks)
    qvec = tfidf_vectors([question])[0]
    scored = [(i, cosine(qvec, vecs[i])) for i in range(len(vecs))]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


if __name__ == "__main__":
    with open("day11/sample.txt", encoding="utf-8") as f:
        text = f.read()

    questions = [
        "周报应该怎么写",
        "怎么调用 DeepSeek API",
        "怎么部署到 Streamlit",
        "pytest 测试怎么写",
        "git 分支怎么用",
    ]

    for size in (100, 300, 600):
        chunks = chunk_text(text, size=size)
        print(f"\n===== chunk_size={size}，共切出 {len(chunks)} 块 =====")
        for q in questions:
            print(f"\n问题：{q}")
            for idx, sc in retrieve(chunks, q, top_k=1):
                print(f"  命中第{idx}块  相似度={sc:.3f}：{chunks[idx][:60]}...")
