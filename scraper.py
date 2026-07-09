import requests
from bs4 import BeautifulSoup
import random
import time
import re
from urllib.parse import quote_plus, urlparse

# Browser profiles with matching User-Agent and Client Hints to pass checks
BROWSER_PROFILES = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-platform": '"Windows"'
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-platform": '"macOS"'
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="122", "Not:A-Brand";v="24", "Chromium";v="122"',
        "sec-ch-ua-platform": '"Windows"'
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="122", "Not:A-Brand";v="24", "Chromium";v="122"',
        "sec-ch-ua-platform": '"macOS"'
    }
]

class AmazonScraper:
    def __init__(self, domain="amazon.in"):
        # Normalize domain
        if not domain.startswith("amazon."):
            domain = f"amazon.{domain}"
        self.domain = domain
        self.base_url = f"https://www.{domain}"
        self.session = None
        self.current_profile = random.choice(BROWSER_PROFILES)
        
        self.base_headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1"
        }

    def _get_headers(self):
        headers = self.base_headers.copy()
        # Ensure User-Agent and Client Hints match to prevent mismatch signals
        headers["User-Agent"] = self.current_profile["User-Agent"]
        headers["sec-ch-ua"] = self.current_profile["sec-ch-ua"]
        headers["sec-ch-ua-platform"] = self.current_profile["sec-ch-ua-platform"]
        headers["sec-ch-ua-mobile"] = "?0"
        return headers

    def get_session(self):
        if not self.session:
            self.session = requests.Session()
            # Set initial headers
            self.session.headers.update(self._get_headers())
            
            # Warm up: Visit home page to acquire session cookies
            try:
                # Add a brief delay
                time.sleep(random.uniform(0.5, 1.5))
                self.session.get(self.base_url, timeout=12)
            except Exception:
                pass
        return self.session

    def fetch_url(self, url):
        import os
        api_key = os.environ.get("SCRAPER_API_KEY")
        if api_key:
            proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={quote_plus(url)}"
            return requests.get(proxy_url, timeout=30)
            
        proxy_http = os.environ.get("PROXY_URL")
        if proxy_http:
            proxies = {
                "http": proxy_http,
                "https": proxy_http
            }
            return requests.get(url, headers=self._get_headers(), proxies=proxies, timeout=20)
            
        session = self.get_session()
        return session.get(url, timeout=15)

    def has_next_page(self, soup):
        # Look for the "Next" button in the pagination container
        pagination = soup.find('span', class_='s-pagination-strip')
        if pagination:
            next_btn = pagination.find('a', class_='s-pagination-next') or pagination.find('span', class_='s-pagination-next')
            if next_btn and 's-pagination-disabled' not in next_btn.get('class', []):
                return True
        
        # Fallback to the notebook style
        div_button = soup.find('div', class_='a-section a-text-center s-pagination-container')
        if div_button:
            next_link = div_button.find('a', class_=lambda c: c and 's-pagination-next' in c)
            if next_link:
                return True
        return False

    def clean_price(self, price_str):
        if not price_str or "not listed" in price_str.lower():
            return None
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned)
        except ValueError:
            return None

    def clean_rating(self, rating_str):
        if not rating_str or "not available" in rating_str.lower():
            return None
        # Match something like "4.5 out of 5 stars" or "4.5"
        match = re.search(r'([0-9.]+)\s*(?:out of|/)\s*5', rating_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        # Fallback to direct number extraction
        match_simple = re.search(r'([0-9.]+)', rating_str)
        if match_simple:
            try:
                val = float(match_simple.group(1))
                if val <= 5.0:
                    return val
            except ValueError:
                pass
        return None

    def clean_reviews(self, reviews_str):
        if not reviews_str or "no reviews" in reviews_str.lower():
            return 0
        # Remove commas, brackets, etc.
        cleaned = re.sub(r'[^\d]', '', reviews_str)
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def scrape_search_results(self, keyword, max_pages=3, log_callback=None):
        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

        results = []
        # URL encode keyword
        encoded_keyword = quote_plus(keyword)
        search_base = f"{self.base_url}/s?k={encoded_keyword}&page={{}}"

        page = 1
        while page <= max_pages:
            log(f"Fetching page {page} of results for '{keyword}'...")
            url = search_base.format(page)
            
            try:
                # Add delay to avoid immediate blocking (1-3 seconds)
                if page > 1:
                    sleep_time = random.uniform(1.5, 3.5)
                    log(f"Sleeping for {sleep_time:.2f}s to prevent rate limiting...")
                    time.sleep(sleep_time)

                headers = self._get_headers()
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    log(f"HTTP Error {response.status_code} on page {page}.")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for CAPTCHA
                if "captcha" in response.text.lower() or "robot check" in response.text.lower():
                    log("CAPTCHA detected! Amazon blocked this request. Try again later or use a different IP/proxy.")
                    break

                products = soup.find_all('div', {'data-component-type': 's-search-result'})
                log(f"Found {len(products)} products on page {page}.")
                
                if not products:
                    # Let's check if the page looks like a 0 result page or layout change
                    if "no results for" in response.text.lower():
                        log("No results matched the query on Amazon.")
                        break
                    else:
                        log("No product elements found. Amazon layout might have changed or blocking is active.")
                        # Save HTML for debug sometimes, but let's break for now
                        break

                for product in products:
                    try:
                        asin = product.get('data-asin', '')
                        if not asin:
                            continue

                        # Title
                        title_el = product.find('h2')
                        title = title_el.text.strip() if title_el else 'No title available'

                        # URL
                        url_el = product.find('a', class_='a-link-normal s-no-outline')
                        product_url = f"{self.base_url}{url_el['href']}" if (url_el and 'href' in url_el.attrs) else ''
                        if not product_url and title_el:
                            title_link = title_el.find('a')
                            if title_link and 'href' in title_link.attrs:
                                product_url = f"{self.base_url}{title_link['href']}"

                        # Price
                        price_val = None
                        price_str = 'Price not listed'
                        price_whole_el = product.find('span', 'a-price-whole')
                        price_fraction_el = product.find('span', 'a-price-fraction')
                        price_symbol_el = product.find('span', 'a-price-symbol')
                        
                        if price_whole_el:
                            price_str = price_whole_el.text.strip()
                            if price_fraction_el:
                                price_str += "." + price_fraction_el.text.strip()
                            if price_symbol_el:
                                price_str = price_symbol_el.text.strip() + price_str
                            
                            price_val = self.clean_price(price_str)
                        else:
                            # Try general offscreen price
                            offscreen = product.find('span', class_='a-offscreen')
                            if offscreen:
                                price_str = offscreen.text.strip()
                                price_val = self.clean_price(price_str)

                        # Rating
                        rating_str = 'Rating not available'
                        rating_el = product.find('span', {'class': 'a-icon-alt'})
                        if rating_el:
                            rating_str = rating_el.text.strip()
                        rating_val = self.clean_rating(rating_str)

                        # Reviews Count
                        reviews_str = 'No reviews'
                        # Usually reviews count is a sibling or near rating, with class a-size-base
                        reviews_el = product.find('span', class_='a-size-base')
                        if reviews_el:
                            reviews_str = reviews_el.text.strip()
                        # Often review count has search-results context
                        reviews_link = product.find('a', class_=lambda c: c and 'a-link-normal' in c and 's-underline-text' in c)
                        if reviews_link:
                            reviews_str = reviews_link.text.strip()
                        reviews_val = self.clean_reviews(reviews_str)

                        # Image URL
                        img_el = product.find('img', class_='s-image')
                        img_url = img_el['src'] if (img_el and 'src' in img_el.attrs) else ''

                        # Availability / Sales (e.g. "5K+ bought in past month")
                        availability = 'Availability not listed'
                        social_proof = product.find('span', class_='a-size-base a-color-secondary')
                        if social_proof and ('bought' in social_proof.text or 'ordered' in social_proof.text):
                            availability = social_proof.text.strip()
                        else:
                            # check standard container
                            availability_div = product.find('div', class_='a-section a-spacing-none a-spacing-top-micro')
                            if availability_div:
                                availability_text = availability_div.find('span', class_='a-size-base a-color-secondary')
                                if availability_text:
                                    availability = availability_text.text.strip()

                        # Delivery Details
                        delivery_text = 'Delivery info not available'
                        free_delivery_date = 'No info'
                        fast_delivery_date = 'No info'
                        
                        if del_info:
                            bold_spans = [s.text.strip() for s in del_info.find_all('span', class_='a-text-bold') if s.text.strip()]
                            if bold_spans:
                                free_delivery_date = bold_spans[0]
                                if len(bold_spans) > 1:
                                    fast_delivery_date = bold_spans[1]

                            # Determine delivery text
                            full_text = del_info.text.strip()
                            if "FREE delivery" in full_text or "Free delivery" in full_text or "free delivery" in full_text:
                                delivery_text = "FREE delivery"
                            elif "Fastest delivery" in full_text or "fastest delivery" in full_text:
                                delivery_text = "Fastest delivery"
                            else:
                                spans = [s.text.strip() for s in del_info.find_all('span') if s.text.strip()]
                                non_bold = [s for s in spans if s not in bold_spans and len(s) > 2 and s not in ["Or", "or", "Get it by", "get it by"]]
                                if non_bold:
                                    delivery_text = non_bold[0]
                                elif spans:
                                    delivery_text = spans[0]
                                else:
                                    delivery_text = "Delivery info available"
                        
                        results.append({
                            'ASIN': asin,
                            'Product Title': title,
                            'Price Display': price_str,
                            'Price Value': price_val,
                            'Rating Display': rating_str,
                            'Rating Value': rating_val,
                            'Number of Reviews': reviews_val,
                            'Availability': availability,
                            'Delivery': delivery_text,
                            'Free Delivery Date': free_delivery_date,
                            'Fast Delivery Date': fast_delivery_date,
                            'Image URL': img_url,
                            'Product URL': product_url
                        })
                    except Exception as e:
                        log(f"Error parsing a product item: {str(e)}")
                        continue

                # Check if there is another page
                if page < max_pages and self.has_next_page(soup):
                    page += 1
                else:
                    log("No more pages available or maximum page limit reached.")
                    break

            except Exception as e:
                log(f"Exception error while scraping page {page}: {str(e)}")
                break

        log(f"Scraping completed. Successfully collected {len(results)} items.")
        return results

    def scrape_product_details(self, product_id_or_url, log_callback=None):
        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

        # Parse inputs to figure out if ASIN or URL is supplied
        url = product_id_or_url
        if not product_id_or_url.startswith("http"):
            # It's probably an ASIN
            url = f"{self.base_url}/dp/{product_id_or_url}"
            log(f"Constructed URL from ASIN: {url}")
        else:
            log(f"Navigating to product URL: {url}")
            # Try to extract domain from the URL to use correct base URL
            try:
                parsed_url = urlparse(url)
                netloc = parsed_url.netloc
                if netloc.startswith("www."):
                    netloc = netloc[4:]
                if netloc.startswith("amazon."):
                    self.domain = netloc
                    self.base_url = f"https://www.{netloc}"
            except Exception:
                pass

        try:
            session = self.get_session()
            response = session.get(url, timeout=15)
            
            if response.status_code != 200:
                log(f"Failed to retrieve product page. HTTP status code: {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            if "captcha" in response.text.lower() or "robot check" in response.text.lower():
                log("CAPTCHA detected! Amazon blocked this request. Single product page could not be scraped.")
                return None

            # Title
            title_el = soup.find('span', id='productTitle')
            title = title_el.text.strip() if title_el else 'No title available'

            # Price
            price_display = 'Price not listed'
            price_value = None
            # Check multiple price blocks
            price_container = soup.find('div', id='corePrice_feature_div') or soup.find('div', id='apex_desktop')
            if price_container:
                price_offscreen = price_container.find('span', class_='a-offscreen')
                if price_offscreen:
                    price_display = price_offscreen.text.strip()
                    price_value = self.clean_price(price_display)
            
            if not price_value or price_display == 'Price not listed':
                # Try generic price elements
                price_el = soup.find('span', class_='a-price')
                if price_el:
                    price_offscreen = price_el.find('span', class_='a-offscreen')
                    if price_offscreen:
                        price_display = price_offscreen.text.strip()
                        price_value = self.clean_price(price_display)

            # Rating
            rating_display = 'Rating not available'
            rating_value = None
            star_el = soup.find('span', class_='a-icon-alt')
            if not star_el:
                popover_el = soup.find('span', id='acrPopover') or soup.find('a', class_='a-popover-trigger')
                if popover_el:
                    star_el = popover_el.find('span', class_='a-icon-alt') or popover_el
            
            if star_el:
                rating_display = star_el.text.strip()
                rating_value = self.clean_rating(rating_display)
            
            # Reviews / Ratings Volume Count
            reviews_count = 0
            rating_el = (soup.find('span', id='acrCustomerReviewText') or 
                         soup.find('span', class_='acrCustomerReviewText') or
                         soup.find('a', id='acrCustomerReviewLink') or
                         soup.find(id='acrCustomerReviewText'))
            if rating_el:
                reviews_count = self.clean_reviews(rating_el.text.strip())

            # Brand
            brand_el = soup.find('a', id='bylineInfo') or soup.find('div', id='bylineInfo_feature_div')
            brand = brand_el.text.strip() if brand_el else 'Brand not listed'
            # Clean up Brand text
            brand = re.sub(r'Visit the\s+', '', brand, flags=re.I)
            brand = re.sub(r'\s+Store', '', brand, flags=re.I)
            brand = brand.replace('Brand:', '').strip()

            # Image
            image_url = ''
            img_div = soup.find('div', id='imgTagWrapperId')
            if img_div:
                img_el = img_div.find('img')
                if img_el:
                    image_url = img_el.get('src', img_el.get('data-old-hires', ''))
            
            if not image_url:
                # Fallback to landing image
                landing_img = soup.find('img', id='landingImage')
                if landing_img:
                    image_url = landing_img.get('src', '')
                    if not image_url and 'data-a-dynamic-image' in landing_img.attrs:
                        # Extract the first image from dynamic image JSON
                        dynamic_images = landing_img['data-a-dynamic-image']
                        match = re.search(r'"(https://[^"]+)"', dynamic_images)
                        if match:
                            image_url = match.group(1)

            # Product Description / About This Item
            description_list = []
            about_div = soup.find('div', id='feature-bullets')
            if about_div:
                bullets = about_div.find_all('li')
                for bullet in bullets:
                    bullet_text = bullet.text.strip()
                    # Filter out empty bullets or cookie notices
                    if bullet_text and not bullet.get('id') == 'replacementTemplate':
                        description_list.append(bullet_text)
            
            # Specs Table / Product Details
            specs = {}
            # Check for details table (usually has class a-keyvalue or is in prodDetails)
            details_tables = soup.find_all('table', class_=lambda c: c and ('a-keyvalue' in c or 'prodDetTable' in c))
            for table in details_tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th') or row.find('td', class_='a-span3')
                    td = row.find('td') or row.find('td', class_='a-span9')
                    if th and td:
                        key = th.text.strip().replace('\n', '')
                        val = td.text.strip().replace('\n', '')
                        # Normalize multiple spaces
                        key = re.sub(r'\s+', ' ', key)
                        val = re.sub(r'\s+', ' ', val)
                        if key and val:
                            specs[key] = val

            # Also check alternative listing for details block if table not found
            if not specs:
                details_list = soup.find('div', id='detailBullets_feature_div')
                if details_list:
                    items = details_list.find_all('li')
                    for item in items:
                        spans = item.find_all('span')
                        if len(spans) >= 2:
                            key = spans[0].text.strip().replace(':', '').replace('\n', '')
                            val = spans[1].text.strip().replace('\n', '')
                            key = re.sub(r'\s+', ' ', key)
                            val = re.sub(r'\s+', ' ', val)
                            if key and val:
                                specs[key] = val

            # Availability
            availability_el = soup.find('div', id='availability')
            availability = availability_el.text.strip() if availability_el else 'Availability not listed'
            availability = re.sub(r'\s+', ' ', availability)

            # Rating Histogram
            histogram = {}
            histo_table = soup.find('table', id='histogramTable')
            if not histo_table:
                histo_table = soup.find('table', class_=lambda c: c and 'histogram' in c.lower())
            if not histo_table:
                histo_div = soup.find('div', class_=lambda c: c and 'histogram' in c.lower())
                if histo_div:
                    histo_table = histo_div.find('table')
            
            if histo_table:
                rows = histo_table.find_all('tr')
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            label = cells[0].text.strip()
                            pct_text = cells[2].text.strip()
                            
                            match = re.search(r'(\d+)\s*(?:star|stars)', label, re.I)
                            if match:
                                label = f"{match.group(1)} Star"
                                pct = re.sub(r'[^\d]', '', pct_text)
                                if pct.isdigit():
                                    histogram[label] = int(pct)
                    except Exception:
                        continue

            # Store scraped details
            product_details = {
                'Title': title,
                'Price Display': price_display,
                'Price Value': price_value,
                'Rating Display': rating_display,
                'Rating Value': rating_value,
                'Reviews Count': reviews_count,
                'Brand': brand,
                'Availability': availability,
                'Image URL': image_url,
                'Product URL': url,
                'Bullet Points': description_list,
                'Specifications': specs,
                'Rating Histogram': histogram
            }
            log(f"Successfully scraped details for product: {title[:50]}...")
            return product_details

        except Exception as e:
            log(f"Exception error while scraping single product details: {str(e)}")
            return None
