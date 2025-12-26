# Instagram Post & Comment Monitor

This Apify Actor collects:
- Instagram posts
- Media URLs (images/videos)
- Post captions, likes
- All comments & replies

## Input example
```json
{
  "users": ["instagram"],
  "postLimit": 3,
  "commentLimit": 20,
  "topPostsCount": 1,
  "followersCount": 1000000
}
