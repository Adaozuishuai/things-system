import { useMemo } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

type SourceGroup = {
    name: string;
    items: unknown[];
    domain: string;
};

interface SourcesChartProps {
    sources: SourceGroup[];
}

export function SourcesChart({ sources }: SourcesChartProps) {
    const data = useMemo(() => {
        // 取前 10 个数据量最多的来源
        return sources
            .map(s => ({
                name: s.name || s.domain,
                count: s.items.length,
                domain: s.domain
            }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10);
    }, [sources]);

    if (data.length === 0) return null;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Top 10 情报源活跃度</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        margin={{
                            top: 5,
                            right: 30,
                            left: 20,
                            bottom: 5,
                        }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" opacity={0.5} />
                        <XAxis 
                            dataKey="name" 
                            tick={{ fill: '#64748B', fontSize: 12 }} 
                            axisLine={false}
                            tickLine={false}
                            interval={0}
                            tickFormatter={(val) => val.length > 8 ? val.slice(0, 8) + '...' : val}
                        />
                        <YAxis 
                            tick={{ fill: '#64748B', fontSize: 12 }} 
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip 
                            cursor={{ fill: '#F1F5F9', opacity: 0.5 }}
                            contentStyle={{ 
                                backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                                borderRadius: '8px',
                                border: 'none',
                                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                            }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={40}>
                            {data.map((_, index) => (
                                <Cell key={`cell-${index}`} fill={index < 3 ? '#3B82F6' : '#94A3B8'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
