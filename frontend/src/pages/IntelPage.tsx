import { useIntelQuery } from '@/hooks/useIntelQuery';
import { useGlobalIntel } from '@/hooks/useGlobalIntel';
import { Banner } from '@/components/layout/Banner';
import { Toolbar } from '@/components/intel/Toolbar';
import { IntelList } from '@/components/intel/IntelList';
import { Loader2 } from 'lucide-react';

export function IntelPage() {
    const {
        items: searchItems,
        answer,
        status,
        progress,
        type, setType,
        range, setRange,
        setQuery,
        selectedIds,
        handleToggleFavorite,
        handleSelect,
        handleExport
    } = useIntelQuery();

    const { items: liveItems, status: liveStatus, toggleFavorite: toggleLiveFavorite } = useGlobalIntel(type === 'hot');

    // Determine which items to show
    const items = type === 'hot' ? liveItems : searchItems;
    const isLoading = type === 'hot' ? liveStatus === 'connecting' : status === 'loading';
    const onToggleFavorite = type === 'hot' ? toggleLiveFavorite : handleToggleFavorite;

    const headerContent = (
        <>
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
                        智能综述
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
            <Banner onSearch={setQuery} />
            
            <div className="flex flex-col flex-1 overflow-hidden">
                <Toolbar 
                    activeTab={type} 
                    onTabChange={setType} 
                    onExport={handleExport}
                    timeRange={range}
                    onTimeRangeChange={setRange}
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
