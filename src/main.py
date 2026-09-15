import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl
import json

# ---------------------------------------------------------------------
# Pydantic model for book details
# ---------------------------------------------------------------------
class Book(BaseModel):
    title : str
    product_url : HttpUrl
    price_gbp : float
    price_text : str
    availability_text : str
    rating_text : str
    description : str | None
    source_page : int
    fetched_at : str

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
URL = "https://books.toscrape.com/"
CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0"
}
LAST_REQUEST_TIME = None

# ---------------------------------------------------------------------
# Fetch catalogue page
# ---------------------------------------------------------------------
def  fetch_catalogue_page(url, cache_file):
    if cache_file.exists():
        html = cache_file.read_text(encoding = "utf-8")

        print("CACHE HIT")
        print(f"response_size ={len(html)} bytes")

        return html
    print("FETCH")

    global LAST_REQUEST_TIME 

    if LAST_REQUEST_TIME is not None:
        elapsed = time.time() - LAST_REQUEST_TIME

        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    LAST_REQUEST_TIME = time.time()

    if response.status_code != 200:
        raise  RuntimeError(
            f"Request failed with status code {response.status_code}"
        )

    html = response.text

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")

    print(f"response_size = {len(html)} bytes")

    return html

# ---------------------------------------------------------------------
# Fetch and cache each book page
# ---------------------------------------------------------------------
def fetch_detail_page(url, cache_file):
    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print("CACHE HIT")
        print(f"response_size = {len(html)} bytes")
        return html
    
    print("FETCH")

    global LAST_REQUEST_TIME

    if LAST_REQUEST_TIME is not None:
        elapsed = time.time() - LAST_REQUEST_TIME
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    LAST_REQUEST_TIME = time.time()

    if response.status_code != 200:
        raise RuntimeError(
            f"request failed with status code {response.status_code}"
        )

    response.encoding = "utf-8"
    html = response.text    

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")

    print(f"response_size = {len(html)} bytes")

    return html

# ---------------------------------------------------------------------
# Extract book details
# ---------------------------------------------------------------------
def extract_book_details(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")

    fetched_at = datetime.now(timezone.utc).isoformat()

    title = soup.select_one(
        "div.product_main h1"
    ).get_text(strip = True)

    price_text = soup.select_one(
        "p.price_color"
    ).get_text(strip=True)

    availability_text = soup.select_one(
        "p.instock.availability"
    ).get_text("", strip=True)

    rating_element= soup.select_one(
      "p.star-rating"  
    )

    rating_text = rating_element.get("class")[1]

    description_element = soup.select_one(
        "#product_description + p"
    )

    if description_element:
        description = description_element.get_text(
            "",
            strip = True
        )
    else:
        description = None

    return {
        "title" : title,
        "product_url":product_url,
        "price_text":price_text,
        "availability_text":availability_text,
        "rating_text":rating_text,
        "description":description,
        "source_page":source_page,
        "fetched_at":fetched_at,
    }
# ---------------------------------------------------------------------
# Normalize price
# ---------------------------------------------------------------------
def normalize_price(price_text):
    return float(price_text.replace("£", "").strip())

def normalize_book(raw_book):
    normalized_book = raw_book.copy()

    normalized_book["price_gbp"] = normalize_price(
        raw_book["price_text"]
    )

    return normalized_book

normalized_books = []



# ---------------------------------------------------------------------
# Book URLs
# ---------------------------------------------------------------------
def discover_book_urls(html, page_url):
    soup = BeautifulSoup(html, "html.parser")

    books = soup.select("article.product_pod")

    book_urls = []

    for book in books:
        link = book.select_one("a")

        if link:
            href = link.get("href")
            product_url = urljoin(page_url, href)
            book_urls.append(product_url)

    return book_urls

# ---------------------------------------------------------------------
# Function for Next URL
# ---------------------------------------------------------------------
def discover_next_url(html, page_url):
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.select_one("li.next a")

    if next_link:
        href = next_link.get("href")
        return urljoin(page_url, href)
    return None

# ---------------------------------------------------------------------          
if __name__ == "__main__":
    current_url = URL
    all_book_urls = []
    book_source_pages = {}


    for page_number in range (1,4):
        cache_file = Path(
            f"cache/catalogue-page-{page_number}.html"
        )
        html = fetch_catalogue_page(

            current_url,
            cache_file
        )

        book_urls = discover_book_urls(
            html,
            current_url
        )

        all_book_urls.extend(book_urls)
        for book_url in book_urls:
             book_source_pages[book_url] = page_number

        print(

            f"catalogue_page = {page_number},"
            f"discovered = {len(book_urls)}"
        )

        if page_number < 3:
            next_url = discover_next_url(
                html,
                current_url
            )

            if next_url is None:
                raise RuntimeError(
                    "Could not find the next catalogue page!"
                )

            current_url = next_url

    unique_book_urls = list(dict.fromkeys(all_book_urls))

    print(f"catalogue_pages=3")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_book_urls)}")

# ---------------------------------------------------------------------
# Raw Books
# ---------------------------------------------------------------------
raw_books = []

for index, product_url in enumerate(unique_book_urls, start=1):
    cache_file = Path(
        f"cache/details/{index}.html"
    )

    print(f"\nProcessing book {index}/60") 

    html = fetch_detail_page(
        product_url,
        cache_file
    )

    source_page = book_source_pages[product_url]
    book = extract_book_details(
        html,
        product_url,
        source_page
    )

    raw_books.append(book)

required_fields = {
    "title",
    "product_url",
    "price_text",
    "availability_text",
    "rating_text",
    "description",
    "source_page",
    "fetched_at",
}

for book in raw_books:
    if set(book.keys()) != required_fields:
        raise RuntimeError(
            f"Invalid fields for book: {book['product_url']}"
        )

print("All records contain the required 8 fields.")

print(f"\ndetail_pages={len(raw_books)}")
print(raw_books[0])

# ---------------------------------------------------------------------
# Price Normlized Books
# ---------------------------------------------------------------------
normalized_books = []

for raw_book in raw_books:
    normalized_book = normalize_book(raw_book)
    normalized_books.append(normalized_book)

print(f"normalized_books={len(normalized_books)}")

# ----------------------------------------
# Validate all books
# ----------------------------------------

valid_books = []
invalid_books = []

for book_data in normalized_books:

    try:
        validated_book = Book(
            **book_data
        )

        valid_books.append(
            validated_book.model_dump(mode="json")
        )

    except Exception as error:

        invalid_books.append({
            "record": book_data,
            "error": str(error)
        })


print(
    f"valid_books={len(valid_books)}"
)

print(
    f"invalid_books={len(invalid_books)}"
)

# ----------------------------------------
# Store validated results
# ----------------------------------------

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

books_file = output_dir / "books.json"
errors_file = output_dir / "errors.json"

with books_file.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        valid_books,
        file,
        indent=2,
        ensure_ascii=False
    )

with errors_file.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        invalid_books,
        file,
        indent=2,
        ensure_ascii=False
    )

print(f"Saved valid books to {books_file}")
print(f"Saved errors to {errors_file}")