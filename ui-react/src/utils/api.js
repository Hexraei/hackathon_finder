// API Configuration
// In production (Netlify), set VITE_API_URL environment variable
// In development, falls back to localhost
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

console.log('[API] Base URL:', API_BASE);
console.log('[API] Environment:', import.meta.env.MODE);

// Fetch all hackathons with pagination (backend limits to 200 per page)
export async function fetchHackathons(params = {}) {
    const pageSize = 200; // Backend max
    let allEvents = [];
    let page = 1;
    let hasMore = true;

    console.log('[API] fetchHackathons called with params:', params);

    while (hasMore) {
        const searchParams = new URLSearchParams({
            page: page,
            page_size: pageSize,
            sort_by: params.sortBy || 'prize',
        });

        const url = `${API_BASE}/hackathons?${searchParams}`;
        console.log(`[API] Fetching page ${page}:`, url);

        try {
            const response = await fetch(url);
            console.log(`[API] Response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[API] Error response body:', errorText);
                throw new Error(`Failed to fetch hackathons: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Page ${page} returned ${data.events?.length || 0} events, total: ${data.total}`);

            const events = data.events || [];
            allEvents = allEvents.concat(events);

            // Check if there are more pages
            if (events.length < pageSize || allEvents.length >= (data.total || 0)) {
                hasMore = false;
            } else {
                page++;
            }
        } catch (error) {
            console.error('[API] Fetch error:', error.message);
            console.error('[API] Full error:', error);
            throw error;
        }
    }

    console.log(`[API] Total events fetched: ${allEvents.length}`);
    return { events: allEvents, total: allEvents.length };
}

// Fetch available sources
export async function fetchSources() {
    const url = `${API_BASE}/sources`;
    console.log('[API] Fetching sources:', url);

    try {
        const response = await fetch(url);
        console.log(`[API] Sources response: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[API] Sources error:', errorText);
            throw new Error('Failed to fetch sources');
        }
        return response.json();
    } catch (error) {
        console.error('[API] Sources fetch error:', error);
        throw error;
    }
}

// AI Search
export async function aiSearch(query) {
    const url = `${API_BASE}/search/ai?q=${encodeURIComponent(query)}`;
    console.log('[API] AI Search:', url);

    try {
        const response = await fetch(url);
        console.log(`[API] AI Search response: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[API] AI Search error:', errorText);
            throw new Error('AI search failed');
        }
        return response.json();
    } catch (error) {
        console.error('[API] AI Search fetch error:', error);
        throw error;
    }
}
