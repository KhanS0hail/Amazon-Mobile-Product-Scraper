# Technical Architecture & Implementation Methods

This document details the software architecture, technical stack, and data extraction methods utilized in the Amazon Product Intelligence Scraper.

---

## 1. Technical Stack

### Backend (Python Server Layer)
- **Framework**: `Flask` (v3.0.x) — Employed for its lightweight footprint and native support for server-side response generators, enabling log streaming.
- **Data Structure**: `pandas` (v2.x) — Utilized for in-memory tabulation of product items, data sanitization, and structured file conversions.
- **Excel Generation**: `openpyxl` — Middleware utilized to compile pandas DataFrames into binary Excel (`.xlsx`) files.
- **Production Web Server**: `gunicorn` — WSGI server configured to host the Flask application in cloud production environments.

### Frontend (User Interface Layer)
- **Structure**: Semantic `HTML5` elements.
- **Styles**: Custom Vanilla `CSS3` implementing a high-contrast monochromatic light-mode design. Key styling features include:
  - Responsive media query overrides for mobile, tablet, and desktop viewports.
  - Custom fluid scrollbars.
  - Monochromatic layout theme configurations.
- **Logic**: Vanilla `JavaScript` (ES6) controlling SPA tab switches, form handlers, asynchronous Fetch API calls, and Server-Sent Events logging listeners.
- **Iconography**: `FontAwesome` (via CDN) for icons.

---

## 2. Scraping Methods & Anti-Blocking Adaptations

Amazon utilizes automated request filters (e.g. CAPTCHAs, HTTP 503 limits) to block scrapers. The application implements several custom defenses:

### A. Persistent Sessions & Domain Warming
Rather than firing one-off raw HTTP calls, the scraper instantiates a `requests.Session()`.
1. The session is initialized with a specific browser profile.
2. The session fires a warming request to the base homepage domain (`amazon.com` or `amazon.in`).
3. This fetches initial validation cookies and tokens from Amazon, which are carried over to subsequent search and product requests, matching normal browser cookie streams.

### B. Aligned Browser Profiles (Client Hints)
Standard scraping libraries often rotate user-agent strings but send mismatched client browser parameters. This scraper maps matching **User-Agents** and **Client Hints** (`sec-ch-ua` and `sec-ch-ua-platform` headers) so that they align exactly (e.g. macOS user-agent strings match macOS client hints).

### C. Proxy Routing (ScraperAPI Integration)
For cloud server deployments, datacenter IPs are immediately blacklisted by Amazon.
- The scraper features a `fetch_url()` method that checks for the presence of a `SCRAPER_API_KEY` (or generic `PROXY_URL`) environment variable.
- If present, requests are routed through a residential proxy network, which automatically handles rotating IPs, headers, and CAPTCHA solving before returning the HTML.

---

## 3. Real-Time Streaming Logs (SSE)

To provide feedback to the user during long-running multi-page scrapes without blocking browser threads, the application uses **Server-Sent Events (SSE)**.
- **API Endpoint**: `/api/scrape/search/stream` returns a `Response` object with `mimetype='text/event-stream'`.
- The backend yields progress packets as they occur (`yield "data: Fetching Page 1\n\n"`).
- On the client side, JavaScript listens using `EventSource` and streams the log text line-by-line into the **Live Progress Logs** UI drawer.
