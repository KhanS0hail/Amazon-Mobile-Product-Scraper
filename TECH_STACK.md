# Technical Stack & Architecture

A brief summary of the technologies and data extraction methods used in the Amazon Product Intelligence Scraper.

---

## 1. Core Stack

### Backend
- **Python / Flask**: Runs the server, routing search queries, product analysis, logs, and downloads.
- **Gunicorn**: Web server mapping configuration used for cloud host environments.
- **Pandas & OpenPyXL**: Manages in-memory data structures and exports CSV, Excel, and JSON files.

### Frontend
- **HTML5 & CSS3**: Minimalist monochromatic styling using flex/grid structures.
- **Vanilla JavaScript**: Controls active tabs, form submits, fetch operations, and logging outputs.
- **FontAwesome**: UI iconography assets.

---

## 2. Data Scraping & Bypass Operations
- **Session Persistence**: Utilizes `requests.Session()` with warmed-up domain cookies to match browser behavior.
- **Header Alignment**: Pairs specific User-Agents with corresponding Client Hints to pass bot checks.
- **Proxy Routing**: Supports routing requests through residential proxy providers (via the `SCRAPER_API_KEY` or `PROXY_URL` environment variables).

---

## 3. Real-Time Logger
- **Server-Sent Events (SSE)**: Streams progress lines directly from Python's background scraper to the frontend progress window using a `/api/scrape/search/stream` connection.
