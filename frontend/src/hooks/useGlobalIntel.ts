import { useState, useEffect, useRef } from 'react';
import { IntelItem } from '@/types';
import { getFavorites, getGlobalStreamUrl, toggleFavorite as apiToggleFavorite } from '@/api';

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
    const [status, setStatus] = useState<'connecting' | 'reconnecting' | 'connected' | 'error'>('connecting');
    const eventSourceRef = useRef<EventSource | null>(null);
    const isClosingRef = useRef(false);
    const reconnectTimerRef = useRef<number | null>(null);
    const attemptRef = useRef(0);
    const lastSeenRef = useRef<{ ts: number; id: string } | null>(null);
    const [reconnectToken, setReconnectToken] = useState(0);
    const favoritesRef = useRef<Set<string>>(new Set());
    const favoritesLoadedRef = useRef(false);

    const getFavoritesStorageKey = () => {
        const username = localStorage.getItem('username') || 'anon';
        return `favorites:intel_ids:${username}`;
    };

    const persistFavoritesToStorage = () => {
        try {
            const key = getFavoritesStorageKey();
            localStorage.setItem(key, JSON.stringify(Array.from(favoritesRef.current)));
        } catch {
            void 0;
        }
    };

    const loadFavoritesFromStorage = () => {
        if (favoritesLoadedRef.current) return;
        favoritesLoadedRef.current = true;
        try {
            const key = getFavoritesStorageKey();
            const raw = localStorage.getItem(key);
            if (!raw) return;
            const ids: unknown = JSON.parse(raw);
            if (!Array.isArray(ids)) return;
            favoritesRef.current = new Set(ids.filter((x) => typeof x === 'string') as string[]);
        } catch {
            void 0;
        }
    };

    const applyFavorites = (data: IntelItem[]) => {
        if (!data.length) return data;
        const favorites = favoritesRef.current;
        if (!favorites.size) return data;
        return data.map((item) => (favorites.has(item.id) ? { ...item, favorited: true } : item));
    };

    const setFavoriteLocal = (id: string, favorited: boolean) => {
        if (favorited) {
            favoritesRef.current.add(id);
        } else {
            favoritesRef.current.delete(id);
        }
        persistFavoritesToStorage();
    };

    useEffect(() => {
        if (!enabled) return;
        loadFavoritesFromStorage();

        let cancelled = false;
        const loadAllFavorites = async () => {
            try {
                const limit = 200;
                let offset = 0;
                let total = Infinity;
                const ids = new Set<string>();
                while (!cancelled && offset < total && offset < 5000) {
                    const res = await getFavorites("", limit, offset);
                    for (const item of res.items ?? []) {
                        ids.add(item.id);
                    }
                    total = typeof res.total === 'number' ? res.total : offset + (res.items?.length ?? 0);
                    if (!res.items || res.items.length < limit) break;
                    offset += limit;
                }
                if (cancelled) return;
                favoritesRef.current = ids;
                persistFavoritesToStorage();
                setItems((prev) => applyFavorites(prev));
            } catch {
                void 0;
            }
        };

        loadAllFavorites();
        return () => {
            cancelled = true;
        };
    }, [enabled]);

    useEffect(() => {
        if (!enabled) {
            if (eventSourceRef.current) {
                isClosingRef.current = true;
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            if (reconnectTimerRef.current) {
                window.clearTimeout(reconnectTimerRef.current);
                reconnectTimerRef.current = null;
            }
            return;
        }

        isClosingRef.current = false;
        attemptRef.current = 0;

        const connect = () => {
            if (reconnectTimerRef.current) {
                window.clearTimeout(reconnectTimerRef.current);
                reconnectTimerRef.current = null;
            }

            if (eventSourceRef.current) {
                isClosingRef.current = true;
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }

            isClosingRef.current = false;
            setStatus(attemptRef.current > 0 ? 'reconnecting' : 'connecting');

            const last = lastSeenRef.current;
            const url = getGlobalStreamUrl(last ? { after_ts: last.ts, after_id: last.id } : undefined);
            const es = new EventSource(url);
            eventSourceRef.current = es;

            es.onopen = () => {
                attemptRef.current = 0;
                setStatus('connected');
            };

            es.onerror = () => {
                if (isClosingRef.current) {
                    return;
                }
                if (attemptRef.current >= 5) {
                    setStatus('error');
                    return;
                }

                attemptRef.current += 1;
                const delay = Math.min(30000, 1000 * Math.pow(2, attemptRef.current - 1));
                setStatus('reconnecting');

                reconnectTimerRef.current = window.setTimeout(() => {
                    connect();
                }, delay);
            };

            es.addEventListener('initial_batch', (event) => {
                try {
                    const data: IntelItem[] = applyFavorites(JSON.parse((event as MessageEvent).data));
                    setItems(prev => {
                        const merged = mergeAndSortByTimestampDesc(prev, data);
                        const top = merged[0];
                        if (top) {
                            lastSeenRef.current = { ts: top.timestamp, id: top.id };
                        }
                        return merged;
                    });
                } catch (e) {
                    console.error("Error parsing initial_batch", e);
                }
            });

            es.addEventListener('new_intel', (event) => {
                try {
                    const item: IntelItem = applyFavorites([JSON.parse((event as MessageEvent).data)])[0];
                    lastSeenRef.current = { ts: item.timestamp, id: item.id };
                    setItems(prev => mergeAndSortByTimestampDesc(prev, [item]));
                } catch (e) {
                    console.error("Error parsing new_intel", e);
                }
            });
        };

        connect();

        return () => {
            if (reconnectTimerRef.current) {
                window.clearTimeout(reconnectTimerRef.current);
                reconnectTimerRef.current = null;
            }
            if (eventSourceRef.current) {
                isClosingRef.current = true;
                eventSourceRef.current.close();
            }
        };
    }, [enabled, reconnectToken]);

    const reconnect = () => {
        attemptRef.current = 0;
        setStatus('connecting');
        setReconnectToken((x) => x + 1);
    };

    const toggleFavorite = async (id: string, current: boolean) => {
        try {
            const next = !current;
            await apiToggleFavorite(id, next);
            setFavoriteLocal(id, next);
            setItems(prev => prev.map(item => 
                item.id === id ? { ...item, favorited: next } : item
            ));
        } catch (error) {
            console.error("Failed to toggle favorite", error);
        }
    };

    const updateFavoritedLocal = (id: string, favorited: boolean) => {
        setFavoriteLocal(id, favorited);
        setItems(prev => prev.map(item => (item.id === id ? { ...item, favorited } : item)));
    };

    return {
        items,
        status,
        toggleFavorite,
        updateFavoritedLocal,
        reconnect
    };
}
