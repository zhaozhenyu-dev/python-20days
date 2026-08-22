from datetime import datetime

def diary():
    while True:
        content = input("写点什么（输入 exit 结束）：")

        if content == "exit":
            print("日记已保存，再见！")
            break

        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M")

        with open("day3/diary.txt", "a", encoding="utf-8") as f:
            f.write(f"[{time_str}] {content}\n")

        print("已记录！")

diary()