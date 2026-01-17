import { Skeleton } from '@/components/ui/skeleton';

export default function AIThinking({ isVisible, currentStep }) {
    if (!isVisible) return null;

    const steps = [
        'Understanding your query...',
        'Searching hackathons...',
        'Analyzing matches...',
        'Generating recommendations...',
    ];

    return (
        <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            {steps.map((step, index) => (
                <div
                    key={index}
                    className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm transition-all ${currentStep > index
                            ? 'bg-green-100 text-green-700'
                            : currentStep === index + 1
                                ? 'bg-purple-100 text-purple-700 animate-pulse'
                                : 'bg-gray-100 text-gray-400'
                        }`}
                >
                    {currentStep > index ? (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                    ) : currentStep === index + 1 ? (
                        <Skeleton className="w-4 h-4 rounded-full" />
                    ) : (
                        <span className="w-4 h-4 rounded-full border-2 border-gray-300" />
                    )}
                    {step}
                </div>
            ))}
        </div>
    );
}
