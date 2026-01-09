import { SearchType, TimeRange } from '@/types';
import { cn } from '@/lib/utils';
import { Download, ChevronDown } from 'lucide-react';

interface ToolbarProps {
    activeTab: SearchType;
    onTabChange: (tab: SearchType) => void;
    onExport: () => void;
    timeRange: TimeRange;
    onTimeRangeChange: (range: TimeRange) => void;
    below?: React.ReactNode;
}

export function Toolbar({ activeTab, onTabChange, onExport, timeRange, onTimeRangeChange, below }: ToolbarProps) {
    return (
        <div className="sticky top-0 z-10">
            <div className="flex items-center justify-between px-8 py-4 bg-transparent dark:bg-transparent border-b border-transparent">
                <div className="flex gap-8">
                    <button
                        onClick={() => onTabChange("hot")}
                        className={cn(
                            "text-lg font-medium pb-1 relative transition-colors",
                            activeTab === "hot" ? "text-red-600" : "text-gray-500 dark:text-gray-400 hover:text-red-600"
                        )}
                    >
                        <span className="flex items-center gap-2">
                            今日热点
                            {activeTab === "hot" && <span className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                            </span>}
                        </span>
                        {activeTab === "hot" && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-red-600 rounded-full" />
                        )}
                    </button>
                    <button
                        onClick={() => onTabChange("history")}
                        className={cn(
                            "text-lg font-medium pb-1 relative transition-colors",
                            activeTab === "history" ? "text-blue-600 dark:text-blue-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                        )}
                    >
                        历史情报
                        {activeTab === "history" && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 dark:bg-blue-400 rounded-full" />
                        )}
                    </button>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={onExport}
                        className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 text-white rounded-full text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
                    >
                        <Download size={16} />
                        导出
                    </button>

                    <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">时间选择</span>
                        <div className="relative">
                            <select
                                value={timeRange}
                                onChange={(e) => onTimeRangeChange(e.target.value as TimeRange)}
                                className="appearance-none bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 text-gray-700 dark:text-gray-200 text-sm rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                            >
                                <option value="all">全部</option>
                                <option value="3h">近3小时</option>
                                <option value="6h">近6小时</option>
                                <option value="12h">近12小时</option>
                            </select>
                            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={14} />
                        </div>
                    </div>
                </div>
            </div>

            {below}
        </div>
    );
}
