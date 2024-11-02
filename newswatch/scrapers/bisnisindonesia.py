import json
import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper


class BisnisIndonesiaScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "bisnisindonesia.id"
        self.start_date = start_date

    async def build_search_url(self, keyword, page):
        # https://api.bisnisindonesia.id/search/v1/article?page=1&pageSize=20&keyword=ekonomi&order_by=DESC
        query_params = {
            "page": page,
            "pageSize": 20,
            "keyword": keyword,
            "order_by": "DESC",
        }
        url = f"https://api.{self.base_url}/search/v1/article?{urlencode(query_params)}"
        return await self.fetch(url)

    def parse_article_links(self, response_text):
        response_json = json.loads(response_text)
        articles = response_json["data"]["articles"]
        if not articles:
            return None

        filtered_hrefs = {
            f"https://{self.base_url}/article/{a['slug']}"
            for a in articles
            if a["slug"]
        }
        return filtered_hrefs

    async def get_article(self, link, keyword):
        pass
        response_text = await self.fetch(link)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")

        try:
            article_data = soup.find("script", id="__NEXT_DATA__")
            article_data_json = json.loads(article_data.string)
            content_data = article_data_json["props"]["pageProps"]["prearticle"]

            title = content_data["title"]
            publish_date_str = content_data["published_at"]
            author = content_data["author_name"]
            category = (
                f"{content_data['category_name']} - {content_data['sub_category_name']}"
            )
            content = BeautifulSoup(content_data["content"], "html.parser").get_text(
                separator=" ", strip=True
            )

            publish_date = self.parse_date(publish_date_str)
            if not publish_date:
                logging.error(f"Error parsing date for article {link}")
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
            }
            await self.queue_.put(item)
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")
