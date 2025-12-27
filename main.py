import asyncio
from apify import Actor
from apify_client import ApifyClient
from operator import itemgetter

async def main():
    async with Actor:
        # 1. Input maglumatlaryny okamak
        input_data = await Actor.get_input() or {}
        target_username = input_data.get("targetUsername")
        top_posts_limit = input_data.get("topPostsLimit", 5)
        include_comments = input_data.get("include_comments", True) # Käte 'includeComments' bolup biler

        if not target_username:
            Actor.log.error("❌ Instagram username girizilmeli!")
            return

        Actor.log.info(f"📥 Ulanyjy: {target_username} | Limit: {top_posts_limit}")

        # 2. Apify Client-i asinhron görnüşde işe girizmek
        client = Actor.new_client()

        # 3. Instagram Postlaryny çekmek
        Actor.log.info(f"📡 {target_username} hasabyndan postlar alynýar...")
        
        run_input_posts = {
            "directUrls": [f"https://www.instagram.com/{target_username}/"],
            "resultsType": "posts",
            "resultsLimit": 50,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        # Instagram Scraper-y çagyrýarys we netijesine garaşýarys (await)
        run = await client.actor("apify/instagram-scraper").call(run_input=run_input_posts)
        
        # Dataset-den itemlary asinhron list görnüşinde alýarys
        posts_iter = client.dataset(run["defaultDatasetId"]).iterate_items()
        posts = [item async for item in posts_iter]

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
        for post in top_posts:
            shortcode = post.get("shortCode")
            comments_data = []

            if include_comments and shortcode:
                Actor.log.info(f"💬 Kommentler alynýar: {shortcode}")
                run_input_comments = {
                    "directUrls": [f"https://www.instagram.com/p/{shortcode}/"],
                    "resultsType": "comments",
                    "resultsLimit": 100,
                    "proxyConfiguration": {"useApifyProxy": True}
                }
                
                try:
                    # Komment skraperini çagyrýarys we garaşýarys (await)
                    run_comments = await client.actor("apify/instagram-scraper").call(run_input=run_input_comments)
                    
                    # Kommentleri dataset-den çekip alýarys
                    comments_iter = client.dataset(run_comments["defaultDatasetId"]).iterate_items()
                    async for c in comments_iter:
                        comments_data.append({
                            "user": c.get("ownerUsername"),
                            "text": c.get("text"),
                            "likes": c.get("likesCount", 0)
                        })
                except Exception as e:
                    Actor.log.error(f"⚠️ Komment çekmekde säwlik: {str(e)}")

            # Netijäni Dataset-e ýazmak
            post_result = {
                "username": target_username,
                "postUrl": post.get("url"),
                "shortcode": shortcode,
                "likes": post.get("likeCount"),
                "commentsCount": post.get("commentsCount"),
                "caption": post.get("caption"),
                "takenAt": post.get("timestamp"),
                "top_comments": comments_data
            }
            await Actor.push_data(post_result)

        Actor.log.info("✅ Iş üstünlikli tamamlandy!")

if __name__ == "__main__":
    asyncio.run(main())