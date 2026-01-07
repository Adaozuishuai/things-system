import { useState, useEffect, useRef, useCallback } from 'react';
import { IntelItem, SearchType, TimeRange, AgentSearchResponse } from '@/types';
import { runAgentTask, getAgentStreamUrl, toggleFavorite as apiToggleFavorite, exportIntel } from '@/api';

export function useIntelQuery() {
    const [items, setItems] = useState<IntelItem[]>([]);
    const [answer, setAnswer] = useState<string | null>(null);
    const [status, setStatus] = useState<'idle' | 'loading' | 'streaming' | 'done' | 'error'>('idle');
    const [progress, setProgress] = useState<{step: string, message: string} | null>(null);
    
    // Filters
    const [query, setQuery] = useState("");
    const [type, setType] = useState<SearchType>("hot");
    const [range, setRange] = useState<TimeRange>("all");
    
    // Selection
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const eventSourceRef = useRef<EventSource | null>(null);

    const startSearch = useCallback(async (q: string, t: SearchType, r: TimeRange) => {
        // Cancel previous stream if any
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setStatus('loading');
        setItems([]); // Clear previous items or keep them? Maybe clear for new search.
        setAnswer(null);
        setProgress(null);

        try {
            const taskId = await runAgentTask(q, t, r);
            
            setStatus('streaming');
            const url = getAgentStreamUrl(taskId);
            const es = new EventSource(url);
            eventSourceRef.current = es;

            es.onmessage = (_event) => {
                // Keep-alive or generic message
            };

            es.addEventListener('status', (event) => {
                const messageEvent = event as MessageEvent;
                const data = JSON.parse(messageEvent.data);
                if (data.status === 'done') {
                    es.close();
                    setStatus('done');
                    setProgress(null);
                }
            });

            es.addEventListener('progress', (event) => {
                const messageEvent = event as MessageEvent;
                const data = JSON.parse(messageEvent.data);
                setProgress(data);
            });

            es.addEventListener('result', (event) => {
                const messageEvent = event as MessageEvent;
                const data: AgentSearchResponse = JSON.parse(messageEvent.data);
                setItems(data.items);
                setAnswer(data.answer || null);
            });

            es.addEventListener('error', (event) => {
                console.error("SSE Error", event);
                es.close();
                setStatus('error');
            });

            es.onerror = (err) => {
                console.error("EventSource failed", err);
                es.close();
                setStatus('error');
            };

        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    }, []);

    // Trigger search when filters change
    useEffect(() => {
        let isMounted = true;
        
        // Wrap startSearch to respect mounted state
        const performSearch = async () => {
             // Don't auto-trigger agent task for 'hot' type unless there is a query
             if (type === 'hot' && !query) {
                 return;
             }

             if (isMounted) {
                 await startSearch(query, type, range);
             }
        };
        
        performSearch();

        return () => {
            isMounted = false;
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, [query, type, range, startSearch]);

    const handleToggleFavorite = async (id: string, current: boolean) => {
        // Optimistic update
        setItems(prev => prev.map(item => 
            item.id === id ? { ...item, favorited: !current } : item
        ));
        try {
            await apiToggleFavorite(id, !current);
        } catch (err) {
            // Revert
            setItems(prev => prev.map(item => 
                item.id === id ? { ...item, favorited: current } : item
            ));
        }
    };

    const handleSelect = (id: string, selected: boolean) => {
        const newSet = new Set(selectedIds);
        if (selected) {
            newSet.add(id);
        } else {
            newSet.delete(id);
        }
        setSelectedIds(newSet);
    };

    const handleExport = async () => {
        try {
            const blob = await exportIntel(Array.from(selectedIds), type, range, query);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;

            let filename = '情报批量导出.docx';
            if (selectedIds.size === 1) {
                const id = Array.from(selectedIds)[0];
                const item = items.find(i => i.id === id);
                if (item) {
                    const safeTitle = item.title.replace(/[\\/:*?"<>|]/g, "");
                    filename = `${safeTitle}.docx`;
                }
            }

            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Export failed", err);
        }
    };

    return {
        items,
        answer,
        status,
        progress,
        query, setQuery,
        type, setType,
        range, setRange,
        selectedIds,
        handleToggleFavorite,
        handleSelect,
        handleExport
    };
}
