"""
author: Okky Mabruri <okkymbrur@gmail.com>
maintainer: Okky Mabruri <okkymbrur@gmail.com>
"""

import asyncio
import csv
import logging
from datetime import datetime
from pathlib import Path

from .scrapers.bisnisindonesia import BisnisIndonesiaScraper
from .scrapers.cnbc import CNBCScraper
from .scrapers.detik import DetikScraper
from .scrapers.kontan import KontanScraper
from .scrapers.viva import VivaScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


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
        filename = Path.cwd() / f"news-watch-{current_time}.csv"

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            for item in data:
                # format datetime objects as strings
                if isinstance(item.get("publish_date"), datetime):
                    item["publish_date"] = item["publish_date"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                writer.writerow(item)
        print(f"Data written to {filename}")
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")


async def main(args):
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    keywords = args.keywords

    scrapers = [
        BisnisIndonesiaScraper(keywords, start_date=start_date),
        CNBCScraper(keywords, start_date=start_date),
        DetikScraper(keywords, start_date=start_date),
        KontanScraper(keywords, start_date=start_date),
        VivaScraper(keywords, start_date=start_date),
        # FIX ME: add more scrapers here
        # FUTURE: english website reuters, CNBC
    ]

    # run all scrapers concurrently
    await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

    all_results = []
    for scraper in scrapers:
        all_results.extend(scraper.results)

    if all_results:
        write_csv(all_results)
    else:
        logging.error("No data scraped.")
