class Student:
    def __init__(self, name, score):  
        self.name = name
        self.score = score
    def get_grade(self):               # 返回等级
        return "优秀" if self.score >= 90 else ("及格" if self.score >= 60 else "不及格")
    def introduce(self):               # 打印自我介绍
        print(f"我是{self.name}，考了{self.score}分，等级：{self.get_grade()}")
    
stu1 = Student("张三", 85)
stu2 = Student("李四", 59)
stu3 = Student("王五", 95)
stu1.introduce(); stu2.introduce(); stu3.introduce()