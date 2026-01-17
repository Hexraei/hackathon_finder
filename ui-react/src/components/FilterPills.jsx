import { Button } from '@/components/ui/button';

const FILTERS = [
    { id: 'all', label: 'All' },
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'live', label: 'Live Now' },
    { id: 'online', label: 'Online' },
    { id: 'in-person', label: 'Offline' },
];

export default function FilterPills({ currentFilter, onFilterChange }) {
    return (
        <div className="flex items-center gap-2 flex-wrap">
            {FILTERS.map(filter => (
                <Button
                    key={filter.id}
                    variant={currentFilter === filter.id ? 'default' : 'outline'}
                    size="sm"
                    className="rounded-full"
                    data-filter={filter.id}
                    onClick={() => onFilterChange(filter.id)}
                >
                    {filter.label}
                </Button>
            ))}
        </div>
    );
}
