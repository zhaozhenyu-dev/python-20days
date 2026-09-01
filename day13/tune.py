"""
Day13 上午：RAG 调优实验
复用 Day12 的 TF-IDF 检索（切分 / 向量 / 余弦），
做三件事：
  1) 扫 chunk_size ∈ {100, 300}、top_k ∈ {2, 3, 5}，统计 10 道测试题的检索命中率；
  2) 加「兜底阈值」：top 相似度 < 阈值 判为「资料中未提及」；
  3) 输出「调前(Day12默认 300/2) vs 调后(最佳)」对照，定位引用错位根因。

运行：
    cd ~/python-20days
    /usr/local/bin/python3 day13/tune.py
"""
import os
import sys

# 复用 Day12 已经写好的检索函数（切分 / TF-IDF 向量 / 余弦 / 检索）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day12"))
from rag_qa import chunk_text, tfidf_vectors, cosine, retrieve


# ---------- 实验配置 ----------
LOW_CONF_THRESHOLD = 0.05          # 兜底：top1 相似度低于此值 → 低置信（疑似未提及）
CHUNK_SIZES = [100, 300]
TOP_KS = [2, 3, 5]

# 10 道测试题：(问题, 该题「正确答案所在段」的唯一关键短语)
# 只要 top-k 抽出的块里出现这个短语，就算「检索命中」
TESTS = [
    ("周报助手怎么用",               "三段式周报"),
    ("怎么调用 DeepSeek API",        "api.deepseek.com"),
    ("怎么部署到 Streamlit Cloud",    "Streamlit Cloud"),
    ("怎么给函数写单元测试",          "unittest.mock"),
    ("git 分支工作流怎么走",          "Pull Request"),
    ("RAG 为什么能缓解幻觉",          "检索增强生成"),
    ("周报的 temperature 设多少合适",  "0.3"),
    ("API Key 怎么读才安全",          "os.getenv"),
    ("怎么让模型回答别太发散",        "temperature"),
    ("部署成功后的网址长什么样",       "https 开头的网址"),
]


def evaluate(text, size, k):
    """对给定的 (chunk_size, top_k)，返回 (命中数, 每题明细)。"""
    chunks = chunk_text(text, size=size)
    detail = []
    hits = 0
    for q, key in TESTS:
        scored = retrieve(chunks, q, top_k=k)
        top_idxs = [i for i, _ in scored]
        top_sim = scored[0][1]
        low_conf = top_sim < LOW_CONF_THRESHOLD
        hit = any(key in chunks[i] for i in top_idxs)
        hits += int(hit)
        detail.append((q, top_idxs, round(top_sim, 3), low_conf, hit))
    return hits, detail


if __name__ == "__main__":
    with open("day13/knowledge.txt", encoding="utf-8") as f:
        text = f.read()

    print(f"测试题：{len(TESTS)} 道 ｜ 兜底阈值：{LOW_CONF_THRESHOLD}")
    print("=" * 60)
    print("【一、命中率总表：chunk_size × top_k】")
    print(f"{'chunk_size':>11} | {'top_k':>5} | {'命中':>6}")
    print("-" * 30)
    best = (0, None, None)
    for size in CHUNK_SIZES:
        for k in TOP_KS:
            hits, _ = evaluate(text, size, k)
            print(f"{size:>11} | {k:>5} | {hits}/{len(TESTS)}")
            if hits > best[0]:
                best = (hits, size, k)
    print("-" * 30)
    print(f"→ 最佳组合：chunk_size={best[1]}, top_k={best[2]}，命中 {best[0]}/{len(TESTS)}")

    print("\n【二、调前(Day12默认 300/2) vs 调后(最佳) 逐题对照】")
    before_hits, before = evaluate(text, 300, 2)
    after_hits, after = evaluate(text, best[1], best[2])
    print(f"{'问题':<24}{'调前top1':>9}{'调后top1':>9}{'调前':>9}{'调后':>9}")
    for (q, b_idx, b_sim, b_low, b_hit), (_, a_idx, a_sim, a_low, a_hit) in zip(before, after):
        bmark = "✅" if b_hit else ("⚠️低置信" if b_low else "❌")
        amark = "✅" if a_hit else ("⚠️低置信" if a_low else "❌")
        print(f"{q:<22}{str(b_idx[0]):>9}{str(a_idx[0]):>9}{bmark:>10}{amark:>10}")
    print(f"\n调前命中 {before_hits}/{len(TESTS)}  →  调后命中 {after_hits}/{len(TESTS)}")

    print("\n【三、兜底样例：调后配置里 top1 相似度低于阈值的题】")
    flagged = False
    for q, idxs, sim, low, hit in after:
        if low:
            flagged = True
            print(f"  · {q} → top1 相似度仅 {sim}（<{LOW_CONF_THRESHOLD}），应回『资料中未提及』")
    if not flagged:
        print("  （本轮无低置信题，说明参数下检索都较稳）")

    print("\n结论：TF-IDF 命中率受 chunk_size/top_k 影响，但本质是『字面匹配』——")
    print("      下午用 fastembed 语义向量，才能真解决 Day12 的『撰写≠写』引用错位。")
