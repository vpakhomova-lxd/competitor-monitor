import os
from datetime import datetime
from urllib.parse import urljoin

import feedparser
import requests
import yaml
from openai import OpenAI


def load_competitors():
    with open("competitors.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data.get("competitors", [])


def guess_rss_urls(page_url):
    return [
        page_url,
        urljoin(page_url, "/feed"),
        urljoin(page_url, "/rss"),
        urljoin(page_url, "/rss.xml"),
        urljoin(page_url, "/feed.xml"),
        urljoin(page_url, "/atom.xml"),
    ]


def fetch_feed_items(url):
    possible_urls = guess_rss_urls(url)

    for feed_url in possible_urls:
        print(f"Trying feed: {feed_url}")

        feed = feedparser.parse(feed_url)

        if feed.entries:
            print(f"Found feed: {feed_url}")
            return feed_url, feed.entries[:5]

    return None, []


def analyze_with_openai(competitor_name, item):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "is_new": "unknown",
            "category": "no_api_key",
            "summary": "OPENAI_API_KEY was not found",
            "recommendation": "Добавьте OPENAI_API_KEY в GitHub Secrets.",
        }

    title = item.get("title", "")
    link = item.get("link", "")
    summary = item.get("summary", "")

    prompt = f"""
Ты аналитик конкурентной разведки.

Проанализируй публикацию конкурента.

Конкурент: {competitor_name}
Заголовок: {title}
Ссылка: {link}
Текст: {summary}

Определи, похоже ли это на новинку: новая услуга, новый продукт, новое мероприятие, новая цена, новый формат, новая локация, новый партнёр или новая рекламная кампания.

Ответь коротко на русском в таком формате:

Новинка: да/нет
Категория: ...
Кратко: ...
Цена: ...
Рекомендация: ...
"""

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        return {
            "is_new": "analyzed",
            "category": "openai",
            "summary": response.output_text,
            "recommendation": "",
        }

    except Exception as error:
        return {
            "is_new": "error",
            "category": "openai_error",
            "summary": str(error),
            "recommendation": "Проверьте API key, billing и доступность модели.",
        }


def main():
    print("Competitor monitor started")
    print(f"Run time: {datetime.now().isoformat()}")

    competitors = load_competitors()
    print(f"Competitors loaded: {len(competitors)}")

    for competitor in competitors:
        name = competitor.get("name")
        website_news = competitor.get("website_news")

        print("")
        print("=" * 60)
        print(f"Competitor: {name}")

        if not website_news:
            print("No website_news URL configured")
            continue

        print(f"Website/news URL: {website_news}")

        feed_url, items = fetch_feed_items(website_news)

        if not items:
            print("No RSS/feed items found for this competitor")
            print("Later we can add normal website parsing for pages without RSS.")
            continue

        print(f"Items found: {len(items)}")
        print(f"Source feed: {feed_url}")

        for index, item in enumerate(items, start=1):
            title = item.get("title", "No title")
            link = item.get("link", "No link")
            published = item.get("published", "No date")

            print("")
            print("-" * 40)
            print(f"Item {index}")
            print(f"Title: {title}")
            print(f"Published: {published}")
            print(f"Link: {link}")

            analysis = analyze_with_openai(name, item)

            print("")
            print("Analysis:")
            print(analysis["summary"])

    print("")
    print("Done")


if __name__ == "__main__":
    main()
