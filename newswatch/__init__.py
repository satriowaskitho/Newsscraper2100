__version__ = "0.2.5"

# main api functions
from .api import (
    scrape,
    scrape_to_dataframe,
    scrape_to_file,
    list_scrapers,
    quick_scrape,
    scrape_ihsg_news,
)
