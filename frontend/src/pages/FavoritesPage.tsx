import { useEffect, useState } from 'react';
import { IntelItem } from '@/types';
import { getFavorites, toggleFavorite } from '@/api';
import { IntelList } from '@/components/intel/IntelList';

export function FavoritesPage() {
    const [items, setItems] = useState<IntelItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    useEffect(() => {
        loadFavorites();
    }, []);

    const loadFavorites = async () => {
        setLoading(true);
        try {
            const data = await getFavorites();
            setItems(data.items);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleFavorite = async (id: string, current: boolean) => {
        try {
            await toggleFavorite(id, !current);
            // Remove from list if unfavorited
            if (current) {
                setItems(prev => prev.filter(i => i.id !== id));
            }
        } catch (err) {
            console.error(err);
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

    return (
        <div className="flex flex-col h-full bg-white dark:bg-slate-900">
            <div className="p-8 bg-white dark:bg-slate-800 border-b dark:border-slate-700">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">我的收藏</h1>
                <p className="text-gray-500 dark:text-gray-400 mt-2">已收藏的情报列表</p>
            </div>
            
            <div className="flex-1 overflow-y-auto bg-white dark:bg-slate-900 p-6">
                <IntelList 
                    items={items} 
                    loading={loading} 
                    onToggleFavorite={handleToggleFavorite}
                    selectedIds={selectedIds}
                    onSelect={handleSelect}
                />
            </div>
        </div>
    );
}
