"""
Day13 RAG 知识库（LangChain 升级版）
==================================
对照 Day12 验收暴露的问题升级两处：
  1) 切分：用 RecursiveCharacterTextSplitter + overlap，治「块被切断」
  2) 向量：用 FastEmbed 语义向量替换 TF-IDF，治「撰写≠写」字面坑
再用 LangChain 把「切分→向量→检索→生成」串成标准流水线。

运行（需先设好 DeepSeek key）：
    export DEEPSEEK_API_KEY=sk-xxx
    cd ~/python-20days
    python3 day13/rag_langchain.py
首次运行会从 HuggingFace 下载中文向量模型 bge-small-zh-v1.5（约 100+ MB）。
"""

import os

# ---------- LangChain 零件导入 ----------
import fastembed  # 语义向量引擎（底层，绕过 langchain 包装以便离线加载）
from langchain_core.embeddings import Embeddings  # 自定义嵌入需继承它
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# 预下载好的中文向量模型所在缓存目录（详见讲义「离线加载」说明）
FASTEMBED_CACHE = "/Users/zhaozhenyu/.workbuddy/fastembed_cache"


# ============ ② 向量化：FastEmbed 语义向量（治「撰写≠写」）============
# 说明：本沙箱代理拦 HuggingFace，故模型已用 curl 预下载到 FASTEMBED_CACHE，
# 并用 local_files_only=True 离线加载。你本机网络正常时，可直接用
#   from langchain_community.embeddings import FastEmbedEmbeddings
#   embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
# 效果完全一样，只是不用手动下载。
class LocalFastEmbedEmbeddings(Embeddings):
    """把 fastembed.TextEmbedding 包成 LangChain 的 Embeddings 接口，
    这样 FAISS.from_documents 就能直接用它。核心就两个方法：
      embed_documents -> 给一批文本算向量（建库用）
      embed_query     -> 给单个问题算向量（检索用）"""

    def __init__(self, model_name="BAAI/bge-small-zh-v1.5",
                 cache_dir=FASTEMBED_CACHE):
        self._model = fastembed.TextEmbedding(
            model_name=model_name,
            cache_dir=cache_dir,
            local_files_only=True,   # 关键：只从本地缓存读，绝不联网
        )

    def embed_documents(self, texts):
        # embed() 返回迭代器，每个是 numpy 数组 -> 转成普通 list 给 FAISS
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text):
        return list(self._model.embed([text]))[0].tolist()


# ============ ① 切分：重叠切分（治 Day12「块被切断」）============
def load_and_split(path="day13/knowledge.txt", chunk_size=300, overlap=60):
    """读资料 → 用带 overlap 的切分器切成块。
    overlap=60 表示相邻两块重叠 60 个字符，一句话跨边界也不会被腰斩。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,      # 每块最多 300 字
        chunk_overlap=overlap,      # 块间重叠 60 字
        separators=["\n\n", "\n", "。", "，", ""],  # 优先在段落/句号处切
    )
    return splitter.create_documents([text])


# ============ ② 向量化：FastEmbed 语义向量（治「撰写≠写」）============
def build_vectorstore(docs):
    """把切好的块变成语义向量，存进 FAISS 向量库。
    模型 bge-small-zh-v1.5 是中文专用，意思相近的句子向量也相近。"""
    embeddings = LocalFastEmbedEmbeddings()
    return FAISS.from_documents(docs, embeddings)


# ============ ④ 取块 + ⑤ 生成：检索 → 拼 prompt → DeepSeek 链 ============
def make_chain(vectorstore, top_k=2):
    """组装 RAG 链：检索 top-k 块 → 拼上下文 → DeepSeek 生成带出处答案。"""
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    # ⑤ 的 prompt 模板（和 Day12 build_prompt 同思路，但用 {context}/{question} 占位符）
    prompt = PromptTemplate.from_template(
        "你是一个严谨的课程资料助手。下面是你【能用的唯一资料】，每段有编号。\n"
        "请只根据资料回答用户问题；如果资料里没有相关信息，就明确说'资料中未提及'。\n"
        "回答时，在依据的句子后面用 [编号] 标注来源。\n\n"
        "【资料】\n{context}\n\n【用户问题】\n{question}\n\n【回答】"
    )

    # ⑤ 的 LLM：DeepSeek 是 OpenAI 兼容接口，所以直接用 ChatOpenAI 指向它
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0.3,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1",  # 关键点：把 OpenAI 地址换成 DeepSeek
        max_tokens=512,
    )

    # ⑤ 的解析器：把模型返回的消息对象 → 纯文本字符串
    parser = StrOutputParser()

    # 检索是单独一步（为了能打印「抽到了哪些块」证明检索升级生效）
    def answer(question):
        hits = retriever.invoke(question)            # ④ 取块
        context = "\n".join(
            f"[{i+1}] {d.page_content}" for i, d in enumerate(hits)
        )
        # ⑤ 用 LCEL 把 prompt | llm | parser 串成一条链
        chain = prompt | llm | parser
        return chain.invoke({"context": context, "question": question}), hits

    return answer


# ============ 演示：同 Day12 三个问题，看语义检索是否修好错位 ============
if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY，请先 export 你的 key")

    docs = load_and_split()
    print(f"切出 {len(docs)} 个块（带 overlap）")

    store = build_vectorstore(docs)
    ask = make_chain(store, top_k=2)

    questions = [
        "周报助手怎么用",
        "怎么调用 DeepSeek API",
        "RAG 为什么能缓解幻觉",   # Day12 这一题 RAG 段没进 top-2，今天应修好
    ]

    for q in questions:
        print(f"\n========== 问：{q} ==========")
        ans, hits = ask(q)
        print("--- 检索到的资料块（证明语义向量生效）---")
        for i, d in enumerate(hits, 1):
            print(f"  [{i}] {d.page_content[:42]}...")
        print("--- 答案 ---")
        print(ans)
