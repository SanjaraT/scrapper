# The Polite Scraper

A small Python scraper built for the FlyRankAI Backend Engineering Week 5 assignment, **A9 - The polite scraper**.

It scrapes the first three catalogue pages of [Books to Scrape](https://books.toscrape.com/), discovers the 60 book pages from the catalogue navigation, extracts book details, normalizes and validates the data with Pydantic, and stores the results as JSON.

## Target classification

**Target:** Books to Scrape
**Scope:** First 3 catalogue pages only
**Expected books:** 60

Books to Scrape is a practice sandbox created for learning web scraping.

The site's `robots.txt` file could not be found / was unavailable when checked.

I will not reuse this code on another site without checking its rules and terms first.

## Pipeline

The scraper follows this flow:

**Fetch → Extract → Normalize → Validate → Store → Report**

1. Fetch the first three catalogue pages.
2. Cache downloaded HTML during development.
3. Discover book links from each catalogue page.
4. Follow the catalogue's own `next` link to reach pages 2 and 3.
5. Visit each of the 60 discovered book pages.
6. Extract the required book fields.
7. Normalize the price into a numeric GBP value.
8. Validate every record with Pydantic.
9. Store valid records in `output/books.json`.
10. Store validation errors in `output/errors.json`.
11. Create `output/run-report.json` with run statistics and failed pages.

## Requirements

* Python 3.10+
* Requests
* Beautiful Soup 4
* Pydantic

## Installation

Create and activate a virtual environment if desired, then install the dependencies:

```bash
pip install requests beautifulsoup4 pydantic
```

## Run

From the project root:

```bash
python src/main.py
```

The scraper uses cached HTML when available. This makes development reruns faster and avoids repeatedly requesting pages that have already been downloaded.

## Output schema

Each valid book record contains:

| Field               | Description                                        |
| ------------------- | -------------------------------------------------- |
| `title`             | Book title                                         |
| `product_url`       | Absolute HTTPS URL of the book page                |
| `price_gbp`         | Numeric price in GBP                               |
| `price_text`        | Original price text                                |
| `availability_text` | Original availability text                         |
| `rating_text`       | Rating value extracted from the page               |
| `description`       | Book description, or `null` when unavailable       |
| `source_page`       | Catalogue page where the book was discovered       |
| `fetched_at`        | UTC timestamp associated with the extracted record |

## Politeness and failure handling

The scraper is designed to avoid unnecessary requests:

* Uses an identifying User-Agent.
* Uses a 10-second request timeout.
* Waits at least 0.5 seconds between real network requests.
* Does not delay cache hits.
* Caches downloaded HTML during development.
* Retries timeouts and HTTP 5xx responses once.
* Does not retry HTTP 403 or 404 responses.
* Processes book pages independently so one failed page does not stop the entire run.
* Does not invent missing descriptions; unavailable descriptions are represented as `null`.

## Why no browser?

No browser is needed because the data is already in server-sent HTML, browser only adds cost.

The scraper uses Requests and Beautiful Soup because the required catalogue and book information can be obtained directly from the returned HTML.

## Failure test

A fake book URL was temporarily added during development to simulate a broken page.

The scraper received:

```text
ERROR: Request failed with status code 404
```

It recorded the failed page and continued processing the remaining books.

The run still produced:

```text
valid_books=60
invalid_books=0
```

The fake URL was removed after testing.

## Run evidence

A normal cached rerun produced:

```json
{
  "catalogue_pages": 3,
  "catalogue_pages_fetched": 0,
  "catalogue_cache_hits": 3,
  "detail_pages_fetched": 0,
  "detail_cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": []
}
```

The complete report is available in:

```text
output/run-report.json
```

## Ethics and limitations

This project is intended for the Books to Scrape practice sandbox.

For another website, its rules and terms must be checked first. If an official API exists, it should be preferred where appropriate. This scraper does not attempt to bypass logins, paywalls, access controls, or blocks, and it collects only the fields required for the assignment.

One limitation is that the scraper only covers the first three catalogue pages and is specifically designed for the structure of this practice site. It should not be assumed to work unchanged on another website.

## Project structure

```text
polite_scrapper/
├── .gitignore
├── README.md
├── src/
│   └── main.py
└── output/
    ├── books.json
    ├── errors.json
    └── run-report.json
```

Cached HTML is kept locally during development and excluded from Git with `.gitignore`.
