import { Search } from 'lucide-react';
import { useState } from 'react';

interface BannerProps {
    onSearch: (query: string) => void;
}

export function Banner({ onSearch }: BannerProps) {
    const [value, setValue] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(value);
    };

    return (
        <div className="relative h-48 w-full bg-slate-900 overflow-hidden shrink-0">
            {/* Background Image Placeholder - Earth/Space style */}
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center opacity-80"></div>
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 to-transparent"></div>

            <div className="absolute inset-0 flex items-center justify-center">
                <form onSubmit={handleSubmit} className="w-full max-w-2xl px-4">
                    <div className="relative group">
                        <input
                            type="text"
                            value={value}
                            onChange={(e) => setValue(e.target.value)}
                            placeholder="内容搜索"
                            className="w-full h-14 pl-6 pr-14 rounded-full bg-white/90 dark:bg-slate-800/90 backdrop-blur text-lg dark:text-white shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder:text-gray-500 dark:placeholder:text-gray-400"
                        />
                        <button 
                            type="submit"
                            className="absolute right-2 top-2 h-10 w-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 transition-colors"
                        >
                            <Search size={20} />
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
