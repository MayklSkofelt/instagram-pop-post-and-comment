import os
import asyncio
from apify_client import ApifyClient

# --- Apify client --- #
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
client = ApifyClient(APIFY_TOKEN)

# --- Input --- #
# Bu actor-a beriljek input görnüşi
INPUT = {
    "username": "",          # Instagram ulanyjy ady
    "password": "",          # Instagram paroly (optionally)
    "target_user": "",       # Postlaryny yzarlamak isleýän ulanyjy
    "min_likes": 100         # Minimal like sany bilen postlary alyp bolar
}

# --- Crawler setup --- #
async def main():
    username = INPUT["username"]
    password = INPUT["password"]
    target_user = INPUT["target_user"]
    min_likes = INPUT["min_likes"]

    if not target_user:
        print("Target user görkezilmän!")
        return

    print(f"Instagram {target_user} postlaryny gözleýär...")

    # Bu ýerde Instagram scraping logikasy bolar
    # Mysal üçin, CheerioCrawler bilen sahypa HTML analiz edip bilersiňiz
    # Hakyky scraping koduny Instagram API ýa-da HTML parsing bilen ulanmaly

    # Dummy maglumat (demo üçin)
    posts = [
        {"id": "1", "likes": 150, "caption": "Post 1", "comments": ["Wow!", "Super!"]},
        {"id": "2", "likes": 50, "caption": "Post 2", "comments": ["Nice"]},
        {"id": "3", "likes": 200, "caption": "Post 3", "comments": ["Awesome", "Cool"]}
    ]

    # Minimal like bilen filterlemek
    popular_posts = [p for p in posts if p["likes"] >= min_likes]

    for post in popular_posts:
        print(f"Post ID: {post['id']}, Likes: {post['likes']}")
        print("Comments:")
        for comment in post["comments"]:
            print(f"- {comment}")

    # Netijeleri Apify dataset-e ýazmak
    dataset = await client.dataset("INSTAGRAM_POP_POSTS").open()
    for post in popular_posts:
        await dataset.push_items(post)

# --- Run --- #
if __name__ == "__main__":
    asyncio.run(main())
