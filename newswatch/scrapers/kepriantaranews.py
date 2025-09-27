import logging
import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper

# from .sentiment import classify_sentiment_id


class KepriAntaranewsScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "https://kepri.antaranews.com"
        self.start_date = start_date
        self.continue_scraping = True
        # Pattern for Kepri Antara News article URLs
        self.href_pattern = re.compile(r"https://kepri\.antaranews\.com/berita/.*")

    async def build_search_url(self, keyword, page):
        """
        Build search URL for Kepri Antara News - STRICT SEARCH ONLY
        Only returns results if the search actually works, no homepage fallback
        """
        # Try the standard search first
        query_params = {"q": keyword, "page": page}
        search_url = f"{self.base_url}/search?{urlencode(query_params)}"
        logging.info(f"Searching for '{keyword}' on page {page}: {search_url}")
        
        response_text = await self.fetch(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Check if we got a proper search results page
        if response_text and len(response_text) > 1000:
            # Verify this is actually a search results page, not an error page
            if "search" in response_text.lower() or keyword.lower() in response_text.lower():
                logging.info(f"Search appears successful for keyword: {keyword}")
                return response_text
            else:
                logging.warning(f"Search page doesn't seem to contain results for: {keyword}")
        
        # If search doesn't work, try tag-based approach (more targeted than homepage)
        logging.warning(f"Primary search failed, trying tag-based search for: {keyword}")
        tag_url = f"{self.base_url}/tag/{keyword.lower().replace(' ', '-').replace(',', '')}"
        if page > 1:
            tag_url += f"?page={page}"
        
        logging.info(f"Trying tag URL: {tag_url}")
        response_text = await self.fetch(tag_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response_text and len(response_text) > 1000:
            logging.info(f"Tag-based search appears successful for keyword: {keyword}")
            return response_text
        
        # NO HOMEPAGE FALLBACK - if search fails, return None
        logging.error(f"All search methods failed for keyword: {keyword}. No results found.")
        return None

    def parse_article_links(self, response_text):
        """
        Parse article links from search results page
        Enhanced to handle multiple page structures
        """
        if not response_text:
            return None
            
        soup = BeautifulSoup(response_text, "html.parser")
        found_links = []
        
        # Multiple selectors to try for different page layouts
        selectors_to_try = [
            # Main Antara News style selectors
            ".card__post.card__post-list.card__post__transition.mt-30 a",
            ".card__post a",
            ".post-item a",
            ".article-item a",
            
            # Homepage/category page selectors
            ".card a",
            ".post a", 
            ".news-item a",
            
            # Generic article link patterns
            "a[href*='/berita/']",
            "a[href*='/news/']",
        ]
        
        for selector in selectors_to_try:
            articles = soup.select(selector)
            if articles:
                logging.info(f"Found {len(articles)} potential links with selector: {selector}")
                for a in articles:
                    href = a.get("href")
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            href = self.base_url + href
                        
                        # Check if it matches our pattern
                        if self.href_pattern.match(href):
                            found_links.append(href)
                
                if found_links:
                    break
        
        # If still no links found, try finding ANY links that look like article URLs
        if not found_links:
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                href = link.get("href")
                if href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    
                    # Broader pattern matching for Kepri articles
                    if "kepri.antaranews.com" in href and "/berita/" in href:
                        found_links.append(href)
        
        # Remove duplicates and log results
        unique_links = list(set(found_links))
        
        if unique_links:
            logging.info(f"Successfully found {len(unique_links)} unique article links")
            # Log first few links for debugging
            for i, link in enumerate(unique_links[:3]):
                logging.info(f"Sample link {i+1}: {link}")
            return unique_links
        else:
            logging.warning("No article links found on this page")
            # Log the page content snippet for debugging
            text_content = soup.get_text()[:500]
            logging.debug(f"Page content preview: {text_content}")
            return None

    async def get_article(self, link, keyword):
        """
        Extract article content from individual article page
        WITH KEYWORD RELEVANCE FILTERING
        """
        response_text = await self.fetch(f"{link}")
        if not response_text:
            logging.warning(f"No response for {link}")
            return
            
        soup = BeautifulSoup(response_text, "html.parser")
        
        try:
            # Extract category - try multiple selectors
            category = ""
            category_selectors = [
                ".breadcrumbs__item",
                ".breadcrumb-item",
                ".category",
                ".post-category"
            ]
            
            for selector in category_selectors:
                category_elements = soup.select(selector)
                if len(category_elements) > 1:
                    category = category_elements[1].get_text(strip=True)
                    break
                elif len(category_elements) == 1:
                    category = category_elements[0].get_text(strip=True)
                    break
            
            if not category:
                category = "Kepri"  # Default category for regional news

            # Extract title - try multiple selectors
            title = ""
            title_selectors = [
                ".wrap__article-detail-title",
                ".post-title",
                ".article-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            if not title:
                logging.warning(f"Could not extract title from {link}")
                return

            # Extract author - try multiple selectors
            author = ""
            author_selectors = [
                ".text-muted.mt-2.small",
                ".author",
                ".post-author",
                ".by-author"
            ]
            
            for selector in author_selectors:
                author_element = soup.select_one(selector)
                if author_element:
                    author = author_element.get_text(strip=True)
                    break
            
            if not author:
                author = "ANTARA Kepri"  # Default author

            # Extract publish date - try multiple selectors
            publish_date_str = ""
            date_selectors = [
                ".list-inline-item.mr-2",
                ".post-date",
                ".publish-date",
                ".date"
            ]
            
            for selector in date_selectors:
                date_elements = soup.select(selector)
                if date_elements:
                    publish_date_str = date_elements[-1].get_text(strip=True)
                    break
            
            # Try alternative date extraction from meta tags
            if not publish_date_str:
                date_meta = soup.find("meta", {"property": "article:published_time"}) or \
                           soup.find("meta", {"name": "date"}) or \
                           soup.find("time")
                if date_meta:
                    publish_date_str = date_meta.get("content") or date_meta.get_text(strip=True)

            # Extract content - try multiple selectors
            content = ""
            content_selectors = [
                ".wrap__article-detail-content.post-content",
                ".post-content",
                ".article-content",
                ".content"
            ]
            
            

            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if content_div:
                # Remove unwanted elements
                for tag in content_div.find_all(["span", "p"]):
                    classes = tag.get("class", [])
                    if any(cls in ["baca-juga", "text-muted", "track-", "related"] 
                           for cls in classes):
                        tag.extract()
                
                # Remove advertisements and related content
                for tag in content_div.find_all(text=lambda text: 
                    text and any(word in text.lower() 
                    for word in ["baca juga", "iklan", "advertisement", "related"])):
                    if tag.parent:
                        tag.parent.extract()
                
                content = content_div.get_text(separator="\n", strip=True)
            
            if not content:
                logging.warning(f"Could not extract content from {link}")
                return
            
         #    sentiment = classify_sentiment_id(title)

            # *** KEYWORD RELEVANCE CHECK ***
            # Check if the article is actually related to our search keyword
            search_text = f"{title} {content}".lower()
            keyword_lower = keyword.lower()
            
            # Split keyword by common separators
            keywords_to_check = [kw.strip() for kw in keyword_lower.replace(',', ' ').split()]
            
            # Check if any keyword appears in title or content
            keyword_found = False
            for kw in keywords_to_check:
                if kw in search_text:
                    keyword_found = True
                    break
            
            if not keyword_found:
                logging.info(f"Article '{title[:50]}...' doesn't contain keyword '{keyword}' - skipping")
                return

            # Parse and validate date
            publish_date = self.parse_date(publish_date_str, locales=["id"])
            if not publish_date:
                logging.error(f"Error parsing date '{publish_date_str}' for article {link}")
                return
                
            # Check date filter
            if self.start_date and publish_date < self.start_date:
                self.continue_scraping = False
                return

            # Create article item
            item = {
                "title": title,
                "publish_date": publish_date,
                "author": author,
                "content": content,
                "keyword": keyword,
                "category": category,
                "source": "kepri.antaranews.com",
                "link": link,
             #    "sentiment": sentiment
            }
            
            await self.queue_.put(item)
            logging.info(f"✅ Successfully scraped relevant article: {title[:50]}...")
            
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")

    async def scrape(self):
        """
        Main scraping method with enhanced error handling
        """
        try:
            await super().scrape()
        except Exception as e:
            logging.error(f"Error in KepriAntaranewsScraper: {e}")
            raise