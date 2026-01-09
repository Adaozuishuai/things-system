import { useIntelQuery } from '@/hooks/useIntelQuery';
import { useGlobalIntel } from '@/hooks/useGlobalIntel';
import { Toolbar } from '@/components/intel/Toolbar';
import { IntelList } from '@/components/intel/IntelList';
import { Loader2, Search } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { getIntel, toggleFavorite as apiToggleFavorite } from '@/api';
import type { IntelItem } from '@/types';

function matchesHotSearch(item: IntelItem, q: string) {
    const needle = q.trim().toLowerCase();
    if (!needle) return true;

    const haystacks: string[] = [];
    if (item.title) haystacks.push(item.title);
    if (item.summary) haystacks.push(item.summary);
    if (item.content) haystacks.push(item.content);
    if (item.source) haystacks.push(item.source);
    if (item.time) haystacks.push(item.time);
    for (const t of item.tags || []) {
        if (t?.label) haystacks.push(t.label);
    }

    return haystacks.some((h) => h.toLowerCase().includes(needle));
}

export function IntelPage() {
    const {
        items: searchItems,
        status,
        progress,
        query,
        type, setType,
        range, setRange,
        setQuery,
        selectedIds,
        handleToggleFavorite,
        handleSelect,
        handleExport
    } = useIntelQuery();

    const { items: liveItems, status: liveStatus, toggleFavorite: toggleLiveFavorite, updateFavoritedLocal, reconnect: reconnectLive } = useGlobalIntel(type === 'hot');

    const [historySearchValue, setHistorySearchValue] = useState('');
    const historySearchInputRef = useRef<HTMLInputElement | null>(null);

    const [hotSearchValue, setHotSearchValue] = useState('');
    const [hotSearchQuery, setHotSearchQuery] = useState('');
    const hotSearchInputRef = useRef<HTMLInputElement | null>(null);
    const [hotSearchDbItems, setHotSearchDbItems] = useState<IntelItem[]>([]);
    const [hotSearchItems, setHotSearchItems] = useState<IntelItem[]>([]);
    const [hotSearchLoading, setHotSearchLoading] = useState(false);
    const [hotSearchRefreshToken, setHotSearchRefreshToken] = useState(0);
    const isHotSearchMode = type === 'hot' && hotSearchQuery.trim().length > 0;

    const handleTabChange = (tab: typeof type) => {
        setType(tab);
    };

    useEffect(() => {
        if (type !== 'history') return;
        const t = window.setTimeout(() => historySearchInputRef.current?.focus(), 0);
        return () => window.clearTimeout(t);
    }, [type]);

    useEffect(() => {
        if (type !== 'hot') return;
        const t = window.setTimeout(() => hotSearchInputRef.current?.focus(), 0);
        return () => window.clearTimeout(t);
    }, [type]);

    const submitHistorySearch = () => {
        setQuery(historySearchValue);
    };

    const submitHotSearch = () => {
        const q = hotSearchValue.trim();
        setHotSearchQuery(q);
        if (q) {
            setHotSearchRefreshToken((x) => x + 1);
        }
        if (!q) {
            setHotSearchDbItems([]);
            setHotSearchItems([]);
        }
    };

    useEffect(() => {
        if (type !== 'hot') return;
        if (!hotSearchQuery.trim()) return;

        let cancelled = false;
        setHotSearchLoading(true);

        getIntel('hot', hotSearchQuery, range, 50, 0)
            .then((res) => {
                if (cancelled) return;
                setHotSearchDbItems(res.items ?? []);
            })
            .catch((err) => {
                if (cancelled) return;
                console.error(err);
                setHotSearchDbItems([]);
            })
            .finally(() => {
                if (cancelled) return;
                setHotSearchLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [type, hotSearchQuery, range, hotSearchRefreshToken]);

    useEffect(() => {
        if (!isHotSearchMode) return;
        const map = new Map<string, IntelItem>();
        for (const item of hotSearchDbItems) {
            map.set(item.id, item);
        }
        for (const item of liveItems) {
            if (!matchesHotSearch(item, hotSearchQuery)) continue;
            map.set(item.id, item);
        }
        const merged = Array.from(map.values()).sort((a, b) => b.timestamp - a.timestamp);
        setHotSearchItems(merged);
    }, [isHotSearchMode, hotSearchDbItems, liveItems, hotSearchQuery]);

    const exitHotSearchMode = () => {
        setHotSearchValue('');
        setHotSearchQuery('');
        setHotSearchDbItems([]);
        setHotSearchItems([]);
        hotSearchInputRef.current?.focus();
    };

    const handleHotSearchToggleFavorite = async (id: string, current: boolean) => {
        const next = !current;
        setHotSearchItems((prev) => prev.map((x) => (x.id === id ? { ...x, favorited: next } : x)));
        updateFavoritedLocal(id, next);
        try {
            await apiToggleFavorite(id, next);
        } catch (err) {
            setHotSearchItems((prev) => prev.map((x) => (x.id === id ? { ...x, favorited: current } : x)));
            updateFavoritedLocal(id, current);
        }
    };

    // Determine which items to show
    const items = type === 'hot' ? (isHotSearchMode ? hotSearchItems : liveItems) : searchItems;
    const isLoading = type === 'hot'
        ? (isHotSearchMode ? hotSearchLoading : (liveStatus === 'connecting' || liveStatus === 'reconnecting'))
        : status === 'loading';
    const onToggleFavorite = type === 'hot'
        ? (isHotSearchMode ? handleHotSearchToggleFavorite : toggleLiveFavorite)
        : handleToggleFavorite;

    const headerContent = (
        <>
            {type === 'hot' && (
                <div
                    className={[
                        "mb-6 p-4 rounded-lg border flex items-center gap-3 mx-6 mt-6",
                        liveStatus === 'connected'
                            ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-100 dark:border-emerald-800/40"
                            : liveStatus === 'reconnecting'
                                ? "bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/40"
                            : liveStatus === 'error'
                                ? "bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/40"
                                : "bg-blue-50 dark:bg-blue-900/30 border-blue-100 dark:border-blue-800",
                    ].join(' ')}
                >
                    {liveStatus === 'connected' ? (
                        <span className="w-2 h-2 rounded-full bg-emerald-600 dark:bg-emerald-400" />
                    ) : liveStatus === 'error' ? (
                        <span className="w-2 h-2 rounded-full bg-red-600 dark:bg-red-400" />
                    ) : liveStatus === 'reconnecting' ? (
                        <Loader2 className="animate-spin text-red-600 dark:text-red-400" />
                    ) : (
                        <Loader2 className="animate-spin text-blue-600 dark:text-blue-400" />
                    )}
                    <div className="flex-1 flex items-center justify-between gap-3">
                        <span
                            className={[
                                "font-medium",
                                liveStatus === 'connected'
                                    ? "text-emerald-900 dark:text-emerald-100"
                                    : liveStatus === 'reconnecting'
                                        ? "text-red-900 dark:text-red-100"
                                    : liveStatus === 'error'
                                        ? "text-red-900 dark:text-red-100"
                                        : "text-blue-900 dark:text-blue-100",
                            ].join(' ')}
                        >
                            {liveStatus === 'connected'
                                ? (isHotSearchMode ? `正在推送${hotSearchValue.trim() || hotSearchQuery}有关消息` : '消息推送中')
                                : liveStatus === 'reconnecting'
                                    ? '重连中...'
                                    : liveStatus === 'connecting'
                                        ? '连接中...'
                                        : '消息推送连接失败'}
                        </span>
                        {liveStatus === 'error' && (
                            <button
                                onClick={reconnectLive}
                                className="shrink-0 px-4 py-1.5 rounded-full bg-red-600 text-white hover:bg-red-700 transition-colors shadow-sm font-medium text-sm"
                            >
                                重新连接
                            </button>
                        )}
                    </div>
                </div>
            )}
            {/* Agent Status / Progress - Only show for non-live tabs */}
            {type !== 'hot' && (status === 'loading' || status === 'streaming') && (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-100 dark:border-blue-800 flex items-center gap-3 mx-6 mt-6">
                    <Loader2 className="animate-spin text-blue-600 dark:text-blue-400" />
                    <div className="flex flex-col">
                        <span className="font-medium text-blue-900 dark:text-blue-100">
                            Agent 正在运行中...
                        </span>
                        {progress && (
                            <span className="text-sm text-blue-700 dark:text-blue-300">
                                {progress.message} ({progress.step})
                            </span>
                        )}
                    </div>
                </div>
            )}

            {type !== 'hot' && status === 'done' && (() => {
                const text = (type === 'history' ? (historySearchValue || query || '') : (query || '')).trim();
                if (!text) return null;
                return (
                    <div className="mb-6 p-4 bg-blue-50/70 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800 mx-6 mt-6">
                        <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                            共找到 {searchItems.length} 条与「{text}」相关的信息
                        </span>
                    </div>
                );
            })()}
        </>
    );

    return (
        <div className="flex flex-col h-full bg-white dark:bg-slate-900">
            <div className="flex flex-col flex-1 overflow-hidden">
                <Toolbar 
                    activeTab={type} 
                    onTabChange={handleTabChange} 
                    onExport={handleExport}
                    timeRange={range}
                    onTimeRangeChange={setRange}
                    below={
                        <div
                            className={[
                                "relative z-20 overflow-hidden transition-all duration-300 ease-out",
                                type === 'history' || type === 'hot' ? "max-h-28" : "max-h-0",
                            ].join(' ')}
                        >
                            <div
                                className={[
                                    "px-6 md:px-8 pt-3 pb-4",
                                    "transition-all duration-300 ease-out",
                                    type === 'history' || type === 'hot' ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2",
                                ].join(' ')}
                            >
                                <form
                                    className="w-full max-w-3xl mx-auto"
                                    onSubmit={(e) => {
                                        e.preventDefault();
                                        if (type === 'history') {
                                            submitHistorySearch();
                                            return;
                                        }
                                        submitHotSearch();
                                    }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="relative flex-1">
                                            <Search
                                                size={18}
                                                className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                                            />
                                            <input
                                                ref={type === 'history' ? historySearchInputRef : hotSearchInputRef}
                                                type="text"
                                                value={type === 'history' ? historySearchValue : hotSearchValue}
                                                onChange={(e) => {
                                                    if (type === 'history') {
                                                        setHistorySearchValue(e.target.value);
                                                        return;
                                                    }
                                                    setHotSearchValue(e.target.value);
                                                }}
                                                placeholder={type === 'history' ? "在历史情报中搜索" : "在今日热点中搜索"}
                                                className="w-full h-11 pl-11 pr-4 rounded-full bg-gray-50 dark:bg-slate-700 text-base dark:text-white shadow-sm border border-gray-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder:text-gray-500 dark:placeholder:text-gray-300"
                                            />
                                        </div>

                                        <button
                                            type="submit"
                                            className="h-11 px-5 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm font-medium"
                                        >
                                            搜索
                                        </button>
                                        {type === 'hot' && (hotSearchValue.trim().length > 0 || hotSearchQuery.trim().length > 0) && (
                                            <button
                                                type="button"
                                                onClick={exitHotSearchMode}
                                                className="h-11 px-5 rounded-full bg-transparent text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-slate-600 hover:bg-gray-50/70 dark:hover:bg-slate-700/60 transition-colors shadow-sm font-medium"
                                            >
                                                清除
                                            </button>
                                        )}
                                    </div>
                                </form>
                            </div>
                        </div>
                    }
                />
                
                <div className="flex-1 overflow-hidden bg-white dark:bg-slate-900">
                    <IntelList 
                        items={items} 
                        loading={isLoading} 
                        onToggleFavorite={onToggleFavorite}
                        selectedIds={selectedIds}
                        onSelect={handleSelect}
                        header={headerContent}
                    />
                </div>
            </div>
        </div>
    );
}
