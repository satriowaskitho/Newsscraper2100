import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper

# from .sentiment import classify_sentiment_id


class HarianKepriScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "hariankepri.com"
        self.start_date = start_date

    async def build_search_url(self, keyword, page):
        # HarianKepri menggunakan format: /page/{page}/?s=keyword
        # Untuk page 1, tidak perlu /page/1/
        if page == 1:
            url = f"https://www.{self.base_url}/?s={keyword}"
        else:
            url = f"https://www.{self.base_url}/page/{page}/?s={keyword}"
            
        return await self.fetch(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

    def parse_article_links(self, response_text):
        if not response_text:
            return None

        soup = BeautifulSoup(response_text, "html.parser")
        
        # Cari semua artikel dengan class "tdb_module_loop"
        articles = soup.find_all("div", class_="tdb_module_loop")
        
        if not articles:
            return None

        filtered_hrefs = set()
        for article in articles:
            # Cari link di dalam h3.entry-title > a
            title_link = article.select_one("h3.entry-title a")
            if title_link and title_link.get("href"):
                href = title_link["href"]
                # Filter hanya artikel hariankepri.com
                if "hariankepri.com" in href:
                    filtered_hrefs.add(href)
        
        return filtered_hrefs if filtered_hrefs else None

    async def get_article(self, link, keyword):
        response_text = await self.fetch(link, timeout=30)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")

        try:
            # Title - dalam h1.entry-title atau h1.tdb-title-text
            title_elem = soup.select_one("h1.entry-title, h1.tdb-title-text")
            if not title_elem:
                title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title:
                logging.error(f"Title not found for article {link}")
                return

            # Publish date - dalam time.entry-date
            publish_date_str = ""
            date_elem = soup.select_one("time.entry-date")
            if date_elem:
                # Coba ambil dari datetime attribute dulu
                publish_date_str = date_elem.get("datetime", "")
                if not publish_date_str:
                    publish_date_str = date_elem.get_text(strip=True)
            
            # Author - dalam .td-post-author-name > a
            author_elem = soup.select_one("a.tdb-author-name")
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Category - dalam a.td-post-category
            category = ""
            category_elem = soup.select_one("a.td-post-category")
            if category_elem:
                category = category_elem.get_text(strip=True)

            # Content - ambil semua tag <p> dari .td-post-content atau .tdb-block-inner
            content_div = soup.select_one(".tdb_single_content")
            if not content_div:
                content_div = soup.select_one(".tdb-block-inner.td-fix-index")
            
            if content_div:
                # Ambil semua tag <p>
                paragraphs = content_div.find_all("p")
                content_parts = []
                
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    if p_text:  # Hanya ambil yang tidak kosong
                        content_parts.append(p_text)
                
                content = " ".join(content_parts)
            else:
                content = ""
            
            # sentiment = classify_sentiment_id(title)

            publish_date = self.parse_date(publish_date_str)
            if not publish_date:
                logging.error(f"Error parsing date for article {link}: {publish_date_str}")
                return
            if self.start_date and publish_date < self.start_date:
                self.continue_scraping = False
                return

            item = {
                "title": title,
                "publish_date": publish_date,
                "author": author,
                "content": content,
                "keyword": keyword,
                "category": category,
                "source": self.base_url,
                "link": link,
                # "sentiment": sentiment
            }
            await self.queue_.put(item)
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")