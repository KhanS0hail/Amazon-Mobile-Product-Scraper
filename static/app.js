// State variables
let activeTab = 'search-tab';
let currentResults = [];


// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    setupTabSwitching();
    setupForms();
});

// Tab Navigation
function setupTabSwitching() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const panes = document.querySelectorAll('.tab-pane');
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    
    const tabMeta = {
        'search-tab': {
            title: 'Search Listings',
            subtitle: 'Extract search results, analyze product listings, and export custom datasets.'
        },
        'product-tab': {
            title: 'Inspect Product',
            subtitle: 'Retrieve deep technical specifications, bullet features, and images of any item.'
        }
    };
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            if (targetTab === activeTab || !tabMeta[targetTab]) return;
            
            // Toggle nav button active states
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Toggle pane visibility
            panes.forEach(pane => {
                pane.classList.remove('active');
                pane.id === targetTab ? pane.classList.add('active') : null;
            });
            
            activeTab = targetTab;
            
            // Update titles
            const meta = tabMeta[targetTab];
            if (titleEl) titleEl.textContent = meta.title;
            if (subtitleEl) subtitleEl.textContent = meta.subtitle;
        });
    });
}

// Forms Submission Setup
function setupForms() {
    // 1. Search Form
    document.getElementById('search-scraper-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const keyword = document.getElementById('search-keyword').value.trim();
        const domain = document.getElementById('amazon-domain').value;
        const pages = document.getElementById('scrape-pages').value;
        
        if (!keyword) return showToast('Please enter a keyword');
        startSearchScrapeStream(keyword, domain, pages);
    });

    // 2. Product Form
    document.getElementById('single-product-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const urlOrAsin = document.getElementById('product-url-asin').value.trim();
        const domain = document.getElementById('product-domain').value;
        
        if (!urlOrAsin) return showToast('Please enter a product link or ASIN');
        fetchProductDetails(urlOrAsin, domain);
    });
}

// Stream Scraper Logs
function startSearchScrapeStream(keyword, domain, pages) {
    const consoleOutput = document.getElementById('console-log-output');
    const consoleProgress = document.getElementById('console-progress');
    const startBtn = document.getElementById('btn-start-scrape');
    
    consoleOutput.innerHTML = '';
    consoleProgress.textContent = '0%';
    
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scraping...';
    
    const url = `/api/scrape/search/stream?keyword=${encodeURIComponent(keyword)}&domain=${encodeURIComponent(domain)}&pages=${pages}`;
    const eventSource = new EventSource(url);
    
    let lineCount = 0;
    
    eventSource.onmessage = (event) => {
        const message = event.data;
        lineCount++;
        
        const logLine = document.createElement('div');
        logLine.className = 'log-line';
        
        if (message.startsWith('[START]')) {
            logLine.style.color = '#000000';
            logLine.textContent = message.replace('[START]', '').trim();
            consoleProgress.textContent = '5%';
        } else if (message.startsWith('[COMPLETE]')) {
            logLine.style.color = '#000000';
            logLine.style.fontWeight = 'bold';
            logLine.textContent = message.replace('[COMPLETE]', '').trim();
            consoleProgress.textContent = '100%';
            
            eventSource.close();
            
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Scrape';
            
            showToast('Scraping completed successfully');
            fetchScrapeResults();
        } else if (message.startsWith('[ERROR]')) {
            logLine.style.color = '#000000';
            logLine.style.textDecoration = 'underline';
            logLine.textContent = message.replace('[ERROR]', '').trim();
            
            eventSource.close();
            
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Scrape';
            
            showToast('Scrape failed. Check logs.');
        } else {
            logLine.textContent = message.replace('[PROGRESS]', '').trim();
            let est = Math.min(95, 10 + Math.floor((lineCount / (pages * 4)) * 80));
            consoleProgress.textContent = `${est}%`;
        }
        
        consoleOutput.appendChild(logLine);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    };
    
    eventSource.onerror = () => {
        const errLine = document.createElement('div');
        errLine.textContent = 'Connection closed or interrupted.';
        consoleOutput.appendChild(errLine);
        
        eventSource.close();
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Scrape';
    };
}

// Fetch Results Data
function fetchScrapeResults() {
    fetch('/api/scrape/results')
        .then(response => response.json())
        .then(data => {
            currentResults = data.results || [];
            renderResultsTable(currentResults);
            
            const exportActions = document.getElementById('table-export-actions');
            exportActions.style.display = currentResults.length > 0 ? 'block' : 'none';
        })
        .catch(err => {
            console.error('Error fetching results:', err);
            showToast('Error loading results data');
        });
}

// Populate table rows
function renderResultsTable(items) {
    const tbody = document.getElementById('scraped-products-tbody');
    const countBadge = document.getElementById('results-count');
    
    countBadge.textContent = `${items.length} items`;
    
    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" class="empty-table-cell">
                    No products loaded yet. Run a search.
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    items.forEach(item => {
        let ratingText = '—';
        if (item['Rating Value'] !== null) {
            ratingText = `${item['Rating Value'].toFixed(1)} ★`;
        }
        
        const reviewsCount = item['Number of Reviews'] > 0 
            ? item['Number of Reviews'].toLocaleString() 
            : '0';

        const imgUrl = item['Image URL'] || 'https://via.placeholder.com/150?text=No+Image';
        const linkHtml = item['Product URL'] 
            ? `<a href="${item['Product URL']}" target="_blank" title="View Listing" style="display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border: 1px solid var(--border-color); border-radius: 6px;"><i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.8rem;"></i></a>`
            : '—';

        html += `
            <tr>
                <td>
                    <img class="table-product-img" src="${imgUrl}" alt="Thumb" onerror="this.src='https://via.placeholder.com/150?text=Error'">
                </td>
                <td style="font-family: monospace; font-size: 0.8rem;">${item['ASIN'] || '—'}</td>
                <td>
                    <div style="font-weight: 500; max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${item['Product Title']}">
                        ${item['Product Title']}
                    </div>
                </td>
                <td style="font-weight: 700;">${item['Price Display'] || '—'}</td>
                <td><span class="rating-pill">${ratingText}</span></td>
                <td>${reviewsCount}</td>
                <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${item['Availability'] || '—'}</span></td>
                <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${item['Delivery'] || '—'}</span></td>
                <td><span style="font-size: 0.8rem;">${item['Free Delivery Date'] || '—'}</span></td>
                <td><span style="font-size: 0.8rem; color: var(--text-muted);">${item['Fast Delivery Date'] || '—'}</span></td>
                <td style="text-align: center;">${linkHtml}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// Single Product details parser
function fetchProductDetails(urlOrAsin, domain) {
    const placeholder = document.getElementById('product-analyzer-placeholder');
    const resultArea = document.getElementById('single-product-result-area');
    const btn = document.getElementById('btn-analyze-product');
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Parsing...';
    
    placeholder.querySelector('p').textContent = 'Analyzing product page details. Please wait.';
    resultArea.style.display = 'none';

    fetch('/api/scrape/product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url_or_asin: urlOrAsin, domain: domain })
    })
    .then(response => {
        if (!response.ok) throw new Error('Request error');
        return response.json();
    })
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = 'Analyze Product';
        
        placeholder.style.display = 'none';
        resultArea.style.display = 'block';
        console.log("Scraped product data:", data);
        
        // Populate info
        document.getElementById('detail-product-image').src = data['Image URL'] || 'https://via.placeholder.com/300?text=No+Image';
        document.getElementById('detail-product-brand').textContent = data['Brand'] || 'PRODUCT';
        document.getElementById('detail-product-title').textContent = data['Title'] || 'No title';
        document.getElementById('detail-product-price').textContent = data['Price Display'] || '—';
        document.getElementById('detail-product-rating').textContent = data['Rating Value'] !== null 
            ? `${data['Rating Value'].toFixed(1)} ★` 
            : '—';
        document.getElementById('detail-product-reviews').textContent = data['Reviews Count'] !== null 
            ? data['Reviews Count'].toLocaleString() 
            : '0';
        document.getElementById('detail-product-availability').textContent = data['Availability'] || '—';
        document.getElementById('detail-product-link').href = data['Product URL'] || '#';
        
        // Populate bullets description
        const bulletsContainer = document.getElementById('detail-product-bullets');
        bulletsContainer.innerHTML = '';
        if (data['Bullet Points'] && data['Bullet Points'].length > 0) {
            data['Bullet Points'].forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                bulletsContainer.appendChild(li);
            });
        } else {
            bulletsContainer.innerHTML = '<li style="color:var(--text-muted)">No features listing details discovered for this product page.</li>';
        }
        
        // Populate specs
        const specsContainer = document.getElementById('detail-product-specs');
        specsContainer.innerHTML = '';
        const specsKeys = Object.keys(data['Specifications'] || {});
        if (specsKeys.length > 0) {
            specsKeys.forEach(key => {
                const item = document.createElement('div');
                item.className = 'spec-item';
                
                const label = document.createElement('span');
                label.className = 'spec-label';
                label.textContent = key;
                
                const val = document.createElement('span');
                val.className = 'spec-value';
                val.textContent = data['Specifications'][key];
                
                item.appendChild(label);
                item.appendChild(val);
                specsContainer.appendChild(item);
            });
        } else {
            specsContainer.innerHTML = '<div style="color:var(--text-muted); padding:1rem; font-size:0.85rem">No specs table found.</div>';
        }

        showToast('Analysis completed successfully');
    })
    .catch(err => {
        console.error(err);
        btn.disabled = false;
        btn.innerHTML = 'Analyze Product';
        
        placeholder.style.display = 'flex';
        placeholder.querySelector('p').textContent = 'Failed to analyze page. Amazon blocked the request or the link is invalid.';
        showToast('Extraction failed');
    });
}

// Download exports
function exportDataset(format) {
    if (currentResults.length === 0) return showToast('No dataset loaded');
    window.location.href = `/api/export?format=${format}`;
    showToast(`Downloading ${format.toUpperCase()}...`);
}

// Clean minimalist Toast Notification
function showToast(message) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    
    toastMsg.textContent = message;
    toast.className = 'toast-notification show';
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
