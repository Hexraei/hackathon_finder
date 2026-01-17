import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuCheckboxItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

export default function SourcesDropdown({ allSources, selectedSources, onSourcesChange }) {
    const handleSourceChange = (source, checked) => {
        const newSelected = new Set(selectedSources);
        if (checked) {
            newSelected.add(source);
        } else {
            newSelected.delete(source);
        }
        onSourcesChange(newSelected);
    };

    const selectAll = () => {
        onSourcesChange(new Set(allSources));
    };

    const clearAll = () => {
        onSourcesChange(new Set());
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                        <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" />
                    </svg>
                    <span>Sources</span>
                    <span className="text-muted-foreground">({selectedSources.size}/{allSources.length})</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                        <path d="m6 9 6 6 6-6" />
                    </svg>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56 max-h-80 overflow-y-auto">
                <div className="flex gap-2 p-2 border-b">
                    <Button variant="secondary" size="sm" className="flex-1" onClick={selectAll}>
                        All
                    </Button>
                    <Button variant="secondary" size="sm" className="flex-1" onClick={clearAll}>
                        Clear
                    </Button>
                </div>
                <DropdownMenuSeparator />
                {allSources.map(source => (
                    <DropdownMenuCheckboxItem
                        key={source}
                        checked={selectedSources.has(source)}
                        onCheckedChange={(checked) => handleSourceChange(source, checked)}
                    >
                        {source}
                    </DropdownMenuCheckboxItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
