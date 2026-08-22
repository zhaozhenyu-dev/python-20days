def get_pass_students(students):
     result=[]
     for stu in  students:
          if stu["score"]>=60:
           result.append(stu["name"])
     return result

students = [
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 55},
    {"name": "王五", "score": 92},
]
passed = get_pass_students(students)
print(f"及格的有{len(passed)}人,{passed}")
for name in passed:
     print(f"  ✅ {name}")