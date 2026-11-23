import re


ASSET_TERMS = {
    "BTCUSDT": re.compile(r"\b(?:bitcoin|btc(?:usdt)?)\b", re.IGNORECASE),
    "XAUUSD": re.compile(r"\b(?:gold|xau(?:usd)?)\b", re.IGNORECASE),
}
MACRO_TERMS = re.compile(
    r"\b(?:federal reserve|fomc|fed rate|us inflation|u\.s\. inflation|"
    r"nonfarm payrolls|u\.s\. cpi|us cpi)\b",
    re.IGNORECASE,
)


class NewsProcessor:
    def __init__(self):
        self.seen_ids = set()

    def add_news(self, news_id):
        if news_id in self.seen_ids:
            return False

        self.seen_ids.add(news_id)
        return True

    def has_seen(self, news_id):
        return news_id in self.seen_ids


def candidate_assets(text):
    if MACRO_TERMS.search(text):
        return tuple(ASSET_TERMS)
    return tuple(asset for asset, terms in ASSET_TERMS.items() if terms.search(text))
