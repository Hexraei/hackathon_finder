/**
 * HackFind - Frontend Application
 * ================================
 * - Clean card design
 * - Infinite scroll (loads 100 at a time)
 * - All hackathons from database
 */

const API_BASE = '/api';
const ITEMS_PER_LOAD = 100;
let isLoadingMore = false;

let state = {
    hackathons: [],
    filteredHackathons: [],
    displayedCount: 0,
    currentFilter: 'all',
    currentSort: 'latest',
    searchQuery: '',
    isLoading: true,
    bookmarks: new Set(JSON.parse(localStorage.getItem('bookmarks') || '[]'))
};

const elements = {
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    sortBtn: document.getElementById('sortBtn'),
    sortMenu: document.getElementById('sortMenu'),
    bentoGrid: document.getElementById('bentoGrid'),
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    resultsCount: document.getElementById('resultsCount'),
    filterPills: document.querySelectorAll('.filter-pill'),
    sortOptions: document.querySelectorAll('.sort-option'),
    sortDropdown: document.querySelector('.sort-dropdown')
};

// === Init ===
document.addEventListener('DOMContentLoaded', init);

async function init() {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/hackathons`);
        if (response.ok) {
            state.hackathons = await response.json();
            console.log(`Loaded ${state.hackathons.length} hackathons from API`);
        } else {
            throw new Error('API failed');
        }
    } catch (error) {
        console.log('API not available, no data to show');
        state.hackathons = [];
    }

    applyFiltersAndSort();
    bindEvents();
    initPlaceholderAnimation();

    setTimeout(() => {
        showLoading(false);
        renderHackathons();
    }, 500);
}

function bindEvents() {
    elements.searchInput?.addEventListener('input', debounce(handleSearch, 300));
    elements.searchBtn?.addEventListener('click', handleSearch);
    elements.searchInput?.addEventListener('keypress', e => { if (e.key === 'Enter') handleSearch(); });

    elements.filterPills.forEach(pill => pill.addEventListener('click', () => handleFilterChange(pill)));

    elements.sortBtn?.addEventListener('click', toggleSortMenu);
    elements.sortOptions.forEach(opt => opt.addEventListener('click', () => handleSortChange(opt)));

    document.addEventListener('click', e => {
        if (!elements.sortDropdown?.contains(e.target)) {
            elements.sortDropdown?.classList.remove('open');
        }
    });

    // Infinite scroll
    window.addEventListener('scroll', debounce(handleScroll, 100));
}

function handleScroll() {
    if (isLoadingMore) return;

    const scrollY = window.scrollY;
    const windowHeight = window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;

    // Load more when 300px from bottom
    if (scrollY + windowHeight >= docHeight - 300) {
        const remaining = state.filteredHackathons.length - state.displayedCount;
        if (remaining > 0) {
            isLoadingMore = true;
            renderHackathons(true);
            isLoadingMore = false;
        }
    }
}

// === Filtering & Sorting ===
function calculateStatus(hackathon) {
    /**
     * Calculate hackathon status based on current date (client-side)
     * This ensures filters work correctly without database updates
     */
    if (!hackathon.start_date) {
        return 'unknown';
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset to start of day for accurate comparison

    try {
        const startDate = new Date(hackathon.start_date);
        const endDate = hackathon.end_date ? new Date(hackathon.end_date) : startDate;

        if (today < startDate) {
            return 'upcoming';
        } else if (today >= startDate && today <= endDate) {
            return 'ongoing';
        } else {
            return 'ended';
        }
    } catch (e) {
        return 'unknown';
    }
}

function applyFiltersAndSort() {
    let filtered = [...state.hackathons];

    if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filtered = filtered.filter(h =>
            (h.title || '').toLowerCase().includes(q) ||
            (h.description || '').toLowerCase().includes(q) ||
            (h.location || '').toLowerCase().includes(q) ||
            (h.source || '').toLowerCase().includes(q) ||
            (h.tags || []).some(t => t.toLowerCase().includes(q))
        );
    }

    // Apply filters with client-side status calculation
    switch (state.currentFilter) {
        case 'upcoming':
            filtered = filtered.filter(h => calculateStatus(h) === 'upcoming');
            break;
        case 'ongoing':
            filtered = filtered.filter(h => calculateStatus(h) === 'ongoing');
            break;
        case 'online':
            filtered = filtered.filter(h => {
                const mode = (h.mode || '').toLowerCase();
                return mode === 'online' || mode.includes('online');
            });
            break;
        case 'in-person':
            filtered = filtered.filter(h => {
                const mode = (h.mode || '').toLowerCase();
                return mode === 'in-person' || mode.includes('in-person') || mode.includes('in person');
            });
            break;
    }

    switch (state.currentSort) {
        case 'latest': filtered.sort((a, b) => new Date(b.start_date || 0) - new Date(a.start_date || 0)); break;
        case 'deadline': filtered.sort((a, b) => new Date(a.start_date || 0) - new Date(b.start_date || 0)); break;
        case 'prize': filtered.sort((a, b) => (b.prize_pool_numeric || 0) - (a.prize_pool_numeric || 0)); break;
        case 'title': filtered.sort((a, b) => (a.title || '').localeCompare(b.title || '')); break;
    }

    state.filteredHackathons = filtered;
    state.displayedCount = 0;
    updateResultsCount();
}

function handleSearch() {
    state.searchQuery = elements.searchInput?.value.trim() || '';
    applyFiltersAndSort();
    renderHackathons();
}

function handleFilterChange(pill) {
    elements.filterPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    state.currentFilter = pill.dataset.filter;

    console.log(`Filter changed to: ${state.currentFilter}`);
    console.log(`Total hackathons before filter: ${state.hackathons.length}`);

    applyFiltersAndSort();

    console.log(`Filtered hackathons: ${state.filteredHackathons.length}`);
    if (state.currentFilter === 'in-person') {
        console.log('In-person filter samples:', state.filteredHackathons.slice(0, 5).map(h => ({
            title: h.title,
            mode: h.mode
        })));
    }

    renderHackathons();
}

function handleSortChange(opt) {
    elements.sortOptions.forEach(o => o.classList.remove('active'));
    opt.classList.add('active');
    state.currentSort = opt.dataset.sort;
    elements.sortBtn.querySelector('span').textContent = `Sort: ${opt.textContent}`;
    elements.sortDropdown?.classList.remove('open');
    applyFiltersAndSort();
    renderHackathons();
}

function toggleSortMenu(e) {
    e.stopPropagation();
    elements.sortDropdown?.classList.toggle('open');
}

function toggleBookmark(e, id) {
    e.stopPropagation();
    const btn = e.currentTarget;
    if (state.bookmarks.has(id)) {
        state.bookmarks.delete(id);
        btn.classList.remove('active');
    } else {
        state.bookmarks.add(id);
        btn.classList.add('active');
    }
    localStorage.setItem('bookmarks', JSON.stringify([...state.bookmarks]));
}

// === Rendering ===
function renderHackathons(append = false) {
    if (!append) {
        state.displayedCount = 0;
        elements.bentoGrid.innerHTML = '';
    }

    const items = state.filteredHackathons.slice(state.displayedCount, state.displayedCount + ITEMS_PER_LOAD);

    if (items.length === 0 && state.displayedCount === 0) {
        elements.emptyState?.classList.remove('hidden');
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }

    elements.emptyState?.classList.add('hidden');

    const html = items.map(h => createCard(h)).join('');
    elements.bentoGrid.insertAdjacentHTML('beforeend', html);

    state.displayedCount += items.length;

    // Bind new card events
    document.querySelectorAll('.bento-card:not([data-bound])').forEach(card => {
        card.dataset.bound = 'true';
        const url = card.dataset.url;
        card.onclick = e => {
            // Open URL when clicking anywhere on the card
            if (url && url.startsWith('http')) window.open(url, '_blank', 'noopener');
        };
    });

    renderLoadMore();
}


function renderLoadMore() {
    const container = document.getElementById('paginationContainer');
    const remaining = state.filteredHackathons.length - state.displayedCount;

    if (remaining > 0) {
        container.style.display = 'flex';
        container.innerHTML = `
            <div class="scroll-indicator">
                <span class="loading-spinner"></span>
                Showing ${state.displayedCount} of ${state.filteredHackathons.length} • Scroll for more
            </div>
        `;
    } else {
        container.style.display = state.displayedCount > 0 ? 'flex' : 'none';
        container.innerHTML = state.displayedCount > 0 ? `<span class="all-loaded">All ${state.displayedCount} hackathons loaded</span>` : '';
    }
}

function loadMore() {
    renderHackathons(true);
}

function createCard(h) {
    const location = getLocation(h.location);

    // Determine mode
    let mode = h.mode || 'unknown';
    const locLower = location.toLowerCase();
    if (locLower === 'online' || locLower === 'virtual' || locLower === 'remote' || locLower.includes('online')) {
        mode = 'online';
    }

    // Format date for badge
    const dateInfo = formatDateForBadge(h.start_date);

    // Format prize
    const prize = h.prize_pool ? `Prize : ${h.prize_pool}` : 'Prize : TBA';

    // SVG icon paths (green hands/heart logo)
    const iconSvg = `
        <svg class="icon-svg" fill="none" viewBox="0 0 50.9987 41.6114">
            <g>
                <path d="M22.8503 41.213H14.7729C14.7497 40.3069 14.5877 38.9711 13.7854 37.7213C11.7101 34.4795 7.71382 35.495 4.23444 32.0345C2.51404 30.3315 1.71171 28.1365 1.48026 27.5272C0.878507 25.9805 0.631634 24.6057 0.531341 23.6214C-0.132131 20.6296 -0.0395536 18.5752 0.0993127 17.4113C0.176461 16.7863 0.307612 16.1145 0.78593 15.8802C1.61913 15.474 2.86893 16.7004 2.95379 16.7785C3.10808 18.5283 3.41668 20.5437 4.003 22.7309C4.31931 23.9105 4.6819 24.9963 5.05221 25.9883C4.73591 23.6527 4.4196 21.3092 4.10329 18.9736C4.18816 18.8642 4.3656 18.6924 4.6279 18.6377C5.05993 18.5596 5.56139 18.872 5.80826 19.4344C5.91627 20.1844 6.086 21.2623 6.33287 22.5591C6.74175 24.7229 6.94234 25.8009 7.28179 26.5508C7.67524 27.41 8.66274 29.0192 11.4709 30.2378L13.6851 30.5346C13.3996 30.3315 8.87875 27.0819 8.66274 25.2462C8.63188 24.9885 8.57016 24.4495 8.89418 24.0198C9.24906 23.5511 9.8431 23.473 10.0437 23.4574C10.5606 23.9183 11.4478 24.676 12.6359 25.4884C15.5752 27.496 17.2185 27.7069 19.2012 29.6441C20.3044 30.7221 20.9216 31.7611 21.207 32.2376C23.2051 35.6434 23.0817 39.2914 22.8503 41.213Z" fill="#70C496"/>
                <path d="M28.1503 41.6114H36.2277C36.2508 40.7053 36.4128 39.3695 37.2152 38.1196C39.2905 34.8779 43.2867 35.8934 46.7661 32.4328C48.4865 30.7299 49.2888 28.5349 49.5203 27.9256C50.122 26.3789 50.3689 25.0041 50.4692 24.0198C51.1327 21.0202 51.0401 18.9736 50.8935 17.8018C50.8164 17.1769 50.6852 16.5051 50.2069 16.2708C49.3737 15.8646 48.1239 17.091 48.039 17.1691C47.8847 18.9189 47.5761 20.9343 46.9898 23.1215C46.6735 24.301 46.3109 25.3868 45.9406 26.3789C46.2569 24.0433 46.5732 21.6998 46.8895 19.3641C46.8047 19.2548 46.6272 19.0829 46.3649 19.0283C45.9329 18.9501 45.4314 19.2626 45.1846 19.825C45.0766 20.5749 44.9068 21.6529 44.66 22.9496C44.2511 25.1134 44.0505 26.1914 43.711 26.9413C43.3176 27.8006 42.3301 29.4098 39.5219 30.6284L37.3077 30.9252C37.5932 30.7221 42.1141 27.4725 42.3301 25.6368C42.3609 25.379 42.4227 24.84 42.0986 24.4104C41.7438 23.9417 41.1497 23.8636 40.9491 23.848C40.4322 24.3088 39.545 25.0666 38.357 25.879C35.4176 27.8865 33.7744 28.0974 31.7917 30.0347C30.6884 31.1127 30.0713 32.1516 29.7858 32.6281C27.7877 36.034 27.9111 39.682 28.1426 41.6036L28.1503 41.6114Z" fill="#70C496"/>
                <path d="M39.3908 10.3652C39.0668 12.1306 37.385 13.9507 35.9423 15.5755C33.1573 18.6142 28.4512 22.5746 26.0674 24.2463C25.9285 24.3401 25.7588 24.4494 25.589 24.3479C21.9322 21.6607 12.8056 14.4038 12.0496 10.0996C11.2241 4.60811 15.691 -2.13325 21.8937 0.647657C23.2746 1.20228 24.5244 2.31151 25.5273 3.42075C25.5813 3.43638 25.6893 3.47543 25.7356 3.49887C26.2448 3.34264 26.8003 2.39744 27.3326 2.06155C33.867 -3.40653 40.4786 3.06923 39.3985 10.2949V10.3652H39.3908Z" fill="#70C496"/>
            </g>
        </svg>
    `;

    return `
        <article class="bento-card" data-url="${h.url || '#'}">
            <!-- Refer Website Button -->
            <div class="absolute refer-btn-bg"></div>
            <div class="absolute refer-highlight-1"></div>
            <div class="absolute refer-highlight-2"></div>
            <p class="absolute refer-text">Refer Website</p>

            <!-- Divider -->
            <div class="divider-container">
                <div class="divider-line"></div>
            </div>

            <!-- Icon -->
            <div class="absolute icon-bg"></div>
            ${iconSvg}

            <!-- Text -->
            <p class="absolute text-prize">${prize}</p>
            <p class="absolute text-location">${location}</p>
            <p class="absolute text-title">${h.title || 'Untitled Hackathon'}</p>

            <!-- Mode Button -->
            <div class="absolute mode-btn">
                <span class="mode-btn-text">${capitalize(mode)}</span>
            </div>

            <!-- Date Badge -->
            <div class="absolute date-circle-black"></div>
            <div class="absolute date-block-white"></div>
            <p class="absolute date-month">${dateInfo.month}</p>
            <p class="absolute date-day">${dateInfo.day}</p>
        </article>
    `;
}

// Helper function to format date for the badge
function formatDateForBadge(dateStr) {
    if (!dateStr) {
        return { month: 'TBA', day: '--' };
    }

    try {
        const date = new Date(dateStr);
        const month = date.toLocaleDateString('en-US', { month: 'short' }).toUpperCase();
        const day = date.getDate();
        return { month, day };
    } catch (e) {
        return { month: 'TBA', day: '--' };
    }
}

function getLocation(loc) {
    if (!loc) return 'TBA';

    // If it's already a clean string
    if (typeof loc === 'string') {
        // Check if it's a stringified dict like "{'icon': 'globe', 'location': 'Online'}"
        if (loc.includes("'location':") || loc.includes('"location":')) {
            // Extract the location value using regex
            const match = loc.match(/['"]location['"]\s*:\s*['"]([^'"]+)['"]/);
            if (match) return match[1];
        }
        // Check for other patterns
        if (loc.includes("'name':") || loc.includes('"name":')) {
            const match = loc.match(/['"]name['"]\s*:\s*['"]([^'"]+)['"]/);
            if (match) return match[1];
        }
        // If it starts with { it's probably a stringified object
        if (loc.startsWith('{')) {
            // Try to extract any meaningful location-like value
            const match = loc.match(/['"]([^'"]+)['"](?:\s*}|\s*,\s*['"]icon)/);
            if (match && match[1] !== 'globe' && match[1] !== 'location') return match[1];
        }
        return loc;
    }

    // If it's an actual object
    if (typeof loc === 'object') {
        if (loc.location) return loc.location;
        if (loc.name) return loc.name;
        if (loc.city) return loc.city;
        const values = Object.values(loc).filter(v => typeof v === 'string' && v.length > 1);
        return values[0] || 'TBA';
    }

    return String(loc);
}

// === Helpers ===
function showLoading(show) {
    state.isLoading = show;
    if (elements.loadingState) elements.loadingState.style.display = show ? 'block' : 'none';
    if (elements.bentoGrid) elements.bentoGrid.style.display = show ? 'none' : 'grid';
}

function updateResultsCount() {
    if (elements.resultsCount) {
        elements.resultsCount.textContent = `${state.filteredHackathons.length} hackathons`;
    }
}

function formatDate(d) {
    if (!d) return 'TBA';
    try {
        return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return 'TBA'; }
}

function formatDateRange(startDate, endDate) {
    if (!startDate) return 'TBA';

    const start = formatDate(startDate);

    if (!endDate || endDate === startDate) {
        return start;
    }

    const end = formatDate(endDate);
    return `${start} - ${end}`;
}

function formatPrize(prizePool) {
    if (!prizePool) return null;

    const prizeStr = String(prizePool).trim();

    // If it already has a currency symbol, return as is
    if (/^[\$€£¥₹]/.test(prizeStr) || /USD|EUR|INR|GBP/.test(prizeStr)) {
        return prizeStr;
    }

    // If it's just a number, add $ symbol
    if (/^[\d,]+$/.test(prizeStr)) {
        return `$${prizeStr}`;
    }

    // Otherwise return as is
    return prizeStr;
}

function capitalize(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

function debounce(fn, wait) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

function resetFilters() {
    state.currentFilter = 'all';
    state.searchQuery = '';
    if (elements.searchInput) elements.searchInput.value = '';
    elements.filterPills.forEach(p => p.classList.toggle('active', p.dataset.filter === 'all'));
    applyFiltersAndSort();
    renderHackathons();
}

window.loadMore = loadMore;
window.resetFilters = resetFilters;

// === Dynamic Placeholder Animation ===
function initPlaceholderAnimation() {
    const searchInput = elements.searchInput;
    if (!searchInput) return;

    const placeholders = [
        'Search for AI hackathons...',
        'Find Web3 competitions...',
        'Discover hackathons in India...',
        'Look for blockchain events...',
        'Search machine learning challenges...',
        'Find gaming hackathons...',
        'Explore climate tech events...',
        'Discover fintech competitions...',
        'Search for beginner-friendly hackathons...',
        'Find hackathons with prizes...'
    ];

    let currentIndex = 0;
    let currentText = '';
    let isDeleting = false;
    let typingSpeed = 80;

    function animatePlaceholder() {
        // Don't animate if user is typing
        if (document.activeElement === searchInput && searchInput.value !== '') {
            setTimeout(animatePlaceholder, 1000);
            return;
        }

        const fullText = placeholders[currentIndex];

        if (isDeleting) {
            currentText = fullText.substring(0, currentText.length - 1);
            typingSpeed = 15;
        } else {
            currentText = fullText.substring(0, currentText.length + 1);
            typingSpeed = 80;
        }

        searchInput.placeholder = currentText;

        if (!isDeleting && currentText === fullText) {
            // Pause at end of word
            typingSpeed = 2000;
            isDeleting = true;
        } else if (isDeleting && currentText === '') {
            isDeleting = false;
            currentIndex = (currentIndex + 1) % placeholders.length;
            typingSpeed = 500;
        }

        setTimeout(animatePlaceholder, typingSpeed);
    }

    // Start animation
    animatePlaceholder();
}
