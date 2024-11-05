import argparse
import asyncio
import logging
from datetime import datetime

from .main import main as run_main


def cli():
    parser = argparse.ArgumentParser(description="News Watch")
    parser.add_argument(
        "--keywords",
        "-k",
        default="ihsg",
        help="Comma-separated list of keywords to scrape (e.g., 'ojk,bank,npl')",
    )
    parser.add_argument(
        "--start_date",
        "-sd",
        default=datetime.now().replace(day=1).strftime("%Y-%m-%d"),
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
