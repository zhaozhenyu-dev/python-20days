students = [
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 92},
    {"name": "王五", "score": 78},
]

print(students[0])                 # 第 1 个学生的完整字典
print(students[0]["name"])         # 第 1 个学生的名字：张三
print(students[1]["score"])        # 第 2 个学生的分数：92

for stu in students:    
    print(f"{stu['name']}考了{stu['score']}分")
    if stu["score"] >= 90:
      print(f"{stu['name']}拿奖学金！")