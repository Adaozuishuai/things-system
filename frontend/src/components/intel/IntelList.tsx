import { Virtuoso } from 'react-virtuoso';
import { IntelItem as IntelItemType } from '@/types';
import { IntelItem } from './IntelItem';

interface IntelListProps {
    items: IntelItemType[];
    loading: boolean;
    onToggleFavorite: (id: string, current: boolean) => void;
    selectedIds: Set<string>;
    onSelect: (id: string, selected: boolean) => void;
    header?: React.ReactNode;
}

export function IntelList({ items, loading, onToggleFavorite, selectedIds, onSelect, header }: IntelListProps) {
    if (loading && items.length === 0) {
        return (
            <div className="flex flex-col h-full bg-white">
                {header}
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <div className="flex flex-col h-full bg-white">
                {header}
                <div className="flex items-center justify-center h-64 text-gray-500">
                    暂无相关情报
                </div>
            </div>
        );
    }

    return (
        <Virtuoso
            style={{ height: '100%', backgroundColor: 'white' }}
            data={items}
            components={{
                Header: () => <>{header}</>
            }}
            itemContent={(_, item) => (
                <IntelItem 
                    key={item.id} 
                    item={item} 
                    onToggleFavorite={onToggleFavorite}
                    selected={selectedIds.has(item.id)}
                    onSelect={onSelect}
                />
            )}
        />
    );
}
