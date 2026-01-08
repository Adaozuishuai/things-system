import { useState, useEffect, useRef } from 'react';
import { IntelItem } from '@/types';
import { getGlobalStreamUrl, toggleFavorite as apiToggleFavorite } from '@/api';

function mergeAndSortByTimestampDesc(existing: IntelItem[], incoming: IntelItem[]) {
    const byId = new Map<string, IntelItem>();

    for (const item of incoming) {
        byId.set(item.id, item);
    }

    for (const item of existing) {
        const current = byId.get(item.id);
        if (!current) {
            byId.set(item.id, item);
            continue;
        }
        byId.set(item.id, { ...current, favorited: item.favorited });
    }

    return Array.from(byId.values()).sort((a, b) => b.timestamp - a.timestamp);
}

export function useGlobalIntel(enabled: boolean = true) {
    const [items, setItems] = useState<IntelItem[]>([]);
    const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
    const eventSourceRef = useRef<EventSource | null>(null);
    const isClosingRef = useRef(false);

    useEffect(() => {
        if (!enabled) {
            if (eventSourceRef.current) {
                isClosingRef.current = true;
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            return;
        }

        isClosingRef.current = false;
        const url = getGlobalStreamUrl();
        const es = new EventSource(url);
        eventSourceRef.current = es;

        es.onopen = () => {
            console.log("Global stream connected");
            setStatus('connected');
        };

        es.onerror = () => {
            if (isClosingRef.current) {
                return;
            }
            if (es.readyState === EventSource.CLOSED) {
                return;
            }
            setStatus('connecting');
        };

        // Listen for initial batch history
        es.addEventListener('initial_batch', (event) => {
            try {
                const data: IntelItem[] = JSON.parse((event as MessageEvent).data);
                console.log("Received initial batch:", data.length);
                setItems(prev => mergeAndSortByTimestampDesc(prev, data));
            } catch (e) {
                console.error("Error parsing initial_batch", e);
            }
        });

        // Listen for new single item
        es.addEventListener('new_intel', (event) => {
            try {
                const item: IntelItem = JSON.parse((event as MessageEvent).data);
                console.log("Received new intel:", item.id);
                setItems(prev => mergeAndSortByTimestampDesc(prev, [item]));
            } catch (e) {
                console.error("Error parsing new_intel", e);
            }
        });

        return () => {
            if (eventSourceRef.current) {
                isClosingRef.current = true;
                eventSourceRef.current.close();
            }
        };
    }, [enabled]);

    const toggleFavorite = async (id: string, current: boolean) => {
        try {
            await apiToggleFavorite(id, !current);
            setItems(prev => prev.map(item => 
                item.id === id ? { ...item, favorited: !current } : item
            ));
        } catch (error) {
            console.error("Failed to toggle favorite", error);
        }
    };

    return {
        items,
        status,
        toggleFavorite
    };
}
