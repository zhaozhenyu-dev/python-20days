
scores = [85, 92, 78, 95, 60]
print(f"(有{len(scores)}个成绩)")
print(f"(最高分:{max(scores)})")
print(f"最低分：{min(scores)}")   
print(f"平均分：{sum(scores) / len(scores):.2f}")

scores.append(88)
print(scores)

for s in scores:
    if s >= 90:
        print(f"{s} 分，优秀！")
    elif s>60:
        print(f"{s}分，良好")
    else:
        print(f"{s}分，不及格")