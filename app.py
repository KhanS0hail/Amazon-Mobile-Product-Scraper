from flask import Flask, render_template, request, jsonify, Response, send_file
import os
import json
import pandas as pd
from scraper import AmazonScraper
import io

app = Flask(__name__)

# Global storage for the latest search scrape results
latest_results = []
latest_keyword = ""
latest_domain = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape/search/stream')
def search_stream():
    global latest_results, latest_keyword, latest_domain
    
    keyword = request.args.get('keyword', '').strip()
    domain = request.args.get('domain', 'amazon.in').strip()
    pages_str = request.args.get('pages', '1').strip()
    
    try:
        pages = int(pages_str)
        if pages < 1:
            pages = 1
        if pages > 20: # Cap at 20 pages to prevent blocking
            pages = 20
    except ValueError:
        pages = 1

    if not keyword:
        def error_generator():
            yield "data: [ERROR] Keyword cannot be empty.\n\n"
        return Response(error_generator(), mimetype='text/event-stream')

    latest_keyword = keyword
    latest_domain = domain

    def generator():
        global latest_results
        
        yield f"data: [START] Initializing scraper for keyword: '{keyword}' on {domain} (Max Pages: {pages})...\n\n"
        
        scraper = AmazonScraper(domain=domain)
        
        local_results = []
        
        def log_cb(msg):
            # Format and send SSE packet
            # We prefix lines with a specific header if needed
            yield f"data: {msg}\n\n"
        
        
        import requests
        from bs4 import BeautifulSoup
        import random
        import time
        from urllib.parse import quote_plus

        encoded_keyword = quote_plus(keyword)
        search_base = f"{scraper.base_url}/s?k={encoded_keyword}&page={{}}"

        session = scraper.get_session()
        page = 1
        while page <= pages:
            yield f"data: [PROGRESS] Fetching page {page} of results for '{keyword}'...\n\n"
            url = search_base.format(page)
            
            try:
                if page > 1:
                    sleep_time = round(random.uniform(2.0, 4.0), 2)
                    yield f"data: [PROGRESS] Sleeping for {sleep_time}s to avoid rate limiting...\n\n"
                    time.sleep(sleep_time)

                response = scraper.fetch_url(url)
                
                if response.status_code != 200:
                    yield f"data: [ERROR] HTTP Error {response.status_code} on page {page}.\n\n"
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                
                if "captcha" in response.text.lower() or "robot check" in response.text.lower():
                    yield "data: [ERROR] CAPTCHA detected! Amazon blocked this request. Try again later or use a different IP/proxy.\n\n"
                    break

                products = soup.find_all('div', {'data-component-type': 's-search-result'})
                yield f"data: [PROGRESS] Found {len(products)} products on page {page}.\n\n"
                
                if not products:
                    if "no results for" in response.text.lower():
                        yield "data: [PROGRESS] No results matched the query on Amazon.\n\n"
                        break
                    else:
                        yield "data: [ERROR] No product elements found. Amazon layout might have changed or blocking is active.\n\n"
                        break

                page_count = 0
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
                        product_url = f"{scraper.base_url}{url_el['href']}" if (url_el and 'href' in url_el.attrs) else ''
                        if not product_url and title_el:
                            title_link = title_el.find('a')
                            if title_link and 'href' in title_link.attrs:
                                product_url = f"{scraper.base_url}{title_link['href']}"

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
                            price_val = scraper.clean_price(price_str)
                        else:
                            offscreen = product.find('span', class_='a-offscreen')
                            if offscreen:
                                price_str = offscreen.text.strip()
                                price_val = scraper.clean_price(price_str)

                        # Rating
                        rating_str = 'Rating not available'
                        rating_el = product.find('span', {'class': 'a-icon-alt'})
                        if rating_el:
                            rating_str = rating_el.text.strip()
                        rating_val = scraper.clean_rating(rating_str)

                        # Reviews Count
                        reviews_str = 'No reviews'
                        reviews_el = product.find('span', class_='a-size-base')
                        if reviews_el:
                            reviews_str = reviews_el.text.strip()
                        reviews_link = product.find('a', class_=lambda c: c and 'a-link-normal' in c and 's-underline-text' in c)
                        if reviews_link:
                            reviews_str = reviews_link.text.strip()
                        reviews_val = scraper.clean_reviews(reviews_str)

                        # Image URL
                        img_el = product.find('img', class_='s-image')
                        img_url = img_el['src'] if (img_el and 'src' in img_el.attrs) else ''

                        # Availability
                        availability = 'Availability not listed'
                        social_proof = product.find('span', class_='a-size-base a-color-secondary')
                        if social_proof and ('bought' in social_proof.text or 'ordered' in social_proof.text):
                            availability = social_proof.text.strip()
                        else:
                            availability_div = product.find('div', class_='a-section a-spacing-none a-spacing-top-micro')
                            if availability_div:
                                availability_text = availability_div.find('span', class_='a-size-base a-color-secondary')
                                if availability_text:
                                    availability = availability_text.text.strip()

                        # Delivery
                        delivery_text = 'Delivery info not available'
                        free_delivery_date = 'No info'
                        fast_delivery_date = 'No info'
                        
                        del_info = product.find('div', class_=lambda c: c and 's-align-children-center' in c)
                        if not del_info:
                            del_info = product.find('div', class_='a-row a-size-base a-color-secondary s-align-children-center')
                        
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

                        local_results.append({
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
                        page_count += 1
                    except Exception as e:
                        yield f"data: [PROGRESS] Warning: Parse error on item: {str(e)}\n\n"
                        continue

                yield f"data: [PROGRESS] Scraped {page_count} items from page {page}.\n\n"

                if page < pages and scraper.has_next_page(soup):
                    page += 1
                else:
                    yield "data: [PROGRESS] Reached the end of available pages.\n\n"
                    break

            except Exception as e:
                yield f"data: [ERROR] Exception error on page {page}: {str(e)}\n\n"
                break

        latest_results = local_results
        
        # Save to CSV in workspace for convenience
        try:
            df = pd.DataFrame(local_results)
            csv_path = 'amazon_products_scraped.csv'
            df.to_csv(csv_path, index=False, encoding='utf-8')
            yield f"data: [PROGRESS] Saved backup to local CSV: {csv_path}\n\n"
        except Exception as e:
            yield f"data: [PROGRESS] Warning: Could not save local CSV backup: {str(e)}\n\n"

        yield f"data: [COMPLETE] Successfully scraped {len(local_results)} products!\n\n"

    return Response(generator(), mimetype='text/event-stream')

@app.route('/api/scrape/results', methods=['GET'])
def get_results():
    global latest_results, latest_keyword, latest_domain
    return jsonify({
        'keyword': latest_keyword,
        'domain': latest_domain,
        'count': len(latest_results),
        'results': latest_results
    })

@app.route('/api/scrape/product', methods=['POST'])
def scrape_single_product():
    data = request.json or {}
    url_or_asin = data.get('url_or_asin', '').strip()
    domain = data.get('domain', 'amazon.in').strip()

    if not url_or_asin:
        return jsonify({'error': 'Product URL or ASIN is required'}), 400

    scraper = AmazonScraper(domain=domain)
    product_details = scraper.scrape_product_details(url_or_asin)
    
    if product_details:
        return jsonify(product_details)
    else:
        return jsonify({'error': 'Failed to scrape product details. Amazon may have blocked the request or the URL is invalid.'}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    global latest_results, latest_keyword
    export_format = request.args.get('format', 'csv').lower()
    
    if not latest_results:
        return jsonify({'error': 'No data available to export. Run a search scrape first.'}), 400

    df = pd.DataFrame(latest_results)
    
    # Sanitize keyword for filename
    filename_keyword = "".join([c if c.isalnum() else "_" for c in latest_keyword])
    if not filename_keyword:
        filename_keyword = "amazon_data"

    if export_format == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(
            mem,
            as_attachment=True,
            download_name=f"{filename_keyword}_export.csv",
            mimetype='text/csv'
        )
        
    elif export_format == 'excel':
        mem = io.BytesIO()
        with pd.ExcelWriter(mem, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Amazon Scraped')
        mem.seek(0)
        return send_file(
            mem,
            as_attachment=True,
            download_name=f"{filename_keyword}_export.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    elif export_format == 'json':
        output = df.to_json(orient='records', indent=2)
        mem = io.BytesIO()
        mem.write(output.encode('utf-8'))
        mem.seek(0)
        return send_file(
            mem,
            as_attachment=True,
            download_name=f"{filename_keyword}_export.json",
            mimetype='application/json'
        )
        
    else:
        return jsonify({'error': 'Unsupported format. Use csv, excel, or json.'}), 400

if __name__ == '__main__':
    # Verify templates folder exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask server on port {port}...")
    print(f"Please open http://127.0.0.1:{port} in your browser.")
    app.run(debug=True, host='0.0.0.0', port=port)
