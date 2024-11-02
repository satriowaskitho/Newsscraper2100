import json
import logging
import re
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup, Comment

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

        cse_tok = re.search(
            r'"cse_token":\s+"([^\"]+)"', response_text, re.DOTALL
        ).group(1)
        cselibv = re.search(
            r'"cselibVersion":\s+"([^\"]+)"', response_text, re.DOTALL
        ).group(1)

        # https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&cselibv=8fa85d58e016b414&cx=partner-pub-9012468469771973%3Auc7pie-r3ad&q=ihsg&safe=active&cse_tok=AB-tC_7xxa159ne0JzegsRjFHGLg%3A1730480993970&lr=&cr=&gl=&filter=0&sort=&as_oq=&as_sitesearch=&exp=cc&callback=google.search.cse.api14013&rurl=https%3A%2F%2Fsearch.kompas.com%2Fsearch%2F%3Fq%3Dihsg%26submit%3DSubmit%23gsc.tab%3D0%26gsc.q%3Dihsg%26gsc.sort%3Ddate
        params = {
            "rsz": "filtered_cse",
            "num": 20,
            "hl": "en",
            "source": "gcsc",
            "cselibv": cselibv,
            "cx": cx,
            "q": keyword,
            "safe": "active",
            "cse_tok": cse_tok,
            "lr": "",
            "cr": "",
            "gl": "",
            "filter": 0,
            "sort": "",
            "as_oq": "",
            "as_sitesearch": "",
            "exp": "cc",
            "callback": "google.search.cse.api14013",
            "rurl": f"https://search.kompas.com/search/?q={keyword}&submit=Submit#gsc.tab=0&gsc.q={keyword}&gsc.sort=date",
        }
        return "https://cse.google.com/cse/element/v1?" + urlencode(params)

    def parse_article_links(self, response_text):
        pattern = r"google\.search\.cse\.[^\(]+\((.*?)\);"
        response_json = json.loads(
            re.search(pattern, response_text, re.DOTALL).group(1)
        )
        articles = response_json["results"]
