import { IntelItem as IntelItemType } from '@/types';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

import { TAG_COLORS } from '@/lib/constants';

interface IntelItemProps {
    item: IntelItemType;
    onToggleFavorite: (id: string, current: boolean) => void;
    onSelect: (id: string, selected: boolean) => void;
    selected: boolean;
}

export function IntelItem({ item, onToggleFavorite, onSelect, selected }: IntelItemProps) {
    const navigate = useNavigate();

    return (
        <div className="flex gap-4 p-6 border-b border-gray-100 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors group">
            <div className="pt-1">
                <input
                    type="checkbox"
                    checked={selected}
                    onChange={(e) => onSelect(item.id, e.target.checked)}
                    className="w-5 h-5 rounded border-gray-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
            </div>
            
            <div className="flex-1 space-y-2">
                <div 
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Navigating to:', `/intel/${item.id}`);
                        navigate(`/intel/${item.id}`);
                    }}
                    className="block cursor-pointer"
                    role="link"
                    tabIndex={0}
                >
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight hover:text-blue-600 dark:hover:text-blue-400 transition-colors line-clamp-1" title={item.title}>
                        {item.title}
                    </h3>
                </div>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed line-clamp-2">
                    {item.summary}
                </p>
                <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500 mt-2">
                    <span>{item.source}</span>
                    <span>{item.time}</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                    {item.tags.map((tag, idx) => {
                        return (
                            <span
                                key={idx}
                                className={cn(
                                    "px-3 py-1 text-xs rounded-full font-medium whitespace-nowrap",
                                    TAG_COLORS[tag.color] || TAG_COLORS.gray
                                )}
                            >
                                {tag.label}
                            </span>
                        );
                    })}
                </div>
            </div>

            <div className="flex flex-col items-end gap-3 shrink-0">
                <button
                    onClick={() => onToggleFavorite(item.id, item.favorited)}
                    className={cn(
                        "px-4 py-1.5 rounded-full text-xs font-medium transition-colors",
                        item.favorited 
                            ? "bg-gray-200 dark:bg-slate-700 text-gray-500 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-slate-600" 
                            : "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50"
                    )}
                >
                    {item.favorited ? "已收藏" : "收藏"}
                </button>
            </div>
        </div>
    );
}
