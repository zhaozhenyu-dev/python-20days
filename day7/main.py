# day7/main.py —— 你的第一家店：收货 + 落库
import sqlite3                      # ① 账本钥匙（Python 自带，不用装）
from fastapi import FastAPI         # 进货：搬厨房设备
from pydantic import BaseModel, Field    # 进货：收货规格单 + Field（字段规则增强）

DB_NAME = "notes.db"                # 账本文件名（常量：以后只改这一处）

app = FastAPI()                     # 组装厨房


@app.get("/hello")                  # 挂菜单牌：登记 "/hello" 这道菜
def say_hello():                     # 这道菜的做法
    return {"msg": "hello"}          # 端出去的菜（自动变 JSON）


class Note(BaseModel):
    title: str = Field(..., min_length=1)   # 必填 + 至少 1 个字符（不能直接写 ""）
    content: str


# ---------- 开店前：把账本画好（只在加载时跑一次） ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)     # 开门（没有这文件就自动创建）
    conn.execute("""                    
        CREATE TABLE IF NOT EXISTS notes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT,
            content TEXT
        )
    """)
    conn.commit()                       # 盖章（建表也是写操作）
    conn.close()                        # 锁门


init_db()                               # 文件被加载的这一刻执行


@app.post("/notes")
def create_note(note: Note):
    conn = sqlite3.connect(DB_NAME)     # 开门
    cur = conn.execute(                 # 第 2 斧：记账（conn.execute 返回的正是 cursor 笔）
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (note.title, note.content),      # 填进两个 ? 的值（元组）
    )
    conn.commit()                       # 忘了这步 = 记假账
    new_id = cur.lastrowid              # 领号：刚那笔的行号
    conn.close()                        # 锁门
    return {"msg": "收到笔记", "id": new_id, "title": note.title}


@app.get("/notes")                      # 新菜：查账（GET，地址栏就能敲）
def list_notes():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT * FROM notes").fetchall()   # 第 3 斧：整本翻开
    conn.close()
    return {"count": len(rows), "notes": rows}

@app.delete("/notes/{note_id}")           # 挂牌：退货口，地址带坑位
def delete_note(note_id: int):            # 参数名必须和花括号里的一致
    conn = sqlite3.connect(DB_NAME)       # 开门
    cur = conn.execute(                   # 第 4 斧：删
        "DELETE FROM notes WHERE id = ?", # 删 id 等于 ? 的那一行（WHERE 不能忘！）
        (note_id,),                       # 3 填进坑（单元素元组）
    )
    deleted = cur.rowcount               # 这条 SQL 动了几行：1=删成，0=没这人
    conn.commit()                         # 删也是写操作，忘了 = 白删
    conn.close()                          # 锁门
    if deleted == 0:                     # 删了个寂寞 → 如实说
        return {"msg": "没找到这条笔记", "id": note_id}
    return {"msg": "已删除", "id": note_id}

@app.put("/notes/{note_id}")               # 挂牌：改单口
def update_note(note_id: int, note: Note):  # 两个参数：点名 + 内容
    conn = sqlite3.connect(DB_NAME)         # 开门
    cur = conn.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",  # 第 5 斧
        (note.title, note.content, note_id),  # 三个 ? 按序填空
    )
    updated = cur.rowcount                  # 动了几行
    conn.commit()                           # 改也是写操作
    conn.close()                            # 锁门
    if updated == 0:                       # 没这人
        return {"msg": "没找到这条笔记", "id": note_id}
    return {"msg": "已更新", "id": note_id, "title": note.title, "content": note.content}

