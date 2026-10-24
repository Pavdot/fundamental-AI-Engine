

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

def register_article(processor, article):
    # À compléter
    news_id = article["id"]


processor = NewsProcessor()

    