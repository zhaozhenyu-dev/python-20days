def safe_calculator():
    while True:                                        
        expr = input("请输入算式（如 10 / 2，输入 exit 退出）：")
        if expr == "exit":                              
            print("再见")
            break
        parts = expr.split()                             # 按空格切成三块：数字 运算符 数字
        if len(parts) != 3:                              # 格式不对
            print("格式错误，请按「数字 运算符 数字」输入")
            continue     
        a_str, op, b_str = parts  
        try:
            a = float(a_str)                             # 转浮点数
            b = float(b_str)
        except ValueError:
            print("请输入数字")
            continue
        if op == "+":
            print(f"{a} + {b} = {a + b}")
        elif op == "-":
            print(f"{a} - {b} = {a - b}")
        elif op == "*":
            print(f"{a} * {b} = {a * b}")
        elif op == "/":
            if b == 0:                                   # 除零保护
                print("不能除以 0")
            else:
                print(f"{a} / {b} = {a / b}")
        else:
            print("不支持该运算符")                       # 运算符不认识

safe_calculator()