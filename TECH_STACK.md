# Technical Architecture & Methods

This document details the software architecture, method integrations, and technical stack used to build the Amazon Product Intelligence Scraper.

---

## 1. Tech Stack Overview

### Backend (Python Server Layer)
- **Framework**: `Flask` (v3.0.x) — Chosen for its lightweight footprint and native support for server generators, enabling asynchronous logs streaming.
- **Data Structuring**: `pandas` (v2.x) — Utilized for in-memory tabulation of product items, data sanitization, and structured file conversions.
- **Excel Generation**: `openpyxl` — Middleware to compile pandas DataFrames into binary Excel (`.xlsx`) files.
- **Production Web Server**: `gunicorn` — WSGI server configured to run the Flask application in production environments (like Render).

### Frontend (User Interface Layer)
- **Structure**: Semantic `HTML5` elements.
- **Styles**: Custom Vanilla `CSS3` implementing a high-end monochromatic light-mode design. Key features include:
  - Responsive media query overrides for mobile, tablet, and desktop viewports.
  - Custom fluid scrollbars.
  - Monochromatic visual variables for fast theme adjustments.
- **Logic**: Vanilla `JavaScript` (ES6) controlling SPA tab switches, form handlers, asynchronous Fetch API polling, and Server-Sent Events logging listeners.
- **Iconography**: `FontAwesome` (via CDN) for icons.

---

## 2. Scraping Methods & Anti-Blocking Techniques

Amazon uses complex automated request filters (e.g. CAPTCHAs, HTTP 503 limits). The scraper implements several defense mechanisms:

### A. Persistent Sessions & Initial Warming
Instead of firing one-off raw HTTP calls, the backend instantiates a `requests.Session()`.
1. The session is first initialized with a browser profile.
2. The session fires a "warming request" to the base homepage domain (`amazon.com` or `amazon.in`).
3. This fetches initial validation cookies and tokens from Amazon, which are then carried over to paginated search and product calls, matching normal browser cookie streams.

### B. Aligned Browser Profiles (Client Hints)
Standard scraping libraries often rotate user-agent strings but send generic, mismatched browser parameters. This scraper maps matching **User-Agents** and **Client Hints** (`sec-ch-ua` and `sec-ch-ua-platform` headers) so that they align exactly (e.g. macOS user-agent matches macOS client hints).

### C. Proxy Routing (ScraperAPI Integration)
For cloud server deployments, datacenter IPs are immediately blacklisted by Amazon.
- The scraper features a `fetch_url()` method that checks for the presence of a `SCRAPER_API_KEY` (or generic `PROXY_URL`) environment variable.
- If present, it routes calls through a residential proxy network, which automatically handles rotating IPs, headers, and CAPTCHA solving before returning clean HTML back to our server.

---

## 3. Real-Time Streaming Logs (SSE)

To provide feedback to the user during long-running multi-page scrapes without blocking browser threads, we use **Server-Sent Events (SSE)**.
- **API Endpoint**: `/api/scrape/search/stream` returns a `Response` object with `mimetype='text/event-stream'`.
- The backend yields progress packets as they occur (`yield "data: Fetching Page 1\n\n"`).
- On the client side, JavaScript listens using `EventSource` and streams the log text line-by-line into the **Live Progress Logs** UI drawer.
