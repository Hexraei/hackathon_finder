import { Button } from '@/components/ui/button';

export default function Header({ activeNav = 'explore' }) {
    return (
        <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                <a href="/" className="flex items-center gap-2 text-gray-900 font-semibold text-lg hover:opacity-80 transition-opacity">
                    <svg className="w-8 h-6 text-gray-900" viewBox="0 0 265.61 193.96">
                        <path d="M0,0V193.96H88.81V109.6h87.98v84.36h88.81V0h-88.81V82.17H88.81V0H0Z" fill="currentColor" />
                    </svg>
                    <span>HackFind</span>
                </a>
                <nav className="flex items-center gap-1">
                    <Button
                        variant={activeNav === 'explore' ? 'default' : 'ghost'}
                        size="sm"
                        asChild
                    >
                        <a href="#">Explore</a>
                    </Button>
                    <Button
                        variant={activeNav === 'saved' ? 'default' : 'ghost'}
                        size="sm"
                        asChild
                    >
                        <a href="#">Saved</a>
                    </Button>
                    <Button
                        variant={activeNav === 'about' ? 'default' : 'ghost'}
                        size="sm"
                        asChild
                    >
                        <a href="#">About</a>
                    </Button>
                </nav>
            </div>
        </header>
    );
}
