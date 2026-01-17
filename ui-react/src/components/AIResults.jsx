import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatPrize } from '../utils/formatters';

export default function AIResults({ results, query }) {
    if (!results || results.length === 0) return null;

    return (
        <div className="mt-8 text-left">
            <div className="flex items-center gap-3 mb-4">
                <h3 className="text-lg font-semibold text-gray-900">AI Recommendations</h3>
                <span className="text-sm text-gray-500">For: "{query}"</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {results.slice(0, 4).map((result, index) => (
                    <a
                        key={result.id || index}
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block group"
                    >
                        <Card className="h-full hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                                <Badge variant="secondary" className="mb-2 bg-purple-100 text-purple-700 border-0">
                                    ✨ AI Match
                                </Badge>
                                <h4 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-2 mb-2">
                                    {result.title}
                                </h4>
                                {result.ai_reason && (
                                    <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                                        {result.ai_reason}
                                    </p>
                                )}
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    {result.prize_pool && (
                                        <span className="font-medium text-gray-700">{formatPrize(result.prize_pool)}</span>
                                    )}
                                    {result.source && (
                                        <span className="bg-gray-100 px-2 py-0.5 rounded">{result.source}</span>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </a>
                ))}
            </div>
        </div>
    );
}
