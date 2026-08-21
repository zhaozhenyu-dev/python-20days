import random                        # 借用随机数工具箱

secret = random.randint(1, 100)      # 生成答案，randint(1,100)=抽1~100的随机整数
count = 0                            # 计数器：猜了几次

while True:                          # 开始无限循环
    guess = int(input("猜一个 1~100 的数："))   # 每轮让玩家猜一次
    count = count + 1                # 每猜一次，count 加 1
    if  guess>secret:
        print("大了，再试试")
    elif guess<secret:
        print("小了，再试试")
    else:
        print(f"恭喜！你猜了 {count} 次")
        break