# 项目 2 · RAG 求职资料助手

基于你自己的课程资料做问答的 RAG 知识库。**答案带 `[编号]` 出处**，可点开核对。
这是「20 天冲刺 250」的第二个可演示项目，对应 Day 11–14 的学习成果。

## 技术栈

| 环节 | 方案 |
|------|------|
| 切分 | `RecursiveCharacterTextSplitter`（带 overlap=60，治「块被切断」） |
| 向量（主） | `fastembed` 中文语义向量 `BAAI/bge-small-zh-v1.5` + `FAISS` |
| 向量（兜底） | TF-IDF（纯标准库，语义引擎/模型不可用时自动降级，demo 不崩） |
| 生成 | DeepSeek `chat/completions`（OpenAI 兼容，纯 `requests` 调用） |
| 界面 | Streamlit |

## 本地运行

```bash
pip install -r day14/requirements.txt
export DEEPSEEK_API_KEY=sk-xxx        # 你的 DeepSeek key
streamlit run day14/app.py
```

## 部署到 Streamlit Cloud（拿在线链接）

1. 把本仓库连到 Streamlit Cloud（项目 1 已连过，直接复用）。
2. 新建一个 App，入口文件填 `day14/app.py`。
3. 在 **App Settings → Secrets** 里加：
   ```
   DEEPSEEK_API_KEY = "sk-xxx"
   ```
4. 推送即自动重新部署（仓库已配 GitHub Actions，每次 push 会先跑测试）。

## 效果数据（为什么从 TF-IDF 升级到语义向量）

同一组 3 个问题里，最关键的**第 3 题「RAG 为什么能缓解幻觉」**——

| 版本 | 检索抽到的 top-2 块 | 结论 |
|------|-------------------|------|
| Day12（TF-IDF） | Git 分支段 + DeepSeek API 段 | ❌ RAG 段**没进 top-2** → 引用错位 |
| Day13/14（语义向量） | `[1]` RAG 知识库原理 + `[2]` Git 分支 | ✅ RAG 段**进 top-1** → 答案正确标 `[1]` |

根因：TF-IDF 是字面匹配，「撰写」和「写」是俩不同词就搜不到；语义向量按「意思」匹配，相邻近。
这也是 Day 13 下午换 LangChain + 语义向量的理由，并写进了简历「项目 2」。

## 测试

```bash
pip install pytest requests
pytest day14/test_rag.py -q
```

CI（`.github/workflows/ci.yml`）在每次 push 到 main 时自动跑这一份测试，
覆盖 TF-IDF 兜底链路与 DeepSeek prompt 拼接（语义链路需下载模型，留本地/线上验证）。
