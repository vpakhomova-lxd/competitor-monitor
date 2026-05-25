import os
from datetime import datetime

import yaml
from openai import OpenAI


def load_competitors():
    with open("competitors.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data.get("competitors", [])


def check_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("OPENAI_API_KEY was not found")
        return False

    print("OPENAI_API_KEY was found")

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-4.1-mini",
            input="Ответь одним словом: работает"
        )

        print("OpenAI test response:")
        print(response.output_text)
        return True

    except Exception as error:
        print("OpenAI test failed")
        print(str(error))
        return False


def main():
    print("Competitor monitor started")
    print(f"Run time: {datetime.now().isoformat()}")

    competitors = load_competitors()

    print(f"Competitors loaded: {len(competitors)}")

    for competitor in competitors:
        print("-" * 40)
        print(f"Name: {competitor.get('name')}")
        print(f"Website: {competitor.get('website_news')}")
        print(f"Telegram: {competitor.get('telegram')}")
        print(f"YouTube: {competitor.get('youtube')}")

    print("-" * 40)
    check_openai_key()

    print("Done")


if __name__ == "__main__":
    main()
