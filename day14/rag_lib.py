"""
Day14 项目 2（RAG 知识库）核心逻辑库
====================================
把「检索 + 生成」拆成纯逻辑，方便 Streamlit 界面(day14/app.py)调用、也方便 pytest 测。
设计原则：
  - 主检索 = 语义向量(FAISS + fastembed 中文模型)，效果最好；
  - 兜底检索 = TF-IDF(纯标准库，零依赖)，万一语义向量引擎/模型下载失败，demo 也不崩；
  - 生成 = 纯 requests 调 DeepSeek(OpenAI 兼容)，不依赖 langchain 的 LLM 封装，最稳。
注意：本文件顶部只 import 标准库 + requests，langchain 只在函数内部按需 import，
      这样 CI 里没装 langchain 也能跑测试（语义检索会自动降级到 TF-IDF）。
"""
import os
import math
import re
from collections import Counter

import requests  # 生成步骤用，CI 里也装得上（轻量）


# ===================== TF-IDF 兜底检索（纯标准库，永远可用）=====================
def tokenize(text):
    """英文/数字按词，中文按字（中文没空格，按字最稳）。"""
    return re.findall(r"[a-zA-Z0-9]+|[一-鿿]", text.lower())


def chunk_text(text, size=300):
    """每 size 个字符切一块（兜底切分，无 overlap）。"""
    return [text[i:i + size] for i in range(0, len(text), size)]


def split_docs(text, size=300, overlap=60):
    """优先用 LangChain 重叠切分（治『块被切断』）；没有 langchain 就退回简单切分。"""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        sp = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", "，", ""],
        )
        return [d.page_content for d in sp.create_documents([text])]
    except Exception:
        return chunk_text(text, size=size)


def tfidf_vectors(docs):
    """一批文档 → TF-IDF 向量（{词:权重}，已 L2 归一化，点积即余弦）。"""
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
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            vec = {t: v / norm for t, v in vec.items()}
        vecs.append(vec)
    return vecs


def cosine(a, b):
    """两归一化向量的余弦相似度 = 共同词权重乘积之和。"""
    return sum(a[t] * b[t] for t in set(a) & set(b))


def retrieve_tfidf(chunks, question, top_k=3):
    """TF-IDF 检索：返回 [(块索引, 相似度), ...] 取 top_k。"""
    vecs = tfidf_vectors(chunks)
    qvec = tfidf_vectors([question])[0]
    scored = [(i, cosine(qvec, vecs[i])) for i in range(len(vecs))]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


# ===================== 语义向量主检索（langchain + fastembed）=====================
def build_semantic_retriever(chunks, model_name="BAAI/bge-small-zh-v1.5"):
    """建 FAISS 语义向量库并返回 retriever。失败返回 None（调用方降级到 TF-IDF）。"""
    try:
        from langchain_community.embeddings import FastEmbedEmbeddings
        from langchain_community.vectorstores import FAISS
        emb = FastEmbedEmbeddings(model_name=model_name)  # 线上首次会自动下载模型
        store = FAISS.from_texts(chunks, emb)
        return store.as_retriever(search_kwargs={"k": 3})
    except Exception:
        return None


# ===================== 生成：纯 requests 调 DeepSeek =====================
def call_deepseek(question, context, api_key=None):
    """用 DeepSeek(OpenAI 兼容) 生成『只据资料、标[编号]』的答案。
    返回 (answer_text, error_or_None)。没有 key 或出错时 answer=None。"""
    key = api_key or os.getenv("DEEPSEEK_API_KEY") or ""
    if not key:
        return None, "未配置 DEEPSEEK_API_KEY（可在 Streamlit Cloud 的 Secrets 里设置）"

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    system = (
        "你是一个严谨的课程资料助手。下面是你【能用的唯一资料】，每段有编号。\n"
        "请只根据资料回答用户问题；资料里没有相关信息就明确说『资料中未提及』。\n"
        "回答时在依据的句子后边用 [编号] 标注来源。"
    )
    user = f"【资料】\n{context}\n\n【用户问题】\n{question}\n\n【回答】"
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=40)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"调用 DeepSeek 失败：{e}"


# ===================== 组装：一个问题的完整 RAG 回答 =====================
def answer(question, knowledge_text, api_key=None):
    """对外主函数：输入问题 + 资料全文，返回 (答案, 命中的块列表, 检索方式, 错误)。
    检索优先语义向量，失败自动降级 TF-IDF；生成失败则返回命中块让读者自查。"""
    chunks = split_docs(knowledge_text)
    sem = build_semantic_retriever(chunks)
    if sem is not None:
        try:
            hits_docs = sem.invoke(question)
            hits = [d.page_content for d in hits_docs]
            mode = "语义向量(FAISS+bge-small-zh)"
        except Exception:
            sem = None
    if sem is None:
        scored = retrieve_tfidf(chunks, question, top_k=3)
        hits = [chunks[i] for i, _ in scored]
        mode = "TF-IDF(兜底)"

    context = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(hits))
    ans, err = call_deepseek(question, context, api_key=api_key)
    return ans, hits, mode, err
