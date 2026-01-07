import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { updateProfile, changePassword } from '@/api';
import { User, Shield, Key, Bell, Save, Moon, Sun, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';

export function SettingsPage() {
    const { user, refreshUser, applyTheme } = useAuth();
    
    // Form States
    const [nickname, setNickname] = useState(user?.username || '');
    const [email, setEmail] = useState(user?.email || '');
    const [bio, setBio] = useState(user?.bio || '');
    
    // Password States
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    
    // UI States
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'profile' | 'account' | 'preference'>('profile');
    const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');

    useEffect(() => {
        if (user) {
            setNickname(user.username || '');
            setEmail(user.email || '');
            setBio(user.bio || '');
            if (user.preferences?.theme) {
                setTheme(user.preferences.theme as any);
            }
        }
    }, [user]);

    const handleSaveProfile = async () => {
        setIsLoading(true);
        try {
            await updateProfile({
                username: nickname,
                email: email,
                bio: bio
            });
            await refreshUser();
            alert('个人资料已更新');
        } catch (error: any) {
            console.error(error);
            alert('更新失败: ' + (error.response?.data?.detail || error.message));
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpdatePassword = async () => {
        if (newPassword !== confirmPassword) {
            alert('两次输入的密码不一致');
            return;
        }
        if (!currentPassword) {
            alert('请输入当前密码');
            return;
        }

        setIsLoading(true);
        try {
            await changePassword({
                current_password: currentPassword,
                new_password: newPassword
            });
            alert('密码修改成功');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            console.error(error);
            alert('修改失败: ' + (error.response?.data?.detail || error.message));
        } finally {
            setIsLoading(false);
        }
    };

    const handleThemeChange = async (newTheme: 'light' | 'dark' | 'system') => {
        setTheme(newTheme);
        applyTheme(newTheme);
        
        // Save to backend
        try {
            await updateProfile({
                preferences: { ...user?.preferences, theme: newTheme }
            });
            await refreshUser();
        } catch (error) {
            console.error("Failed to save theme", error);
        }
    };

    const tabs = [
        { id: 'profile', label: '个人资料', icon: User },
        { id: 'account', label: '账号安全', icon: Shield },
        { id: 'preference', label: '偏好设置', icon: Bell },
    ];

    return (
        <div className="max-w-4xl mx-auto py-10 px-6">
            <h1 className="text-2xl font-bold text-slate-800 mb-2 dark:text-white">系统设置</h1>
            <p className="text-slate-500 mb-8 dark:text-slate-400">管理您的个人信息和系统偏好。</p>

            <div className="flex flex-col md:flex-row gap-8">
                {/* Sidebar Navigation */}
                <div className="w-full md:w-64 space-y-1">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm",
                                activeTab === tab.id 
                                    ? "bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-100 dark:border-slate-700" 
                                    : "text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200"
                            )}
                        >
                            <tab.icon size={18} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 space-y-6">
                    {/* Profile Settings */}
                    {activeTab === 'profile' && (
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <h2 className="text-lg font-semibold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
                                <User className="text-blue-500" size={20} />
                                基本信息
                            </h2>
                            
                            <div className="space-y-6">
                                {/* Avatar */}
                                <div className="flex items-center gap-6">
                                    <div className="w-20 h-20 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-400 border-2 border-white dark:border-slate-600 shadow-sm overflow-hidden">
                                        {user?.avatar ? (
                                            <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
                                        ) : (
                                            <User size={32} />
                                        )}
                                    </div>
                                    <div>
                                        <button className="px-4 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 hover:text-slate-900 transition-colors">
                                            更换头像
                                        </button>
                                        <p className="text-xs text-slate-400 mt-2">支持 JPG, PNG 格式，最大 2MB</p>
                                    </div>
                                </div>

                                {/* Form Fields */}
                                <div className="grid gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">用户名</label>
                                        <input 
                                            type="text" 
                                            value={nickname}
                                            onChange={(e) => setNickname(e.target.value)}
                                            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">电子邮箱</label>
                                        <input 
                                            type="email" 
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="example@email.com"
                                            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">个人简介</label>
                                        <textarea 
                                            rows={3}
                                            value={bio}
                                            onChange={(e) => setBio(e.target.value)}
                                            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50 resize-none"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <button 
                                        onClick={handleSaveProfile}
                                        disabled={isLoading}
                                        className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {isLoading ? '保存中...' : (
                                            <>
                                                <Save size={18} />
                                                保存修改
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Account Security */}
                    {activeTab === 'account' && (
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <h2 className="text-lg font-semibold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
                                <Shield className="text-green-500" size={20} />
                                账号安全
                            </h2>
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">当前密码</label>
                                    <div className="relative">
                                        <Key className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input 
                                            type="password" 
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">新密码</label>
                                        <div className="relative">
                                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                            <input 
                                                type="password" 
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">确认新密码</label>
                                        <div className="relative">
                                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                            <input 
                                                type="password" 
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-white bg-slate-50/50 dark:bg-slate-700/50"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <button 
                                        onClick={handleUpdatePassword}
                                        disabled={isLoading}
                                        className="px-6 py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                                    >
                                        {isLoading ? '更新中...' : '更新密码'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Preference */}
                    {activeTab === 'preference' && (
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <h2 className="text-lg font-semibold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
                                <Monitor className="text-purple-500" size={20} />
                                界面偏好
                            </h2>
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">主题模式</label>
                                    <div className="grid grid-cols-3 gap-4">
                                        <button 
                                            onClick={() => handleThemeChange('light')}
                                            className={cn(
                                                "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all",
                                                theme === 'light' 
                                                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400" 
                                                    : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
                                            )}
                                        >
                                            <Sun size={24} />
                                            <span className="text-sm font-medium">浅色</span>
                                        </button>
                                        <button 
                                            onClick={() => handleThemeChange('dark')}
                                            className={cn(
                                                "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all",
                                                theme === 'dark' 
                                                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400" 
                                                    : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
                                            )}
                                        >
                                            <Moon size={24} />
                                            <span className="text-sm font-medium">深色</span>
                                        </button>
                                        <button 
                                            onClick={() => handleThemeChange('system')}
                                            className={cn(
                                                "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all",
                                                theme === 'system' 
                                                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400" 
                                                    : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
                                            )}
                                        >
                                            <Monitor size={24} />
                                            <span className="text-sm font-medium">跟随系统</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
