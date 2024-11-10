import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper


class CNBCScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "https://www.cnbcindonesia.com"
        self.start_date = start_date

    async def build_search_url(self, keyword, page):
        # https://www.cnbcindonesia.com/search?query=&fromdate=&page=
        query_params = {
            "query": keyword,
            "fromdate": self.start_date.strftime("%Y/%m/%d"),
            "page": page,
        }
        url = f"{self.base_url}/search?{urlencode(query_params)}"
        return await self.fetch(url)

    def parse_article_links(self, response_text):
        soup = BeautifulSoup(response_text, "html.parser")
        articles = soup.select(".nhl-list a.group[href]")
        if not articles:
            return None

        filtered_hrefs = {a.get("href") for a in articles if a.get("href")}
        return filtered_hrefs

    async def get_article(self, link, keyword):
        response_text = await self.fetch(link)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")
        try:
            category = soup.select_one("a.text-xs.font-semibold[href='#']").get_text(
                strip=True
            )
            title = soup.select_one("h1.mb-4.text-32.font-extrabold").get_text(
                strip=True
            )
            author = soup.select("div.mb-1.text-base.font-semibold")[1].get_text(
                strip=True
            )
            publish_date_str = soup.select_one("div.text-cm.text-gray").get_text(
                strip=True
            )

            content_div = soup.find("div", {"class": "detail-text"})

            # loop through paragraphs and remove those with class patterns like "sisip-*"
            for tag in content_div.find_all(["table", "div"]):
                class_list = tag.get("class", [])
                if any(
                    cls.startswith("sisip_") or cls.startswith("link_sisip")
                    for cls in class_list
                ):
                    tag.extract()

            content = content_div.get_text(separator="\n", strip=True)

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
                "source": self.base_url.split("www.")[1],
                "link": link,
            }
            await self.queue_.put(item)
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")
