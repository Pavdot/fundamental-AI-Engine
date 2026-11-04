import os 
import requests 
from dotenv import load_dotenv
from processor import NewsProcessor


load_dotenv()

def fetch_news():
    response=requests.get("https://finnhub.io/api/v1/news"
    , params = {"category":"general",
    "token":os.getenv("FINNHUB_API_KEY")},
    timeout = 15)
    
    return response.json()

result = fetch_news()

if __name__ == "__main__":
    articles = fetch_news() 
    processor = NewsProcessor()

    for article in articles[:3]:
        if processor.add_news(article["id"]):
            print(article["id"], article["headline"])