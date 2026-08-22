def word_stats():
   
    try:
        with open("day3/article.txt", "r", encoding="utf-8") as f:
            content = f.read()               
    except FileNotFoundError:               
        print("找不到 article.txt，先去建一个！")
        return     
    words = content.split()
    count = {}                               
    for word in words:                       
        count[word] = count.get(word, 0) + 1
    print(f"一共 {len(words)} 个词，其中不同单词 {len(count)} 个：\n")
    for word in count:                      
        print(f"{word}: {count[word]} 次")

word_stats()