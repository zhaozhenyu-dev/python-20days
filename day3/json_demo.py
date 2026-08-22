import json                                    
students = [                                  
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 92},
]

path = "/Users/zhaozhenyu/python-30days/day3/students.json"
with open(path, "w", encoding="utf-8") as f: 
    json.dump(students, f, ensure_ascii=False, indent=2)
print("写入成功")
with open(path, "r", encoding="utf-8") as f:
    loaded=json.load(f)
    print(loaded)
    print(loaded[0]["name"])