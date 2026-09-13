import requests
from pathlib import Path

URL = "https://books.toscrape.com/"
CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0"
}

def  fetch_catalogue_page():
    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding = "utf-8")

        print("CACHE HIT")
        print(f"response_size ={len(html)} bytes")

        return html
    print("FETCH")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=10
    )

    if response.status_code != 200:
        raise  RuntimeError(
            f"Request failed with status code {response.status_code}"
        )

    html = response.text

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(html, encoding="utf-8")

    print(f"response_size = {len(html)} bytes")

    return html

if __name__ == "__main__":
    fetch_catalogue_page()