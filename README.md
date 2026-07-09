# Amazon Product Intelligence Scraper

A premium, monochromatic light-themed web dashboard that upgrades Amazon mobile scraping into a fully generic, real-world product intelligence tool. Users can scrape listing search results dynamically, inspect individual products to extract technical specification sheets, view visual price and review analytics, and export scraped datasets.

---

## What We Have Done (Upgrades & Features)

1. **Jupyter Notebook to Web App Migration**:
   - Migrated the raw BeautifulSoup notebook code into a structured, production-ready Python application.
   - Built a lightweight, concurrent local web server using **Flask**.

2. **Generic Keyword Scraper**:
   - Upgraded the scraper to search for **any** product keyword (e.g., *laptops*, *keyboards*, *headphones*), moving away from hardcoded mobile search configurations.
   - Supports selecting from multiple Amazon regional storefronts: India (`amazon.in`), United States (`amazon.com`), United Kingdom (`amazon.co.uk`), Germany (`amazon.de`), and Canada (`amazon.ca`).
   - Supports multi-page scrapers with dynamic progress indicators.

3. **Advanced Anti-Blocking Security Features**:
   - Integrated matched **Browser Profiles** combining matched user-agents and client-hint indicators (like `sec-ch-ua` and `sec-ch-ua-platform`) to prevent bot detection flags.
   - Integrated `requests.Session` cookie persistence with domain warm-ups.
   - Designed optional **Proxy Routing Integration** (compatible with ScraperAPI) to bypass Amazon's IP blocks and HTTP 503 errors when hosted live.

4. **Product Details & Spec Sheet Inspector**:
   - Paste any product URL or ASIN.
   - Extracts Brand name, Product Description Bullet points, High-Res Image, and a full mapping of the technical specification tables (e.g. RAM, Weight, Operating System, Manufacturer details).

5. **Monochromatic Light Web Interface**:
   - Designed a modern, minimalist white-and-black dashboard with left-sidebar navigation and multi-column grid panes.
   - Outputs a clean, 11-column data table that keeps data points (Image, ASIN, Title, Price, Rating, Reviews, Availability, Shipping, and Dates) isolated in separate cells.
   - Interactive collapsable operation progress logging screen.

6. **Multi-Format Data Exporter**:
   - Direct download of scraped datasets as **CSV**, **Excel (XLSX)**, or **JSON** files.

---

## How to Set Up and Run Locally

1. **Clone the Repository**:
   ```bash
   git clone <your-repository-url>
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
   Go to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Preparing for GitHub Upload

The repository is pre-configured with a [`.gitignore`](.gitignore) file. When you push this project to GitHub, Git will automatically ignore:
- The local virtual environment (`venv/` folder).
- Pycache and compiler metadata.
- Local spreadsheet datasets or test outputs (`*.csv`, `*.xlsx`, `*.json`).

Simply run the following Git commands in your terminal to push your repository:
```bash
git init
git add .
git commit -m "feat: upgrade Amazon Scraper with premium light UI, generic scraping, and proxy support"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

---

## Future Plans & Roadmap
- **Interactive Visual Analytics**: Integrate dynamic Chart.js libraries to display price range bar charts for keyword listing statistics and customer review rating breakdown histograms (5-Star to 1-Star star frequency) for single product details pages.
