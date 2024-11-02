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
from .scrapers.kompas import KompasScraper
from .scrapers.kontan import KontanScraper
from .scrapers.viva import VivaScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


async def write_csv(queue, filename=None):
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

    current_time = datetime.now().strftime("%Y%m%d_%H")
    filename = Path.cwd() / f"news-watch-{current_time}.csv"

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            csv_writer.writeheader()

            while True:
                item = await queue.get()
                if item is None:  # Sentinel value to stop the writer
                    break

                # Format datetime objects as strings
                if isinstance(item.get("publish_date"), datetime):
                    item["publish_date"] = item["publish_date"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                csv_writer.writerow(item)
                csvfile.flush()  # Ensure data is written to disk

        print(f"Data written to {filename}")
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")


async def main(args):
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    keywords = args.keywords

    queue_ = asyncio.Queue()
    writer_task = asyncio.create_task(write_csv(queue_))

    scrapers = [
        BisnisIndonesiaScraper(keywords, start_date=start_date, queue_=queue_),
        CNBCScraper(keywords, start_date=start_date, queue_=queue_),
        DetikScraper(keywords, start_date=start_date, queue_=queue_),
        # Disable KontanScraper since it has been banned by Cloudflare
        # KontanScraper(keywords, start_date=start_date, queue_=   queue_),
        KompasScraper(keywords, start_date=start_date, queue_=queue_),
        VivaScraper(keywords, start_date=start_date, queue_=queue_),
        # FIX ME: add more scrapers here
        # FUTURE: english website reuters, CNBC
    ]

    # run all scrapers concurrently
    await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

    # ater scraping is done, put a sentinel value into the queue to signal the writer to finish
    await queue_.put(None)
    await writer_task
