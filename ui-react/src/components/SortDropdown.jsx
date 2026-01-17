import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

const SORT_OPTIONS = [
    { id: 'relevance', label: 'Relevance' },
    { id: 'prize', label: 'Prize' },
    { id: 'deadline', label: 'Deadline' },
    { id: 'participants', label: 'Participants' },
];

export default function SortDropdown({ currentSort, onSortChange }) {
    const currentLabel = SORT_OPTIONS.find(o => o.id === currentSort)?.label || 'Relevance';

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <span>Sort: {currentLabel}</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                        <path d="m6 9 6 6 6-6" />
                    </svg>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                {SORT_OPTIONS.map(option => (
                    <DropdownMenuItem
                        key={option.id}
                        className={currentSort === option.id ? 'bg-accent' : ''}
                        onClick={() => onSortChange(option.id)}
                    >
                        {option.label}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
