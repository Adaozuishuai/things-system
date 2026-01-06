import { LayoutDashboard, Star, BarChart2, Settings } from 'lucide-react';
import { useLocation, Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function Sidebar() {
    const location = useLocation();
    const pathname = location.pathname;

    const menuItems = [
        { label: "情报智探", route: "/intel", icon: LayoutDashboard },
        { label: "我的收藏", route: "/favorites", icon: Star },
        { label: "数据概览", route: "/overview", icon: BarChart2 }
    ];

    return (
        <div className="w-64 bg-white border-r h-screen flex flex-col fixed left-0 top-0 z-10">
            <div className="p-6 flex items-center gap-3 border-b border-gray-100">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                   <div className="w-4 h-4 border-2 border-white rounded-full"></div>
                </div>
                <h1 className="text-xl font-bold text-gray-800">情报智探</h1>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => {
                    const isActive = pathname.startsWith(item.route);
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.route}
                            to={item.route}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                                isActive 
                                    ? "bg-blue-600 text-white shadow-md shadow-blue-200" 
                                    : "text-gray-600 hover:bg-gray-50"
                            )}
                        >
                            <Icon size={20} />
                            <span className="font-medium">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-gray-100">
                <Link to="/settings" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg">
                    <Settings size={20} />
                    <span className="font-medium">系统设置</span>
                </Link>
            </div>
        </div>
    );
}
