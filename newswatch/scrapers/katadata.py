import logging
import json
import asyncio

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .basescraper import BaseScraper


class KatadataScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "katadata.co.id"
        self.api_url = "https://search.katadata.co.id/api/search"
        self.start_date = start_date
        self.continue_scraping = True
        self.bearer_token = None

    async def get_bearer_token(self):
        if self.bearer_token:
            return self.bearer_token
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set up request interception to capture the API call with the Bearer token
            api_request = asyncio.Future()
            
            async def handle_request(request):
                if self.api_url in request.url:
                    headers = request.headers
                    if 'authorization' in headers:
                        auth_header = headers['authorization']
                        if auth_header.startswith('Bearer '):
                            token = auth_header.split('Bearer ')[1]
                            if not api_request.done():
                                api_request.set_result(token)
            
            # Listen for requests
            await page.route('**/*', lambda route: route.continue_())
            page.on('request', handle_request)
            
            # Navigate to search page with a test query
            search_query = f"https://search.{self.base_url}/search?q=&order_by_date=true&from_most_recent=true"
            await page.goto(search_query)
            
            # Wait for the API call to happen and extract token (with 10s timeout)
            try:
                self.bearer_token = await asyncio.wait_for(api_request, 10)
                logging.info("Bearer token successfully extracted")
            except asyncio.TimeoutError:
                logging.error("Failed to capture Bearer token from network requests")
                self.bearer_token = None
            
            await browser.close()
            
        return self.bearer_token

    async def build_search_url(self, keyword, page):
        # Ensure we have a bearer token
        token = await self.get_bearer_token()
        if not token:
            logging.error("Failed to obtain Bearer token, search may fail")

        payload = {
            "prompt": keyword,
            "offset": (page - 1) * 10,
            "source": "katadata",
            "kanal_or_topic": "",
            "order_by_date": "true",
            "from_most_recent": "true"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0"
        }
        
        return await self.fetch(
            self.api_url,
            method="POST",
            data=json.dumps(payload),
            headers=headers,
            timeout=45
        )

    def parse_article_links(self, response_text):
        try:
            response_json = json.loads(response_text)
        except Exception as e:
            logging.error(f"Error decoding JSON response: {e}")
            return None
            
        articles = response_json.get("results", [])
        if not articles:
            return None
            
        filtered_hrefs = {
            article.get("url") for article in articles
            if article.get("url")
        }
        return filtered_hrefs

    async def get_article(self, link, keyword):
        response_text = await self.fetch(link)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")
        try:
            category = soup.select_one(".section-breadcrumb").get_text(strip=True)
            title = soup.select_one(".detail-title.mb-4").get_text(strip=True)
            author = (
                soup.select_one(".detail-author-name")
                .get_text(strip=True)
                .replace("Oleh", "")
            )
            publish_date_str = soup.select_one(".detail-date.text-gray").get_text(
                strip=True
            )

            # content_div = soup.find_all("div", class_ = "detail-main")
            content_div = soup.select_one(".detail-main")

            # loop through paragraphs and remove those with class patterns "widget-baca-juga*" or if any class contains "ai-summary"
            for tag in content_div.find_all("div"):
                classes = tag.get("class", [])
                if tag and (
                    any(cls.startswith("widget-baca-juga") for cls in classes)
                    or any("ai-summary" in cls for cls in classes)
                ):
                    tag.extract()

            content = content_div.get_text(separator="\n", strip=True)

            publish_date = self.parse_date(publish_date_str, locales=["id"])
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
