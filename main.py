import argparse
import asyncio
import csv
import logging
from datetime import datetime
from pathlib import Path

from scrapers.cnbc import CNBCScraper
from scrapers.detik import DetikScraper
from scrapers.kontan import KontanScraper
from scrapers.viva import VivaScraper


def write_csv(data, filename=None):
    fieldnames = [
        "title",
        "publish_date",
        "author",
        "content",
        "keyword",
        "category",
        "source",
        "link",
    ]

    if filename is None:
        current_time = datetime.now().strftime("%Y%m%d_%H")
        filename = Path.cwd() / f"id-news-watch{current_time}.csv"

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            for item in data:
                # Format datetime objects as strings
                if isinstance(item.get("publish_date"), datetime):
                    item["publish_date"] = item["publish_date"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                writer.writerow(item)
        print(f"Data written to {filename}")
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start_date",
        default=datetime.now().replace(day=1).strftime("%Y-%m-%d"),
        help="Start date for scraping in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--keywords",
        default="ekonomi",
        help="comma-separated list of keywords to scrape (e.g., 'ojk,bank,npl')",
    )
    parser.add_argument(
        "--verbose",
        action="store_false",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    # set logging level based on verbose argument
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.CRITICAL)  # silence all logs unless critical

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    keywords = args.keywords

    scrapers = [
        CNBCScraper(keywords, start_date=start_date),
        DetikScraper(keywords, start_date=start_date),
        VivaScraper(keywords, start_date=start_date),
        KontanScraper(keywords, start_date=start_date),
        # FIX ME: add more scrapers here
    ]

    # run all scrapers concurrently
    await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

    all_results = []
    for scraper in scrapers:
        all_results.extend(scraper.results)

    if all_results:
        await write_csv(all_results)
    else:
        logging.error("No data scraped.")


if __name__ == "__main__":
    asyncio.run(main())
