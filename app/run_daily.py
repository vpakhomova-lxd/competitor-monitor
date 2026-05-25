from datetime import datetime
import yaml


def load_competitors():
    with open("competitors.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data.get("competitors", [])


def main():
    competitors = load_competitors()

    print("Competitor monitor started")
    print(f"Run time: {datetime.now().isoformat()}")
    print(f"Competitors loaded: {len(competitors)}")

    for competitor in competitors:
        print("-" * 40)
        print(f"Name: {competitor.get('name')}")
        print(f"Website: {competitor.get('website_news')}")
        print(f"Telegram: {competitor.get('telegram')}")
        print(f"YouTube: {competitor.get('youtube')}")

    print("Done")


if __name__ == "__main__":
    main()
