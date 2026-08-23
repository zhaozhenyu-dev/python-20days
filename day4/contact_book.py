import json

class ContactBook:
    def __init__(self):
        self.contacts = self.load()     

    def load(self):
        try:
            with open("contacts.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []                    

    def save(self):
        with open("contacts.json", "w", encoding="utf-8") as f:
            json.dump(self.contacts, f, ensure_ascii=False, indent=2)

    def add(self, name, phone):
        self.contacts.append({"name": name, "phone": phone})
        self.save()                      

    def show_all(self):
        if not self.contacts:
            print("（通讯录为空）")
            return
        for c in self.contacts:
            print(f"- {c['name']}：{c['phone']}")



book = ContactBook()
book.show_all() 