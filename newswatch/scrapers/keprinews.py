import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper

# from .sentiment import classify_sentiment_id


class KeprinewsScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "keprinews.co"
        self.start_date = start_date

    async def build_search_url(self, keyword, page):
        # KepriNews menggunakan WordPress search dengan format: /?s=keyword&paged=page
        query_params = {
            "s": keyword,
        }
        
        # WordPress pagination: page 1 tidak perlu paged parameter
        if page > 1:
            query_params["paged"] = page
            
        url = f"https://{self.base_url}/?{urlencode(query_params)}"
        return await self.fetch(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

    def parse_article_links(self, response_text):
        if not response_text:
            return None

        soup = BeautifulSoup(response_text, "html.parser")
        
        # Cari semua artikel dengan class "jeg_post"
        main_article = soup.find('div', class_='jeg_main_content')
        articles = main_article.find_all("article", class_="jeg_post")
        
        if not articles:
            return None

        filtered_hrefs = set()
        for article in articles:
            # Cari link di dalam h3.jeg_post_title > a
            title_link = article.select_one("h3.jeg_post_title a")
            if title_link and title_link.get("href"):
                href = title_link["href"]
                # Filter hanya artikel keprinews.co dengan format tanggal di URL
                if "keprinews.co" in href:
                    filtered_hrefs.add(href)
        
        return filtered_hrefs if filtered_hrefs else None

    async def get_article(self, link, keyword):
        response_text = await self.fetch(link, timeout=30)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")

        try:
            # Title - dalam h1.jeg_post_title
            title_elem = soup.select_one("h1.jeg_post_title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title:
                logging.error(f"Title not found for article {link}")
                return

            # Publish date - dalam div.jeg_meta_date > a
            publish_date_str = ""
            date_elem = soup.select_one(".jeg_meta_date a")
            if date_elem:
                publish_date_str = date_elem.get_text(strip=True)
            
            # Author - dalam div.jeg_meta_author > a
            author = "Admin"  # Default
            author_elem = soup.select_one(".jeg_meta_author a")
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Category - dalam div.jeg_meta_category > span > a (ambil yang pertama)
            category = ""
            category_elem = soup.select_one(".jeg_meta_category a")
            if category_elem:
                category = category_elem.get_text(strip=True)

            # Content - dalam div.entry-content > div.content-inner
            content_div = soup.select_one(".entry-content .content-inner")
            
            if not content_div:
                # Fallback ke .entry-content jika .content-inner tidak ada
                content_div = soup.select_one(".entry-content")

            if content_div:
                # Remove unwanted elements
                for tag in content_div.find_all(["script", "style", "iframe"]):
                    tag.extract()
                
                # Remove share buttons, ads, dan elemen lain yang tidak diinginkan
                for tag in content_div.find_all(["div"]):
                    if tag:
                        classes = tag.get("class", [])
                        # Hapus div dengan class tertentu
                        if any(
                            cls for cls in classes 
                            if any(keyword in cls for keyword in [
                                "jeg_share", "jeg_ad", "share", "ads", 
                                "social", "jeg_post_tags", "jeg_prevnext"
                            ])
                        ):
                            tag.extract()

                # Get text content
                content = content_div.get_text(separator=" ", strip=True)
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