movie = {                               
    "title": "流浪地球2",
    "director": "郭帆",
    "year": 2023,
    "rating": 8.5,
    "tags": ["科幻", "太空", "灾难"],     
}


print(f"《{movie['title']}》是 {movie['director']} 执导的 {movie['year']} 年电影，评分 {movie['rating']}")


movie["rating"] = 9.0                  
print(f"二刷之后，我的评分改成了 {movie['rating']}")


movie["观后感"] = "特效炸裂，剧情也比第一部更扎实。"
print(f"我的观后感：{movie['观后感']}")
print("---- 全部信息 ----")
for key,value in  movie.items():     
    print(f"{key}: {value}")