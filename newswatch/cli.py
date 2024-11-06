import argparse
import asyncio
import logging
import platform
from datetime import datetime

from .main import main as run_main


def cli():
    # List of available scrapers based on the platform
    is_linux = platform.system().lower() == "linux"
    available_scrapers = ["bisnisindonesia", "cnbc", "detik", "kompas", "viva"]
    if not is_linux:
        available_scrapers.append("kontan")
    available_scrapers_str = ",".join(available_scrapers)

    # main description with platform-specific notes
    description = (
        "News Watch - Scrape news articles from various Indonesian news websites.\n"
        f"Currently supports: {available_scrapers_str}.\n"
    )
    if is_linux:
        description += "Note: The 'kontan' scraper is not available on Linux platforms due to known issues."

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--keywords",
        "-k",
        default="ihsg",
        help="Comma-separated list of keywords to scrape (e.g., 'ojk,bank,npl')",
    )
    parser.add_argument(
        "--start_date",
        "-sd",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Start date for scraping in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--scrapers",
        "-s",
        default="all",
        help="Comma-separated list of scrapers to use (e.g., 'kompas,viva'). Default is all.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity level (e.g., -v, -vv, -vvv)",
    )
    # FIX ME: add argument for output name

    args = parser.parse_args()

    # set up logging level based on verbosity
    log_level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(
        args.verbose, logging.DEBUG
    )

    logging.basicConfig(level=log_level)

    asyncio.run(run_main(args))


if __name__ == "__main__":
    cli()
