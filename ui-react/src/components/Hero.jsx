import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import AIThinking from './AIThinking';
import AIResults from './AIResults';

export default function Hero({ onSearch, isSearching, currentStep, results, query }) {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = (e) => {
        e?.preventDefault();
        if (inputValue.trim()) {
            onSearch(inputValue.trim());
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    };

    return (
        <section className="py-40 bg-gradient-to-b from-white to-gray-50">
            <div className="max-w-4xl mx-auto px-6 text-center">
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                    Find Your Next <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">Hackathon</span>
                </h1>
                <p className="text-lg text-gray-600 mb-8">
                    AI-powered search across <span className="font-semibold">12+</span> platforms. Real-time updates from Unstop, Devpost, Devfolio & more.
                </p>

                {/* AI Search Box */}
                <div className="relative max-w-2xl mx-auto">
                    <div className="flex gap-2 p-2 bg-white rounded-2xl shadow-lg border border-gray-200">
                        <Input
                            type="text"
                            placeholder="e.g., beginner friendly hackathons in India with prizes"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            className="flex-1 border-0 shadow-none focus-visible:ring-0 text-base"
                        />
                        <Button
                            onClick={handleSubmit}
                            disabled={isSearching}
                            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-6 rounded-xl"
                        >
                            Ask AI
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 ml-2">
                                <path d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                        </Button>
                    </div>
                </div>

                {/* AI Thinking Process */}
                <AIThinking isVisible={isSearching} currentStep={currentStep} />

                {/* AI Results */}
                <AIResults results={results} query={query} />
            </div>
        </section>
    );
}
