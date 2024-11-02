import json
import logging
import random
import re
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .basescraper import BaseScraper


class KompasScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None):
        super().__init__(keywords, concurrency)
        self.base_url = "https://www.kompas.com"
        self.start_date = start_date
        self.continue_scraping = True

    def build_search_url(self, keyword, page):
        cx = "partner-pub-9012468469771973:uc7pie-r3ad"
        response_text = requests.get(f"https://cse.google.com/cse.js?cx={cx}").text

        cse_tok_pattern = re.compile(r'"cse_token":\s+"([^\"]+)"', re.DOTALL)
        cselibv_pattern = re.compile(r'"cselibVersion":\s+"([^\"]+)"', re.DOTALL)

        cse_tok = cse_tok_pattern.search(response_text).group(1)
        cselibv = cselibv_pattern.search(response_text).group(1)

        random_string = f"{random.randint(1000, 9999)}"
        # https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&start=10&cselibv=8fa85d58e016b414&cx=partner-pub-9012468469771973%3Auc7pie-r3ad&q=ihsg&safe=active&cse_tok=AB-tC_4ESv3DqiuMy-n2BHbEuIRb%3A1730534606417&lr=&cr=&gl=&filter=0&sort=date&as_oq=&as_sitesearch=&exp=cc&callback=google.search.cse.api15570&rurl=https%3A%2F%2Fsearch.kompas.com%2Fsearch%2F%3Fq%3Dihsg%26submit%3DSubmit%23gsc.tab%3D0%26gsc.q%3Dihsg%26gsc.sort%3Ddate
        params = {
            "rsz": "filtered_cse",
            "num": 10,
            "hl": "en",
            "source": "gcsc",
            "start": page - 1 * 10,
            "cselibv": cselibv,
            "cx": cx,
            "q": keyword,
            "safe": "active",
            "cse_tok": cse_tok,
            "lr": "",
            "cr": "",
            "gl": "",
            "filter": 0,
            "sort": "date",
            "as_oq": "",
            "as_sitesearch": "",
            "exp": "cc",
            "callback": f"google.search.cse.api{random_string}",
            "rurl": f"https://search.kompas.com/search/?q={keyword}&submit=Submit#gsc.tab=0&gsc.q={keyword}&gsc.sort=date",
        }
        return "https://cse.google.com/cse/element/v1?" + urlencode(params)

    def parse_article_links(self, response_text):
        pattern = r"google\.search\.cse\.[^\(]+\((.*?)\);"
        response_json = json.loads(
            re.search(pattern, response_text, re.DOTALL).group(1)
        )
        articles = response_json["results"]
        if not articles:
            return None

        filtered_hrefs = {
            a["unescapedUrl"]
            for a in articles
            if a["unescapedUrl"] and "kompas.com/tag/" not in a["unescapedUrl"]
        }
        return filtered_hrefs

    async def get_article(self, link, keyword):
        response_text = await self.fetch(f"{link}?page=all")
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")
        try:
            category = soup.select_one(".breadcrumb__wrap").get_text(
                separator="/", strip=True
            )
            title = soup.select_one(".read__title").get_text(strip=True)
            publish_date_str = (
                soup.select_one(".read__time").get_text(strip=True).split("- ")[1]
            )
            author = soup.select_one(".credit-title-name").get_text(strip=True)

            content_div = soup.select_one(".read__content")

            # loop through paragraphs and remove those with class patterns like "track-*"
            for tag in content_div.find_all(["div", "span"]):
                # a_tag = tag.find("a", class_=True)
                if tag and any(
                    cls.startswith("inject-baca-juga") or cls.startswith("kompasidRec")
                    for cls in tag.get("class", [])
                ):
                    tag.extract()
            # remove unwanted elements
            unwanted_phrases = [
                r"Simak.*WhatsApp Channel",
                r"https://www\.whatsapp\.com/channel/",
                r"Baca juga: ",
            ]
            unwanted_pattern = re.compile("|".join(unwanted_phrases), re.IGNORECASE)

            for tag in content_div.find_all(["i", "p"]):
                tag_text = tag.get_text()
                if unwanted_pattern.search(tag_text):
                    tag.extract()

            content = content_div.get_text(separator=" ", strip=True)

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
            self.results.append(item)
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")
