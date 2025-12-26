import asyncio
from datetime import datetime
from apify import Actor
from apify_client import ApifyClient


# ========= MEDIA =========
def extract_media_list(post):
    media_list = []

    if post.get("childPosts"):
        for child in post["childPosts"]:
            m = _extract_media(child)
            if m:
                media_list.append(m)
    elif post.get("carousel_media"):
        for item in post["carousel_media"]:
            m = _extract_media(item)
            if m:
                media_list.append(m)
    else:
        m = _extract_media(post)
        if m:
            media_list.append(m)

    return media_list


def _extract_media(item):
    if item.get("videoUrl"):
        return {"url": item["videoUrl"], "type": "video"}
    if item.get("video_versions"):
        return {"url": item["video_versions"][0]["url"], "type": "video"}

    image_url = item.get("displayUrl")
    if not image_url and item.get("image_versions2", {}).get("candidates"):
        image_url = item["image_versions2"]["candidates"][0].get("url")

    if image_url:
        return {"url": image_url, "type": "image"}

    return None


# ========= APIFY =========
def get_posts(username, client, limit):
    run_input = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsType": "posts",
        "resultsLimit": limit,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def get_post_comments(shortcode, client, limit):
    run_input = {
        "directUrls": [f"https://www.instagram.com/p/{shortcode}/"],
        "resultsType": "comments",
        "resultsLimit": limit,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


# ========= MAIN =========
async def main():
    async with Actor:
        input = await Actor.get_input() or {}

        users = input.get("users", [])
        post_limit = input.get("postLimit", 12)
        comment_limit = input.get("commentLimit", 300)
        top_count = input.get("topPostsCount", 3)
        followers = input.get("followersCount", 0)

        if not users:
            raise ValueError("Input içinde users ýok!")

        client = ApifyClient(Actor.config.token)

        for username in users:
            Actor.log.info(f"📡 Analiz başlady: {username}")

            posts = await asyncio.to_thread(
                get_posts, username, client, post_limit
            )

            user_posts = []

            for post in posts:
                shortcode = post.get("shortCode")
                if not shortcode:
                    continue

                likes = post.get("likesCount", 0)
                comments_count = post.get("commentsCount", 0)

                taken_at = post.get("takenAt") or post.get("timestamp")
                if isinstance(taken_at, (int, float)):
                    post_time = datetime.fromtimestamp(taken_at).isoformat()
                else:
                    post_time = str(taken_at)

                media = extract_media_list(post)

                comments = await asyncio.to_thread(
                    get_post_comments,
                    shortcode,
                    client,
                    comment_limit,
                )

                parsed_comments = [{
                    "user": c.get("ownerUsername"),
                    "text": c.get("text"),
                    "replyTo": (
                        c.get("repliedToComment", {}).get("ownerUsername")
                        if c.get("repliedToComment") else None
                    )
                } for c in comments]

                engagement_rate = None
                if followers > 0:
                    engagement_rate = round(
                        (likes + comments_count) / followers,
                        6
                    )

                post_data = {
                    "type": "POST",
                    "username": username,
                    "shortcode": shortcode,
                    "postTime": post_time,
                    "caption": post.get("caption"),
                    "likes": likes,
                    "commentsCount": comments_count,
                    "engagementRate": engagement_rate,
                    "media": media,
                    "comments": parsed_comments,
                }

                user_posts.append({
                    "shortcode": shortcode,
                    "likes": likes,
                    "comments": comments_count,
                    "engagementRate": engagement_rate,
                    "caption": post.get("caption"),
                    "media": media,
                    "postTime": post_time,
                })

                await Actor.push_data(post_data)

            # ===== TOP LISTLER =====
            top_liked = sorted(
                user_posts, key=lambda x: x["likes"], reverse=True
            )[:top_count]

            top_commented = sorted(
                user_posts, key=lambda x: x["comments"], reverse=True
            )[:top_count]

            top_engagement = sorted(
                user_posts,
                key=lambda x: (x["engagementRate"] or 0),
                reverse=True
            )[:top_count]

            await Actor.push_data({
                "type": "SUMMARY",
                "username": username,
                "followers": followers,
                "topLikedPosts": top_liked,
                "topCommentedPosts": top_commented,
                "topEngagementPosts": top_engagement
            })

        Actor.log.info("✅ Actor üstünlikli tamamlandy")


if __name__ == "__main__":
    asyncio.run(main())
