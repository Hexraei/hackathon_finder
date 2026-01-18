import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatPrize, getLocation, calculateStatus } from '../utils/formatters';

// Source logo URLs
const SOURCE_LOGOS = {
    'Devpost': 'devpost.com',
    'Devfolio': 'devfolio.co',
    'Unstop': 'unstop.com',
    'MLH': 'mlh.io',
    'DoraHacks': 'dorahacks.io',
    'Kaggle': 'kaggle.com',
    'HackerEarth': 'hackerearth.com',
    'TechGig': 'techgig.com',
    'Superteam': 'superteam.fun',
    'HackQuest': 'hackquest.io',
    'DevDisplay': 'devdisplay.org',
    'HackCulture': 'hackculture.com',
    'MyCareerNet': 'mycareernet.in',
    'Lisk': 'lisk.com',
    'ETHGlobal': 'ethglobal.com',
    'Taikai': 'taikai.network',
    'Hack2Skill': 'hack2skill.com'
};

function renderSourceIcon(source) {
    if (!source) return '?';
    const domain = SOURCE_LOGOS[source];
    if (domain) {
        return (
            <img
                src={`https://www.google.com/s2/favicons?domain=${domain}&sz=64`}
                alt={source}
                className="w-8 h-8 rounded"
                onError={(e) => { e.target.outerHTML = source.charAt(0); }}
            />
        );
    }
    return <span className="text-lg font-bold text-gray-600">{source.charAt(0).toUpperCase()}</span>;
}

function formatMode(mode) {
    if (!mode) return 'Unknown';
    if (mode.toLowerCase() === 'in-person') return 'Offline';
    return mode.charAt(0).toUpperCase() + mode.slice(1);
}

function getModeColor(mode) {
    switch (mode?.toLowerCase()) {
        case 'online': return 'bg-green-100 text-green-700 border-green-200';
        case 'in-person':
        case 'offline': return 'bg-purple-100 text-purple-700 border-purple-200';
        case 'hybrid': return 'bg-blue-100 text-blue-700 border-blue-200';
        default: return 'bg-gray-100 text-gray-600 border-gray-200';
    }
}

export default function HackathonCard({ hackathon, isBookmarked, onBookmark }) {
    const h = hackathon;
    const location = getLocation(h.location);
    const status = calculateStatus(h);

    let mode = h.mode || 'unknown';
    const locLower = (location || '').toLowerCase();
    if (locLower === 'online' || locLower === 'virtual' || locLower === 'remote' || locLower.includes('online')) {
        mode = 'online';
    }

    const isLocationRedundant = mode === 'online' && ['online', 'virtual', 'remote'].includes(locLower);

    const dateObj = h.end_date ? new Date(h.end_date) : null;
    const month = dateObj ? dateObj.toLocaleDateString('en-US', { month: 'short' }).toUpperCase() : 'TBA';
    const day = dateObj ? dateObj.getDate() : '--';

    const prize = h.prize_pool;
    let prizeText = 'Prize TBD';
    let prizeStyle = 'text-gray-400 italic';

    if (prize) {
        const isMonetary = /^[\$€£¥₹][\d,]+/.test(prize);
        if (isMonetary) {
            prizeText = prize;
            prizeStyle = 'text-gray-800 font-bold';
        } else {
            const isZeroValue = prize.match(/^[\$€£¥₹]?0(\.0+)?$/);
            if (!isZeroValue) {
                prizeText = 'Non-Cash Prize';
                prizeStyle = 'text-gray-500';
            }
        }
    }

    const count = parseInt(h.participants_count || 0);
    const stats = [];

    if (status === 'upcoming' && count === 0) {
        stats.push({ icon: '⏳', text: 'Upcoming' });
    } else if (count > 0) {
        stats.push({ icon: '👥', text: count.toLocaleString() });
    }

    if (h.team_size_min || h.team_size_max) {
        let teamText;
        if (h.team_size_min && h.team_size_max) {
            teamText = h.team_size_min === h.team_size_max
                ? (h.team_size_max === 1 ? 'Solo' : `Team: ${h.team_size_max}`)
                : `Team: ${h.team_size_min}-${h.team_size_max}`;
        } else {
            const size = h.team_size_max || h.team_size_min;
            teamText = size === 1 ? 'Solo' : `Team: ${size}`;
        }
        stats.push({ icon: '👤', text: teamText });
    }

    const handleBookmarkClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        onBookmark(h.id);
    };

    const handleCardClick = () => {
        if (h.url) {
            window.open(h.url, '_blank');
        }
    };

    return (
        <Card
            className="p-4 gap-2 cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col"
            onClick={handleCardClick}
        >
            {/* Top Row: Source Icon + Date Badge */}
            <div className="flex items-start justify-between mb-3">
                <div className="w-12 h-12 rounded-xl border border-gray-200 flex items-center justify-center bg-white shadow-sm">
                    {renderSourceIcon(h.source)}
                </div>
                <div className="w-12 h-12 rounded-xl overflow-hidden shadow-sm border border-gray-200 flex flex-col">
                    <div className="bg-gray-900 text-white text-[8px] font-semibold text-center py-1">
                        {month}
                    </div>
                    <div className="bg-white text-gray-900 text-base font-bold flex-1 flex items-center justify-center">
                        {day}
                    </div>
                </div>
            </div>

            {/* Title */}
            <h3 className="font-bold text-lg text-gray-900 line-clamp-2 mb-1">
                {h.title || 'Untitled'}
            </h3>

            {/* AI Reason */}
            {h.ai_reason && (
                <p className="text-sm text-purple-600 bg-purple-50 p-2 rounded-lg mb-1">
                    ✨ {h.ai_reason}
                </p>
            )}

            {/* Mode Row */}
            <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className={`rounded-lg text-xs ${getModeColor(mode)}`}>
                    {formatMode(mode)}
                </Badge>
                {!isLocationRedundant && location && (
                    <span className="text-sm text-gray-500 truncate">{location}</span>
                )}
            </div>

            {/* Prize */}
            <div className={`text-2xl mb-1 ${prizeStyle}`}>
                {prizeText}
            </div>

            {/* Stats */}
            {stats.length > 0 && (
                <div className="flex items-center gap-4 mb-1 text-sm text-gray-600">
                    {stats.map((stat, i) => (
                        <span key={i} className="flex items-center gap-1">
                            <span>{stat.icon}</span>
                            {stat.text}
                        </span>
                    ))}
                </div>
            )}

            {/* Tags */}
            {h.tags && h.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-1">
                    {h.tags.slice(0, 3).map((tag, i) => (
                        <Badge key={i} variant="secondary" className="text-xs font-normal">
                            {tag}
                        </Badge>
                    ))}
                </div>
            )}

            {/* Spacer */}
            <div className="flex-1" />

            {/* Divider */}
            <div className="h-px bg-gray-200 mt-2 mb-3" />

            {/* Footer */}
            <div className="flex items-center gap-[5%]">
                <Button
                    variant="default"
                    size="sm"
                    className="w-[75%]"
                    onClick={(e) => {
                        e.stopPropagation();
                        if (h.url) window.open(h.url, '_blank');
                    }}
                >
                    View Details
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    className={`w-[20%] text-xl ${isBookmarked ? 'text-amber-500' : 'text-gray-400'} hover:text-amber-500`}
                    onClick={handleBookmarkClick}
                >
                    {isBookmarked ? '★' : '☆'}
                </Button>
            </div>
        </Card>
    );
}
