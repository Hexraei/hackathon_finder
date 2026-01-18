import HackathonCard from './HackathonCard';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

export default function HackathonGrid({
    hackathons,
    isLoading,
    hasMore,
    onLoadMore,
    isBookmarked,
    onBookmark,
    lastCardRef
}) {
    if (isLoading) {
        return (
            <section className="max-w-7xl mx-auto px-6 py-8">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="space-y-4 p-6 border rounded-xl">
                            <Skeleton className="h-12 w-12 rounded-xl" />
                            <Skeleton className="h-6 w-3/4" />
                            <Skeleton className="h-4 w-1/2" />
                            <Skeleton className="h-8 w-1/3" />
                            <Skeleton className="h-4 w-full" />
                        </div>
                    ))}
                </div>
            </section>
        );
    }

    if (!hackathons || hackathons.length === 0) {
        return (
            <section className="max-w-7xl mx-auto px-6 py-16">
                <div className="text-center">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-16 h-16 mx-auto text-gray-300 mb-4">
                        <circle cx="11" cy="11" r="8" />
                        <path d="m21 21-4.35-4.35" />
                    </svg>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No hackathons found</h3>
                    <p className="text-gray-500">Try adjusting your filters or search query.</p>
                </div>
            </section>
        );
    }

    return (
        <section className="max-w-7xl mx-auto px-6 py-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {hackathons.map((hackathon, index) => {
                    // Attach ref to last card for infinite scroll
                    const isLast = index === hackathons.length - 1;
                    return (
                        <div key={hackathon.id} ref={isLast ? lastCardRef : null}>
                            <HackathonCard
                                hackathon={hackathon}
                                isBookmarked={isBookmarked(hackathon.id)}
                                onBookmark={onBookmark}
                            />
                        </div>
                    );
                })}
            </div>

            {hasMore && (
                <div className="text-center mt-8">
                    <Button variant="outline" size="lg" onClick={onLoadMore} className="gap-2">
                        Load More
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                            <path d="M12 5v14M5 12l7 7 7-7" />
                        </svg>
                    </Button>
                </div>
            )}
        </section>
    );
}
