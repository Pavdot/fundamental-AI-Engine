import sqlite3
from main import *
from news_api import fetch_news
from processor import *

article = fetch_news()

connection = sqlite3.connect("news.db")


for article in article[:5]:
    news_id = article["id"]
    cursor = connection.execute("""INSERT OR IGNORE
INTO processed_news (id) VALUES(?)""", (news_id,))

connection.execute("""CREATE TABLE IF NOT EXISTS processed_news (
id INTERGER PRIMARY KEY)""")

if cursor.rowcount == 1:
    print(news_id, "Nouvel article")
else:
    print(news_id, "Déjà enregistré")

connection.commit()

print(cursor.fetchall())
connection.close()


