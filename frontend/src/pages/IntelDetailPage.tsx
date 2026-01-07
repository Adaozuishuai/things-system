import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getIntelDetail, toggleFavorite, exportIntel } from '@/api';
import { IntelItem as IntelItemType } from '@/types';
import { cn, isCountry } from '@/lib/utils';
import { ArrowLeft } from 'lucide-react';

export function IntelDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [item, setItem] = useState<IntelItemType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) {
            setLoading(true);
            getIntelDetail(id)
                .then(setItem)
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [id]);

    const handleToggleFavorite = async () => {
        if (!item) return;
        try {
            await toggleFavorite(item.id, !item.favorited);
            setItem(prev => prev ? { ...prev, favorited: !prev.favorited } : null);
        } catch (error) {
            console.error('Failed to toggle favorite:', error);
        }
    };

    const handleExport = async () => {
        if (!item) return;
        try {
            const blob = await exportIntel([item.id], "all", "all", "");
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Clean filename title
            const safeTitle = item.title.replace(/[\\/:*?"<>|]/g, "");
            a.download = `${safeTitle}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Failed to export:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!item) {
        return <div className="p-8 text-center text-gray-500 dark:text-gray-400">情报未找到</div>;
    }

    const tagColors: Record<string, string> = {
        purple: "bg-purple-600 text-white",
        blue: "bg-blue-600 text-white",
        gray: "bg-gray-400 text-white",
    };

    return (
        <div className="flex-1 flex flex-col h-full bg-gray-50/50 dark:bg-slate-900 p-4 md:p-6 overflow-hidden">
            {/* Header Actions (Floating Top Right) */}
            <div className="w-full mx-auto flex justify-end gap-3 mb-4 shrink-0">
                <button
                    onClick={handleExport}
                    className="flex items-center gap-2 px-5 py-1.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors shadow-sm font-medium text-sm"
                >
                    <span>导出</span>
                </button>
                <button
                    onClick={handleToggleFavorite}
                    className={cn(
                        "flex items-center gap-2 px-5 py-1.5 rounded-full transition-colors shadow-sm border font-medium text-sm",
                        item.favorited
                            ? "bg-yellow-500 text-white border-yellow-500 hover:bg-yellow-600"
                            : "bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-200 border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700"
                    )}
                >
                    <span>{item.favorited ? "已收藏" : "收藏"}</span>
                </button>
            </div>

            {/* Main Content Card */}
            <div className="w-full mx-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 md:p-8 space-y-8 flex-1 overflow-y-auto">
                
                {/* 1. Tags Section */}
                <div className="space-y-5">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">拟投栏目</h3>
                    <div className="flex flex-wrap gap-2">
                        {item.tags.map((tag, index) => {
                            const isCountryTag = isCountry(tag.label) || tag.color === 'red';
                            return (
                                <span
                                    key={index}
                                    className={cn(
                                        "px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide text-white",
                                        isCountryTag 
                                            ? "bg-red-600" 
                                            : (tagColors[tag.color] || tagColors.purple)
                                    )}
                                >
                                    {tag.label}
                                </span>
                            );
                        })}
                    </div>
                </div>

                {/* 2. Time & Value Point Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Time */}
                    <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-5 space-y-2">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">事件时间</h3>
                        <p className="text-xl font-medium text-gray-900 dark:text-gray-200">{item.time.split(' ')[0]}</p>
                    </div>
                    {/* Value Point */}
                    <div className="md:col-span-2 bg-gray-50 dark:bg-slate-700/50 rounded-lg p-5 space-y-2">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">价值点</h3>
                        <p className="text-base text-gray-800 dark:text-gray-300 leading-relaxed">
                            {item.summary}
                        </p>
                    </div>
                </div>

                {/* 3. Title & Body Section */}
                <div className="space-y-4 pt-2">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">标题</h3>
                    <div className="space-y-4">
                        <p className="text-lg text-gray-900 dark:text-gray-200 font-medium leading-relaxed">
                            {item.title}
                        </p>
                        {/* If we had separate body content, it would go here. For now, we can omit or show summary again if needed. 
                            The design shows text below title. Assuming it's the full content. 
                            Since we only have summary, we will display the summary here as well if it's long, or leave it blank if value point covers it.
                            Let's display the summary again but formatted as body text to fill the space like the design.
                        */}
                         <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                            {item.summary}
                        </p>
                    </div>
                </div>

                {/* 4. Source Box (Blue) */}
                <div className="bg-blue-50/50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-100/50 dark:border-blue-800/30 space-y-3">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">来源</h3>
                    <div className="space-y-2 text-sm text-gray-800 dark:text-gray-300 font-medium">
                        <p>来源：{item.source}</p>
                        <p>原标题：{item.title}</p>
                        <div className="flex items-start gap-1">
                            <span className="shrink-0">来源URL：</span>
                            {item.url ? (
                                <a 
                                    href={item.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer" 
                                    className="text-gray-800 dark:text-blue-300 hover:text-blue-600 dark:hover:text-blue-200 hover:underline break-all"
                                >
                                    {item.url}
                                </a>
                            ) : (
                                <span>暂无</span>
                            )}
                        </div>
                    </div>
                </div>

            </div>

            {/* Floating Back Button */}
            <button
                onClick={() => navigate('/')}
                className="fixed bottom-12 right-12 flex items-center gap-2 px-6 py-3 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-200 rounded-full shadow-lg hover:bg-gray-50 dark:hover:bg-slate-700 hover:shadow-xl transition-all border border-gray-200 dark:border-slate-600 z-50 group font-medium"
                title="返回主页"
            >
                <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                <span>返回</span>
            </button>
        </div>
    );
}
