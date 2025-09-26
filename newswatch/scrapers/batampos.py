import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from newspaper import Article
from .basescraper import BaseScraper  # Pastikan ini ada
from .sentiment import classify_sentiment_id

class BatamposScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "https://batampos.co.id"
        self.start_date = start_date
        self.continue_scraping = True
        self.href_pattern = re.compile(r".*batampos\.co\.id.*", re.IGNORECASE)

    async def build_search_url(self, keyword, page):
        url = f"{self.base_url}/?s={keyword}&paged={page}"
        return await self.fetch(url, headers={"User-Agent": "Mozilla/5.0"})
    
    def parse_article_links(self, response_text):
        soup = BeautifulSoup(response_text, "html.parser")

        all_links = soup.find_all("a", href=True)
        filtered_hrefs = set()

        for a in all_links:
            href = a["href"]
            if href and not href.startswith('#'):
                full_url = urljoin(url, href)
                if 'batampos.co.id' in full_url:
                    filtered_hrefs.append(full_url)

            # Exclude links inside .vc_column-inner (e.g., sidebars, widgets)
            if a.find_parent(class_="vc_column-inner"):
                continue
            filtered_hrefs.add(href)
        return list(filtered_hrefs)
    
    async def get_article(self, filtered_hrefs, keyword):
        try:
            for article in filtered_hrefs: 
                article.download()
                article.parse()

                # Filter by keyword
                # if keyword.lower() not in article.text.lower() and keyword.lower() not in article.title.lower():
                #    return

                # Parse publish date
                publish_date = article.publish_date
                if not publish_date:
                    logging.warning(f"No publish date for {link}, skipping")
                    return

                if self.start_date and publish_date < self.start_date:
                    self.continue_scraping = False
                    return

                # Try to get category from URL
                match = re.search(r"https://www\.*\.batampos\.co\.id/\d{4}/\d{2}/\d{2}/([^/]+)/", link)
                category = match.group(1) if match else "Unknown"

                item = {
                    "title": article.title,
                    "publish_date": publish_date,
                    "author": article.authors[0] if article.authors else "Unknown",
                    "content": article.text,
                    "keyword": keyword,
                    "category": category,
                    "source": self.base_url.split("www.")[1],
                    "link": link,
                }

            await self.queue_.put(item)

        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")
