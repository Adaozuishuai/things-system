import { useIntelQuery } from '@/hooks/useIntelQuery';
import { useGlobalIntel } from '@/hooks/useGlobalIntel';
import { Toolbar } from '@/components/intel/Toolbar';
import { IntelList } from '@/components/intel/IntelList';
import { Loader2, Search } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export function IntelPage() {
    const {
        items: searchItems,
        answer,
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

    const { items: liveItems, status: liveStatus, toggleFavorite: toggleLiveFavorite, reconnect: reconnectLive } = useGlobalIntel(type === 'hot');

    const [historySearchValue, setHistorySearchValue] = useState('');
    const historySearchInputRef = useRef<HTMLInputElement | null>(null);

    const handleTabChange = (tab: typeof type) => {
        setType(tab);
    };

    useEffect(() => {
        if (type !== 'history') return;
        const t = window.setTimeout(() => historySearchInputRef.current?.focus(), 0);
        return () => window.clearTimeout(t);
    }, [type]);

    const submitHistorySearch = () => {
        setQuery(historySearchValue);
    };

    // Determine which items to show
    const items = type === 'hot' ? liveItems : searchItems;
    const isLoading = type === 'hot' ? (liveStatus === 'connecting' || liveStatus === 'reconnecting') : status === 'loading';
    const onToggleFavorite = type === 'hot' ? toggleLiveFavorite : handleToggleFavorite;

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
                                ? '推送中'
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

            {/* AI Answer */}
            {type !== 'hot' && answer && status === 'done' && (
                <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800 shadow-sm mx-6 mt-6">
                    <h3 className="text-sm font-bold text-blue-800 dark:text-blue-200 uppercase tracking-wide mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                        {type === 'history' ? (historySearchValue || query || '') : '智能综述'}
                    </h3>
                    <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                        {answer}
                    </p>
                </div>
            )}
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
                        <div className="bg-white dark:bg-slate-800 border-b dark:border-slate-700">
                            <div
                                className={[
                                    "relative z-20 overflow-hidden transition-all duration-300 ease-out",
                                    type === 'history' ? "max-h-28" : "max-h-0",
                                ].join(' ')}
                            >
                                <div
                                    className={[
                                        "px-6 md:px-8 pt-3 pb-4",
                                        "transition-all duration-300 ease-out",
                                        type === 'history' ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2",
                                    ].join(' ')}
                                >
                                    <form
                                        className="w-full max-w-3xl mx-auto"
                                        onSubmit={(e) => {
                                            e.preventDefault();
                                            submitHistorySearch();
                                        }}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="relative flex-1">
                                                <Search
                                                    size={18}
                                                    className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                                                />
                                                <input
                                                    ref={historySearchInputRef}
                                                    type="text"
                                                    value={historySearchValue}
                                                    onChange={(e) => setHistorySearchValue(e.target.value)}
                                                    placeholder="在历史情报中搜索"
                                                    className="w-full h-11 pl-11 pr-4 rounded-full bg-gray-50 dark:bg-slate-700 text-base dark:text-white shadow-sm border border-gray-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder:text-gray-500 dark:placeholder:text-gray-300"
                                                />
                                            </div>

                                            <button
                                                type="submit"
                                                className="h-11 px-5 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm font-medium"
                                            >
                                                搜索
                                            </button>
                                        </div>
                                    </form>
                                </div>
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
