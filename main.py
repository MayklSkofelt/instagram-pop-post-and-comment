from apify import Actor
from apify_client import ApifyClient
from operator import itemgetter

async def main():
    async with Actor:
        # ===============================
        # INPUT OKA
        # ===============================
        input_data = await Actor.get_input() or {}

        target_username = input_data.get("targetUsername")
        top_posts_limit = input_data.get("topPostsLimit", 5)
        include_comments = input_data.get("includeComments", True)

        if not target_username:
            raise Exception("❌ Instagram username girizilmeli!")

        Actor.log.info(f"📥 Target user: {target_username}")
        Actor.log.info(f"⭐ Top posts limit: {top_posts_limit}")
        Actor.log.info(f"💬 Include comments: {include_comments}")

        # ===============================
        # APIFY CLIENT
        # ===============================
        client = ApifyClient(Actor.get_env().get("APIFY_TOKEN"))

        # ===============================
        # 1️⃣ POSTLARY AL
        # ===============================
        run_input_posts = {
            "directUrls": [f"https://www.instagram.com/{target_username}/"],
            "resultsType": "posts",
            "resultsLimit": 50,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        Actor.log.info("📡 Instagram postlar alnyp başlanýar...")

        run = client.actor("apify/instagram-scraper").call(run_input=run_input_posts)
        posts = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        if not posts:
            Actor.log.warning("⚠️ Post tapylmady!")
            return

        # ===============================
        # 2️⃣ LIKE BOÝUNÇA SORT
        # ===============================
        for p in posts:
            p["likeCount"] = p.get("likesCount", 0)

        posts_sorted = sorted(posts, key=itemgetter("likeCount"), reverse=True)
        top_posts = posts_sorted[:top_posts_limit]

        Actor.log.info(f"🔥 {len(top_posts)} sany iň köp like alan post saýlandy")

        # ===============================
        # 3️⃣ DATASET
        # ===============================
        dataset = await Actor.open_dataset()

        # ===============================
        # 4️⃣ HER POST ÜÇIN KOMMENT
        # ===============================
        for post in top_posts:
            shortcode = post.get("shortCode")
            comments_data = []

            if include_comments and shortcode:
                Actor.log.info(f"💬 Kommentler alnyp başlanýar → {shortcode}")

                run_input_comments = {
                    "directUrls": [f"https://www.instagram.com/p/{shortcode}/"],
                    "resultsType": "comments",
                    "resultsLimit": 300,
                    "proxyConfiguration": {"useApifyProxy": True}
                }

                try:
                    run_comments = client.actor("apify/instagram-scraper").call(
                        run_input=run_input_comments
                    )
                    comments = list(
                        client.dataset(run_comments["defaultDatasetId"]).iterate_items()
                    )

                    for c in comments:
                        comments_data.append({
                            "username": c.get("ownerUsername"),
                            "text": c.get("text"),
                            "likes": c.get("likesCount", 0),
                            "repliedTo": c.get("repliedToCommentId")
                        })

                except Exception as e:
                    Actor.log.warning(f"⚠️ Komment ýalňyşlygy: {e}")

            # ===============================
            # 5️⃣ DATASET-E ÝAZ
            # ===============================
            await dataset.push_data({
                "username": target_username,
                "postUrl": post.get("url"),
                "shortcode": shortcode,
                "caption": post.get("caption"),
                "likes": post.get("likeCount"),
                "commentsCount": post.get("commentsCount"),
                "takenAt": post.get("timestamp"),
                "comments": comments_data
            })

        Actor.log.info("✅ Ähli maglumatlar üstünlikli ýygnaldy!")
