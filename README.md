# Amazon Product Intelligence Scraper

A premium, monochromatic light-themed web dashboard that upgrades standard product searching and single product specifications scraping into a comprehensive product intelligence tool. The application allows users to search keywords dynamically, inspect detailed product specifications, and export the scraped datasets.

---

## Key Features & Implementations 

1. **Web Dashboard Interface**:
   - Built on a lightweight, concurrent **Flask** backend.
   - Styled with a modern, high-contrast black-and-white minimalist design.
   - Features a sidebar-based layout, a responsive 11-column data table, and interactive progress logs.

2. **Generic Keyword Scraper**:
   - Supports search queries for any product keyword.
   - Allows selection from multiple Amazon regional storefronts: India (`amazon.in`), United States (`amazon.com`), United Kingdom (`amazon.co.uk`), Germany (`amazon.de`), and Canada (`amazon.ca`).
   - Supports scraping multiple result pages with dynamic progress estimation.

3. **Product Detail Inspector**:
   - Parses specific product pages via ASIN or direct URL inputs.
   - Extracts Brand name, Bullet point features, Product image, and complete technical specifications tables (such as RAM, Storage, Manufacturer details, Weight, Dimensions).

4. **Multi-Format Data Exporter**:
   - Supports downloading scraped datasets in **CSV**, **Excel (XLSX)**, or **JSON** formats.

5. **Anti-Blocking Adaptations**:
   - Implements aligned **Browser Profiles** matching user-agents and client-hints (such as `sec-ch-ua` and `sec-ch-ua-platform`) to minimize bot detection triggers.
   - Features `requests.Session` cookie persistence with initial domain warm-ups.
   - Includes optional **Proxy Routing Integration** (via ScraperAPI or custom HTTP proxies) to bypass datacenter IP blocks and 503 errors in production.

---

## Local Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd Amazon-Mobile-Product-Scraper
   ```

2. **Create a Virtual Environment**:
   * macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * Windows:
     ```bash
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Server**:
   ```bash
   python app.py
   ```

5. **Open Dashboard**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in the browser.


---


## Future Plans & Roadmap
- **Interactive Visual Analytics**: Integrate dynamic Chart.js libraries to display price range bar charts for keyword listing statistics and customer review rating breakdown histograms (5-Star to 1-Star star frequency) for single product details pages.
