import { useState, useEffect, useRef } from 'react';
import { IntelItem } from '@/types';
import { getGlobalStreamUrl, toggleFavorite as apiToggleFavorite } from '@/api';

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
                // Prepend or set? Since it's initial, set is fine.
                // But if we want to support reconnect, maybe careful.
                // Assuming simple case:
                setItems(data.reverse()); // Newest first?
            } catch (e) {
                console.error("Error parsing initial_batch", e);
            }
        });

        // Listen for new single item
        es.addEventListener('new_intel', (event) => {
            try {
                const item: IntelItem = JSON.parse((event as MessageEvent).data);
                console.log("Received new intel:", item.id);
                setItems(prev => [item, ...prev]);
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
