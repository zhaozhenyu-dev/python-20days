import json

# —— 函数：读档案（文件不存在就给个空列表） ——
def load_contacts():
    try:
        with open("contacts.json", "r", encoding="utf-8") as f:
            return json.loads(f.read())       # 读到就还原成列表
    except FileNotFoundError:                    # 第一次运行还没有这文件
        return []                            
def save_contacts(contacts):
    with open("contacts.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(contacts, ensure_ascii=False, indent=2))
contacts = load_contacts()                     # 启动时先读旧档案
name = input("姓名：")
phone = input("电话：")
contacts.append({"name": name, "phone": phone})   # Day 2 的列表套字典
save_contacts(contacts)                        # 存回文件

print(f"已保存！通讯录共 {len(contacts)} 人：")          # Day 2 的 len
for c in contacts:                               # Day 2 的遍历
    print(f"- {c['name']}：{c['phone']}")            # Day 1 的 f-string