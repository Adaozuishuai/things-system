import { LayoutDashboard, Star, BarChart2, Settings, LogIn, LogOut, User as UserIcon, Globe } from 'lucide-react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';

export function Sidebar() {
    const location = useLocation();
    const pathname = location.pathname;
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const menuItems = [
        { label: "情报智探", route: "/intel", icon: LayoutDashboard },
        { label: "我的收藏", route: "/favorites", icon: Star },
        { label: "情报来源", route: "/sources", icon: Globe },
        { label: "数据概览", route: "/overview", icon: BarChart2 }
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-100 dark:border-slate-700 h-screen flex flex-col fixed left-0 top-0 z-10 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.02)]">
            <div className="px-6 py-8 flex items-center gap-3">
                <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                   <div className="w-4 h-4 border-[2.5px] border-white rounded-full"></div>
                </div>
                <h1 className="text-xl font-bold text-slate-800 dark:text-white tracking-tight">情报智探</h1>
            </div>

            <nav className="flex-1 px-4 space-y-1.5 py-4">
                {menuItems.map((item) => {
                    const isActive = pathname.startsWith(item.route);
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.route}
                            to={item.route}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                isActive 
                                    ? "bg-blue-50/80 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-semibold" 
                                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 font-medium"
                            )}
                        >
                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r-full"></div>
                            )}
                            <Icon size={20} className={cn("transition-transform duration-200", isActive ? "scale-105" : "group-hover:scale-105")} />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 space-y-2 mb-2">
                <div className="border-t border-slate-100 dark:border-slate-700 mb-4 mx-2"></div>
                
                {(() => {
                    const isSettingsActive = pathname.startsWith('/settings');
                    return (
                        <Link 
                            to="/settings" 
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                isSettingsActive 
                                    ? "bg-blue-50/80 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-semibold" 
                                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 font-medium"
                            )}
                        >
                            {isSettingsActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r-full"></div>
                            )}
                            <Settings size={20} className={cn("transition-transform duration-200", isSettingsActive ? "scale-105" : "group-hover:scale-105")} />
                            <span>系统设置</span>
                        </Link>
                    );
                })()}
                
                {user ? (
                    <div className="mt-2">
                        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/50 border border-slate-100 dark:border-slate-700 flex items-center gap-3">
                            <div className="w-9 h-9 bg-white dark:bg-slate-600 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-sm border border-slate-100 dark:border-slate-600">
                                <UserIcon size={16} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{user.username}</p>
                                <p className="text-xs text-slate-400">已登录</p>
                            </div>
                        </div>
                        <button 
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl mt-2 transition-colors text-sm font-medium"
                        >
                            <LogOut size={18} />
                            <span>退出登录</span>
                        </button>
                    </div>
                ) : (
                    <Link to="/login" className="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl mt-2 transition-colors font-medium">
                        <LogIn size={20} />
                        <span>登录 / 注册</span>
                    </Link>
                )}
            </div>
        </div>
    );
}
