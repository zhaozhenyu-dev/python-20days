students = [
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 92},
    {"name": "王五", "score": 78},
    {"name": "赵六", "score": 95},
    {"name": "孙七", "score": 60},
]
def get_average(students):
    total = 0
    for stu in students:
        total += stu["score"]
    return total / len(students)

def get_top_student(students):
    top = students[0]
    for stu in students:
        if stu["score"] > top["score"]:
            top = stu
    return top
average = get_average(students)
top = get_top_student(students)
print(f"平均分是{average:.2f}")
average = get_average(students)
print(f"最高分是 {top['name']}，考了 {top['score']} 分")