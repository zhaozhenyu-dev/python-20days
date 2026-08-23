class BankAccount:
     def __init__(self, owner):
        self.owner = owner        
        self.balance = 0          
     def deposit(self, amount):    
        self.balance += amount

     def withdraw(self, amount):  
        if self.balance >= amount:
            self.balance -= amount
        else:
            print("余额不足")
    
     def get_balance(self):       
        return self.balance

acc = BankAccount("张三")
acc.deposit(100)          
acc.deposit(50)           
acc.withdraw(200)         
acc.withdraw(120)        
print(acc.get_balance())  