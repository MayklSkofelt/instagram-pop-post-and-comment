import asyncio
from apify import Actor
from apify_client import ApifyClient
from operator import itemgetter

async def main():
    async with Actor:
        # 1. Input maglumatlaryny okamak
        # Input_schema.json-daky 'targetUsername' bilen birmeňzeş bolmaly
        input_data = await Actor.get_input() or {}
        target_username = input_data.get("targetUsername")
        # target_username = "georginagio"
        top_posts_limit = input_data.get("topPostsLimit", 5)
        include_comments = input_data.get("includeComments", True)

        if not target_username:
            Actor.log.error("❌ Instagram username girizilmeli!")
            return

        Actor.log.info(f"📥 Ulanyjy: {target_username} | Limit: {top_posts_limit}")

        # 2. Apify Client-i Actor-yň öz tokeni bilen işe girizmek
        client = Actor.new_client()

        # 3. Instagram Postlaryny çekmek
        Actor.log.info(f"📡 {target_username} hasabyndan postlar alynýar...")
        
        run_input_posts = {
            "directUrls": [f"https://www.instagram.com/{target_username}/"],
            "resultsType": "posts",
            "resultsLimit": 50, # Seljermek üçin ilki 50 post alýarys
            "searchType": "hashtag",
            "proxyConfiguration": {"useApifyProxy": True}
        }

        # Başga bir Actor-y (Instagram Scraper) çagyrýarys
       # .call_async() ulanmak has gowudyr we await goýmaly
        run = await client.actor("apify/instagram-scraper").call(run_input=run_input_posts)
        # Dataset-den maglumatlary alanyňyzda hem await gerek
        dataset_client = client.dataset(run["defaultDatasetId"])
        posts = []
        async for item in dataset_client.iterate_items():
            posts.append(item)
        if not posts:
            Actor.log.warning("⚠️ Hiç hili post tapylmady!")
            return

        # 4. Like sany boýunça iň gowularyny saýlamak
        for p in posts:
            p["likeCount"] = p.get("likesCount", 0)

        posts_sorted = sorted(posts, key=itemgetter("likeCount"), reverse=True)
        top_posts = posts_sorted[:top_posts_limit]

        Actor.log.info(f"🔥 {len(top_posts)} sany meşhur post seljerilip başlanýar...")

        # 5. Her post üçin kommentleri ýygnamak
        final_data = []
        for post in top_posts:
            shortcode = post.get("shortCode")
            comments_data = []

            if include_comments and shortcode:
                Actor.log.info(f"💬 Kommentler alynýar: {shortcode}")
                run_input_comments = {
                    "directUrls": [f"https://www.instagram.com/p/{shortcode}/"],
                    "resultsType": "comments",
                    "resultsLimit": 100, # Her postdan 100 komment
                    "proxyConfiguration": {"useApifyProxy": True}
                }
                
                try:
                    run_comments = client.actor("apify/instagram-scraper").call(run_input=run_input_comments)
                    comments = list(client.dataset(run_comments["defaultDatasetId"]).iterate_items())
                    
                    for c in comments:
                        comments_data.append({
                            "user": c.get("ownerUsername"),
                            "text": c.get("text"),
                            "likes": c.get("likesCount", 0)
                        })
                except Exception as e:
                    Actor.log.error(f"⚠️ Komment çekmekde säwlik: {str(e)}")

            # Netijäni taýýarlamak
            post_result = {
                "postUrl": post.get("url"),
                "likes": post.get("likeCount"),
                "commentsCount": post.get("commentsCount"),
                "caption": post.get("caption"),
                "top_comments": comments_data
            }
            final_data.append(post_result)
            
            # Dataset-e ýazmak (Baryşy her postda görmek üçin)
            await Actor.push_data(post_result)

        Actor.log.info("✅ Iş üstünlikli tamamlandy!")

if __name__ == "__main__":
    asyncio.run(main())