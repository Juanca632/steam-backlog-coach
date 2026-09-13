"""Steam CDN header image URLs.

Public, unauthenticated static assets — no API call or key needed, just
the well-known Akamai CDN path keyed by appid. Works for any real appid,
owned or not.
"""

HEADER_IMAGE_TEMPLATE = "https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"


def header_image_url(appid: int) -> str:
    return HEADER_IMAGE_TEMPLATE.format(appid=appid)
