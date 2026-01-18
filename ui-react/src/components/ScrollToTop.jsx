import { Button } from '@/components/ui/button';

export default function ScrollToTop({ isVisible, onClick }) {
    if (!isVisible) return null;

    return (
        <Button
            variant="outline"
            size="icon"
            className="fixed bottom-6 right-6 z-50 rounded-full shadow-lg bg-gray-900 text-white border-0 hover:bg-gray-800"
            onClick={onClick}
            title="Scroll to top"
        >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
        </Button>
    );
}
