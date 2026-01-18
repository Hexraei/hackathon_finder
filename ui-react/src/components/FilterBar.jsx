import { useState, useEffect, useRef } from 'react';
import FilterPills from './FilterPills';
import SourcesDropdown from './SourcesDropdown';
import SortDropdown from './SortDropdown';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { debounce } from '../utils/formatters';

export default function FilterBar({
    currentFilter,
    onFilterChange,
    currentSort,
    onSortChange,
    searchQuery,
    onSearchChange,
    locationFilter,
    onLocationChange,
    allSources,
    selectedSources,
    onSourcesChange,
    totalCount,
    showStickyHeader,
}) {
    const [localSearch, setLocalSearch] = useState(searchQuery);
    const [localLocation, setLocalLocation] = useState(locationFilter);
    const debouncedSearch = useRef(debounce(onSearchChange, 300));
    const debouncedLocation = useRef(debounce(onLocationChange, 500));

    useEffect(() => {
        debouncedSearch.current(localSearch);
    }, [localSearch]);

    useEffect(() => {
        debouncedLocation.current(localLocation);
    }, [localLocation]);

    const handleNearby = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setLocalLocation('Near me');
                    onLocationChange('Near me');
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    alert('Could not get your location. Please enter it manually.');
                }
            );
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    };

    return (
        <section className="py-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Explore</h2>
            <div className={`max-w-7xl mx-auto px-6 ${showStickyHeader ? 'bg-white/90 backdrop-blur-md shadow-lg fixed top-16 left-0 right-0 z-40 py-4' : ''}`}>
                <div className="flex flex-col lg:flex-row gap-6">
                    {/* Left Column: Pills + Sources */}
                    <div className="flex flex-col gap-3 flex-shrink-0">
                        <FilterPills
                            currentFilter={currentFilter}
                            onFilterChange={onFilterChange}
                        />
                        <SourcesDropdown
                            allSources={allSources}
                            selectedSources={selectedSources}
                            onSourcesChange={onSourcesChange}
                        />
                    </div>

                    {/* Right Column: Search + Loc/Sort/Count */}
                    <div className="flex flex-col gap-3 flex-1">
                        {/* Row 1: Keyword Search */}
                        <div className="relative">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400">
                                <circle cx="11" cy="11" r="8" />
                                <path d="m21 21-4.35-4.35" />
                            </svg>
                            <Input
                                type="text"
                                placeholder="Search keywords..."
                                value={localSearch}
                                onChange={(e) => setLocalSearch(e.target.value)}
                                className="pl-10"
                            />
                        </div>

                        {/* Row 2: Location + Sort + Count */}
                        <div className="flex items-center gap-3 flex-wrap">
                            <div className="flex items-center gap-2">
                                <Input
                                    type="text"
                                    placeholder="Location..."
                                    value={localLocation}
                                    onChange={(e) => setLocalLocation(e.target.value)}
                                    className="w-40"
                                />
                                <Button
                                    variant="secondary"
                                    size="icon"
                                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                                    onClick={handleNearby}
                                    title="Use my location"
                                >
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                                        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
                                    </svg>
                                </Button>
                            </div>

                            <SortDropdown
                                currentSort={currentSort}
                                onSortChange={onSortChange}
                            />

                            <span className="text-sm text-gray-500">
                                {totalCount} hackathons
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
