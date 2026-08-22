shopping = ["牛奶", "面包", "鸡蛋"]        

print(shopping)                           
print(f"一共 {len(shopping)} 样")         

shopping.append("西瓜")                    
print(shopping)         

shopping.remove("面包")
print(shopping)                            # 打印删除后的清单

print("最终清单：")
for item in shopping:
    print(f"{item}")