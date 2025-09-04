// Custom JavaScript for OpenProject MCP documentation

document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize version selector
    initializeVersionSelector();
    
    // Initialize dark mode toggle
    initializeDarkMode();
    
    // Initialize table of contents
    initializeTableOfContents();
    
    // Initialize code highlighting
    initializeCodeHighlighting();
    
    // Initialize copy functionality
    initializeCopyFunctionality();
    
    // Initialize responsive navigation
    initializeResponsiveNavigation();
});

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            filterContent(query);
        });
    }
}

function filterContent(query) {
    const content = document.querySelectorAll('.md-content');
    content.forEach(section => {
        const text = section.textContent.toLowerCase();
        if (text.includes(query) || query === '') {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
}

// Version selector functionality
function initializeVersionSelector() {
    const versionSelect = document.querySelector('.md-version__list');
    if (versionSelect) {
        versionSelect.addEventListener('change', function(e) {
            const version = e.target.value;
            if (version) {
                window.location.href = `/${version}/`;
            }
        });
    }
}

// Dark mode toggle
function initializeDarkMode() {
    const darkModeToggle = document.querySelector('[data-md-component="palette"]');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function(e) {
            const isDarkMode = e.target.matches('[data-md-color-scheme="slate"]');
            localStorage.setItem('darkMode', isDarkMode);
        });
    }
    
    // Load saved preference
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    if (savedDarkMode) {
        document.documentElement.setAttribute('data-md-color-scheme', 'slate');
    }
}

// Table of contents functionality
function initializeTableOfContents() {
    const tocLinks = document.querySelectorAll('.md-nav__link');
    tocLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            tocLinks.forEach(l => l.classList.remove('md-nav__link--active'));
            // Add active class to clicked link
            link.classList.add('md-nav__link--active');
        });
    });
}

// Code highlighting
function initializeCodeHighlighting() {
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        // Add line numbers
        const lines = block.textContent.split('\n');
        const numberedLines = lines.map((line, index) => {
            return `<span class="line-number">${index + 1}</span>${line}`;
        }).join('\n');
        
        block.innerHTML = numberedLines;
        
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'md-clipboard';
        copyButton.title = 'Copy code';
        copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>';
        
        const pre = block.parentElement;
        pre.style.position = 'relative';
        pre.appendChild(copyButton);
        
        copyButton.addEventListener('click', function() {
            copyCode(block.textContent);
            showCopyFeedback(copyButton);
        });
    });
}

// Copy functionality
function initializeCopyFunctionality() {
    const copyButtons = document.querySelectorAll('.md-clipboard');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const codeBlock = button.parentElement.querySelector('code');
            if (codeBlock) {
                copyCode(codeBlock.textContent);
                showCopyFeedback(button);
            }
        });
    });
}

function copyCode(text) {
    navigator.clipboard.writeText(text).then(function() {
        console.log('Code copied to clipboard');
    }).catch(function(err) {
        console.error('Failed to copy code:', err);
    });
}

function showCopyFeedback(button) {
    const originalContent = button.innerHTML;
    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>';
    button.style.color = '#4caf50';
    
    setTimeout(() => {
        button.innerHTML = originalContent;
        button.style.color = '';
    }, 2000);
}

// Responsive navigation
function initializeResponsiveNavigation() {
    const navToggle = document.querySelector('.md-nav__toggle');
    const nav = document.querySelector('.md-nav');
    
    if (navToggle && nav) {
        navToggle.addEventListener('change', function() {
            if (navToggle.checked) {
                nav.classList.add('md-nav--expanded');
            } else {
                nav.classList.remove('md-nav--expanded');
            }
        });
    }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Table sorting functionality
function initializeTableSorting() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                sortTable(table, index);
            });
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to sort as numbers first
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return aNum - bNum;
        }
        
        // Sort as strings
        return aValue.localeCompare(bValue);
    });
    
    // Clear and re-append sorted rows
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
}

// Initialize table sorting when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTableSorting);

// Lazy loading for images
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
document.addEventListener('DOMContentLoaded', initializeLazyLoading);

// Print functionality
function initializePrintFunctionality() {
    const printButton = document.createElement('button');
    printButton.textContent = 'Print';
    printButton.className = 'md-print';
    printButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        background-color: #448aff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        z-index: 1000;
    `;
    
    printButton.addEventListener('click', () => {
        window.print();
    });
    
    document.body.appendChild(printButton);
}

// Initialize print functionality
document.addEventListener('DOMContentLoaded', initializePrintFunctionality);

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('[data-md-component="search-query"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Ctrl/Cmd + P to print
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
    
    // Escape to close modals or search
    if (e.key === 'Escape') {
        const searchOverlay = document.querySelector('[data-md-component="search"]');
        if (searchOverlay) {
            searchOverlay.setAttribute('data-md-toggle', 'false');
        }
    }
});

// Analytics tracking (if enabled)
function initializeAnalytics() {
    // Track page views
    if (typeof gtag !== 'undefined') {
        gtag('config', 'G-XXXXXXXXXX', {
            'page_path': window.location.pathname
        });
    }
    
    // Track outbound links
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        link.addEventListener('click', function(e) {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'click', {
                    'event_category': 'outbound',
                    'event_label': link.href
                });
            }
        });
    });
}

// Initialize analytics
document.addEventListener('DOMContentLoaded', initializeAnalytics);

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    
    // Send error to analytics if available
    if (typeof gtag !== 'undefined') {
        gtag('event', 'exception', {
            'description': e.error.message,
            'fatal': false
        });
    }
});

// Performance monitoring
function initializePerformanceMonitoring() {
    if ('performance' in window) {
        window.addEventListener('load', function() {
            const timing = performance.timing;
            const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
            
            console.log(`Page load time: ${pageLoadTime}ms`);
            
            // Send to analytics if available
            if (typeof gtag !== 'undefined') {
                gtag('event', 'timing_complete', {
                    'name': 'load',
                    'value': pageLoadTime,
                    'event_category': 'performance'
                });
            }
        });
    }
}

// Initialize performance monitoring
document.addEventListener('DOMContentLoaded', initializePerformanceMonitoring);

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for external use
window.mcpDocs = {
    search: filterContent,
    copyCode: copyCode,
    sortTable: sortTable,
    debounce: debounce,
    throttle: throttle
};