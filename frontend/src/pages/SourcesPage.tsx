import { useEffect, useMemo, useRef, useState } from 'react';
import { getIntel } from '@/api';
import type { IntelItem } from '@/types';
import { cn } from '@/lib/utils';
import { ExternalLink, Globe, BarChart2, Calendar, Hash } from 'lucide-react';
import { useGlobalIntel } from '@/hooks/useGlobalIntel';
import { SourcesChart } from '@/components/sources/SourcesChart';

const TWO_PART_PUBLIC_SUFFIXES = new Set([
    'co.jp', 'or.jp', 'ne.jp', 'ac.jp', 'go.jp',
    'co.uk',
    'com.cn', 'net.cn', 'org.cn', 'gov.cn',
    'com.hk',
    'com.tw',
    'com.au',
]);

function getRegistrableDomain(hostname: string) {
    const host = hostname.toLowerCase().replace(/\.$/, '').replace(/^www\./, '');
    const parts = host.split('.').filter(Boolean);
    if (parts.length <= 2) return host;

    const last2 = parts.slice(-2).join('.');
    if (TWO_PART_PUBLIC_SUFFIXES.has(last2) && parts.length >= 3) {
        return parts.slice(-3).join('.');
    }
    return last2;
}

function tryParseUrl(raw?: string) {
    if (!raw) return null;
    try {
        return new URL(raw);
    } catch {
        try {
            return new URL(`https://${raw}`);
        } catch {
            return null;
        }
    }
}

const DOMAIN_NAME_MAP: Record<string, string> = {
    'ntv.co.jp': '日テレNEWS / NTV',
    'reuters.com': 'Reuters',
    'bbc.co.uk': 'BBC',
    'apnews.com': 'AP News',
    'news.un.org': '联合国新闻',
    'thehackernews.com': 'The Hacker News',
    'krebsonsecurity.com': 'KrebsOnSecurity',
};

type SourceGroup = {
    domain: string;
    host: string;
    origin: string;
    name: string;
    items: IntelItem[];
};

export function SourcesPage() {
    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState<IntelItem[]>([]);
    const [expandedDomain, setExpandedDomain] = useState<string | null>(null);
    const [pageByDomain, setPageByDomain] = useState<Record<string, number>>({});
    const { items: liveItems, status: liveStatus } = useGlobalIntel(true);
    const [registry, setRegistry] = useState<Record<string, SourceGroup>>({});
    const seenIdsRef = useRef<Set<string>>(new Set());
    const [sortBy, setSortBy] = useState<'count' | 'time'>('count');
    const [showChart, setShowChart] = useState(true);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        // 加载最近的 1000 条数据进行分析，避免数据量过大导致卡顿，同时覆盖足够多的来源
        getIntel('all', '', 'all', 1000, 0)
            .then((res) => {
                if (cancelled) return;
                setItems(res.items ?? []);
            })
            .catch((e) => {
                if (cancelled) return;
                console.error(e);
                setItems([]);
            })
            .finally(() => {
                if (cancelled) return;
                setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, []);

    const addToRegistry = (incoming: IntelItem[]) => {
        setRegistry((prev) => {
            const next = { ...prev };
            for (const item of incoming) {
                if (!item?.id) continue;
                if (seenIdsRef.current.has(item.id)) continue;
                if (!item.url && !item.source) continue;

                const u = tryParseUrl(item.url);
                let domain: string;
                let host: string;
                let origin: string;

                if (u) {
                    host = u.hostname.toLowerCase().replace(/^www\./, '');
                    domain = getRegistrableDomain(host);
                    origin = u.origin;
                } else {
                    const sourceSlug = (item.source || '')
                        .toLowerCase()
                        .trim()
                        .replace(/\s+/g, '-')
                        .replace(/[^a-z0-9.-]/g, '');

                    domain = sourceSlug || 'unknown';
                    host = domain;
                    origin = `https://${domain}`;
                }

                seenIdsRef.current.add(item.id);

                const key = domain;
                const name = DOMAIN_NAME_MAP[domain] || item.source || domain;

                const current = next[key];
                if (!current) {
                    next[key] = { domain, host, origin, name, items: [item] };
                    continue;
                }

                const already = current.items.some((x) => x.id === item.id);
                if (already) continue;

                next[key] = {
                    ...current,
                    host: current.host || host,
                    origin: current.origin || origin,
                    items: [item, ...current.items],
                };
            }

            return next;
        });
    };

    useEffect(() => {
        addToRegistry(items);
    }, [items]);

    useEffect(() => {
        addToRegistry(liveItems);
    }, [liveItems]);

    const sources = useMemo(() => {
        const list = Object.values(registry).map((s) => ({
            ...s,
            items: s.items
                .slice()
                .sort((a, b) => b.timestamp - a.timestamp),
        }));

        if (sortBy === 'time') {
            return list.sort((a, b) => {
                const timeA = a.items[0]?.timestamp ?? 0;
                const timeB = b.items[0]?.timestamp ?? 0;
                return timeB - timeA;
            });
        }
        
        return list.sort((a, b) => (b.items.length - a.items.length) || (b.items[0]?.timestamp ?? 0) - (a.items[0]?.timestamp ?? 0));
    }, [registry, sortBy]);

    // 统计总数并在变化时高亮
    const totalItems = useMemo(() => {
        return sources.reduce((acc, s) => acc + s.items.length, 0);
    }, [sources]);

    const [highlightCount, setHighlightCount] = useState(false);
    const prevTotalRef = useRef(totalItems);

    useEffect(() => {
        if (totalItems > prevTotalRef.current) {
            setHighlightCount(true);
            const timer = setTimeout(() => setHighlightCount(false), 2000);
            return () => clearTimeout(timer);
        }
        prevTotalRef.current = totalItems;
    }, [totalItems]);

    return (
        <div className="flex flex-col h-full bg-white dark:bg-slate-900">
            <div className="p-6 bg-white dark:bg-slate-800 border-b dark:border-slate-700 space-y-6">
                <div className="flex items-center justify-between gap-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <Globe size={22} />
                            <span>情报来源仪表盘</span>
                        </h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-2">
                            {loading 
                                ? '加载中…' 
                                : liveStatus === 'connected' 
                                    ? (
                                        <>
                                            <span>实时监控中 · 共 {sources.length} 个来源</span>
                                            <span className={cn(
                                                "transition-all duration-300 px-2 py-0.5 rounded-full text-xs font-medium",
                                                highlightCount 
                                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 scale-110" 
                                                    : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                                            )}>
                                                {totalItems} 条情报
                                            </span>
                                        </>
                                    )
                                    : `连接中… · 共 ${sources.length} 个来源 (${totalItems} 条情报)`}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setShowChart(!showChart)}
                            className={cn(
                                "p-2 rounded-lg transition-colors border",
                                showChart 
                                    ? "bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400" 
                                    : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400"
                            )}
                            title={showChart ? "隐藏图表" : "显示图表"}
                        >
                            <BarChart2 size={20} />
                        </button>
                        <div className="h-8 w-px bg-slate-200 dark:bg-slate-700 mx-1" />
                        <div className="flex bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
                            <button
                                onClick={() => setSortBy('count')}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                                    sortBy === 'count'
                                        ? "bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm"
                                        : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                                )}
                            >
                                <Hash size={16} />
                                数量优先
                            </button>
                            <button
                                onClick={() => setSortBy('time')}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                                    sortBy === 'time'
                                        ? "bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm"
                                        : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                                )}
                            >
                                <Calendar size={16} />
                                更新时间
                            </button>
                        </div>
                    </div>
                </div>

                {showChart && !loading && sources.length > 0 && (
                    <div className="animate-in fade-in slide-in-from-top-4 duration-500">
                        <SourcesChart sources={sources} />
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900 p-6">
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : sources.length === 0 ? (
                    <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
                        暂无来源
                    </div>
                ) : (
                    <div className="max-w-full mx-auto">
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {sources.map((s) => {
                                const open = expandedDomain === s.domain;
                                const pageSize = 10;
                                const totalPages = Math.max(1, Math.ceil(s.items.length / pageSize));
                                const page = Math.min(totalPages, Math.max(1, pageByDomain[s.domain] ?? 1));
                                const start = (page - 1) * pageSize;
                                const visibleItems = s.items.slice(start, start + pageSize);
                                return (
                                    <div key={s.domain} className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm overflow-hidden h-fit">
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setExpandedDomain((cur) => {
                                                    const next = cur === s.domain ? null : s.domain;
                                                    if (next) {
                                                        setPageByDomain((prev) => ({ ...prev, [s.domain]: 1 }));
                                                    }
                                                    return next;
                                                });
                                            }}
                                            className="w-full px-5 py-4 flex items-center justify-between gap-4 hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors"
                                        >
                                            <div className="min-w-0 text-left">
                                                <div className="text-base font-semibold text-slate-800 dark:text-slate-100 truncate">{s.name}</div>
                                                <div className="text-sm text-slate-500 dark:text-slate-400 truncate">{s.host}</div>
                                            </div>
                                            <div className="flex items-center gap-3 shrink-0">
                                                <span 
                                                    data-testid="source-count"
                                                    className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                                                >
                                                    {s.items.length}
                                                </span>
                                                <a
                                                    href={s.origin}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors text-slate-500 dark:text-slate-400"
                                                    title="打开网站"
                                                >
                                                    <ExternalLink size={16} />
                                                </a>
                                            </div>
                                        </button>

                                        {open && (
                                            <div className="border-t border-slate-100 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-700/20">
                                                <div className="px-5 py-3 flex items-center justify-between gap-3">
                                                    <div className="text-xs text-slate-500 dark:text-slate-400">
                                                        全部链接（共 {s.items.length} 条）
                                                    </div>
                                                    <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                                                        <button
                                                            type="button"
                                                            disabled={page <= 1}
                                                            onClick={() => setPageByDomain((prev) => ({ ...prev, [s.domain]: Math.max(1, page - 1) }))}
                                                            className={cn(
                                                                "px-2 py-1 rounded-md border transition-colors",
                                                                page <= 1
                                                                    ? "border-slate-200 dark:border-slate-700 text-slate-300 dark:text-slate-600 cursor-not-allowed"
                                                                    : "border-slate-200 dark:border-slate-700 hover:bg-white/70 dark:hover:bg-slate-700/40"
                                                            )}
                                                        >
                                                            上一页
                                                        </button>
                                                        <span className="tabular-nums">
                                                            {page} / {totalPages}
                                                        </span>
                                                        <button
                                                            type="button"
                                                            disabled={page >= totalPages}
                                                            onClick={() => setPageByDomain((prev) => ({ ...prev, [s.domain]: Math.min(totalPages, page + 1) }))}
                                                            className={cn(
                                                                "px-2 py-1 rounded-md border transition-colors",
                                                                page >= totalPages
                                                                    ? "border-slate-200 dark:border-slate-700 text-slate-300 dark:text-slate-600 cursor-not-allowed"
                                                                    : "border-slate-200 dark:border-slate-700 hover:bg-white/70 dark:hover:bg-slate-700/40"
                                                            )}
                                                        >
                                                            下一页
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="px-2 pb-3">
                                                    {s.items.length === 0 ? (
                                                        <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
                                                            暂无可用链接
                                                        </div>
                                                    ) : (
                                                        visibleItems.map((it) => (
                                                            <a
                                                                key={it.id}
                                                                href={it.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className={cn(
                                                                    "block px-3 py-2 rounded-lg text-sm truncate",
                                                                    "text-slate-700 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400",
                                                                    "hover:bg-white/80 dark:hover:bg-slate-700/40 transition-colors"
                                                                )}
                                                                title={it.title || it.url}
                                                            >
                                                                {it.title || it.url}
                                                            </a>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
