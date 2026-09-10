"""Store API `appdetails` client (UNOFFICIAL).

Critical points:
- aggressive rate limit (~200 requests / 5 min, returns 429 with no warning)
- exponential backoff + honor Retry-After
- everything fetched is cached PERMANENTLY in AppDetails (genre/description never change)
- get_app_details(appid) checks the cache before hitting the network
"""
