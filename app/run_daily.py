import re
from datetime import datetime, date
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup


START_DATE = date(2026, 6, 1)


MONTHS_RU = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def load_competitors():
    with open("competitors.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data.get("competitors", [])


def parse_russian_date(text):
    text = text.lower()

    # Формат: 1 июня 2026
    match = re.search(
        r"(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
        r"(?:\s+(\d{4}))?",
        text,
    )

    if not match:
        return None

    day = int(match.group(1))
    month = MONTHS_RU[match.group(2)]
    year = int(match.group(3)) if match.group(3) else START_DATE.year

    try:
        return date(year, month, day)
    except ValueError:
        return None


def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 compatible; competitor-monitor/1.0"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.text


def extract_event_candidates(page_url):
    print(f"Reading schedule page: {page_url}")

    html = fetch_html(page_url)
    soup = BeautifulSoup(html, "html.parser")

    candidates = []

    selectors = [
        "article",
        ".event",
        ".events",
        ".event-card",
        ".event-item",
        ".schedule-item",
        ".afisha-item",
        ".item",
        ".card",
        "li",
        "tr",
    ]

    for selector in selectors:
        blocks = soup.select(selector)

        for block in blocks:
            text = block.get_text(" ", strip=True)

            if len(text) < 20:
                continue

            event_date = parse_russian_date(text)

            if not event_date:
                continue

            if event_date < START_DATE:
                continue

            link_tag = block.find("a", href=True)
            link = urljoin(page_url, link_tag["href"]) if link_tag else page_url

            title = ""

            if link_tag:
                title = link_tag.get_text(" ", strip=True)

            if not title or len(title) < 5:
                title = text[:160]

            candidates.append({
                "date": event_date,
                "title": title,
                "link": link,
                "text": text[:500],
            })

    unique = []
    seen = set()

    for item in candidates:
        key = (item["date"], item["link"], item["title"])

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    unique.sort(key=lambda item: item["date"])

    return unique


def main():
    print("Competitor event monitor started")
    print(f"Run time: {datetime.now().isoformat()}")
    print(f"Collecting events from: {START_DATE.isoformat()}")

    competitors = load_competitors()
    print(f"Competitors loaded: {len(competitors)}")

    total_events = 0

    for competitor in competitors:
        name = competitor.get("name")
        website_news = competitor.get("website_news")

        print("")
        print("=" * 80)
        print(f"Competitor: {name}")

        if not website_news:
            print("No website_news URL configured")
            continue

        try:
            events = extract_event_candidates(website_news)
        except Exception as error:
            print(f"Failed to read page: {error}")
            continue

        if not events:
            print("No future events found from 1 June")
            continue

        print(f"Future events found: {len(events)}")
        total_events += len(events)

        for event in events:
            print("")
            print("-" * 40)
            print(f"Date: {event['date'].isoformat()}")
            print(f"Title: {event['title']}")
            print(f"Link: {event['link']}")

    print("")
    print("=" * 80)
    print(f"Total future events found: {total_events}")
    print("Done")


if __name__ == "__main__":
    main()
