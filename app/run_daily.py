import os
from datetime import datetime
from urllib.parse import urljoin

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
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
            items = []

            for entry in feed.entries[:5]:
                items.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "No date"),
                    "summary": entry.get("summary", ""),
                    "source_type": "rss",
                })

            return feed_url, items

    return None, []


def fetch_html_items(page_url):
    print(f"Trying HTML page: {page_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 compatible; competitor-monitor/1.0"
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as error:
        print(f"HTML fetch failed: {error}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []

    selectors = [
        "article",
        ".event",
        ".events",
        ".news",
        ".item",
        ".post",
        ".card",
        "li",
    ]

    for selector in selectors:
        blocks = soup.select(selector)

        for block in blocks:
            link_tag = block.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(" ", strip=True)
            href = link_tag.get("href")
            link = urljoin(page_url, href)

            text = block.get_text(" ", strip=True)

            if len(title) < 5:
                continue

            if len(text) < 20:
                continue

            candidates.append({
                "title": title[:200],
                "link": link,
                "published": "No date",
                "summary": text[:1000],
                "source_type": "html",
            })

    unique_items = []
    seen_links = set()

    for item in candidates:
        if item["link"] in seen_links:
            continue

        seen_links.add(item["link"])
        unique_items.append(item)

    return unique_items[:5]


def analyze_with_openai(competitor_name, item):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "OPENAI_API_KEY was not found"

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

        return response.output_text

    except Exception as error:
        return f"OpenAI analysis skipped/failed: {error}"


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

        if items:
            print(f"Items found via RSS: {len(items)}")
            print(f"Source feed: {feed_url}")
        else:
            print("No RSS/feed items found. Trying HTML parsing...")
            items = fetch_html_items(website_news)
            print(f"Items found via HTML: {len(items)}")

        if not items:
            print("No items found for this competitor")
            continue

        for index, item in enumerate(items, start=1):
            title = item.get("title", "No title")
            link = item.get("link", "No link")
            published = item.get("published", "No date")
            source_type = item.get("source_type", "unknown")

            print("")
            print("-" * 40)
            print(f"Item {index}")
            print(f"Source type: {source_type}")
            print(f"Title: {title}")
            print(f"Published: {published}")
            print(f"Link: {link}")

            analysis = analyze_with_openai(name, item)

            print("")
            print("Analysis:")
            print(analysis)

    print("")
    print("Done")


if __name__ == "__main__":
    main()
