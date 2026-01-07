import { Sidebar } from './Sidebar';
import { Outlet } from 'react-router-dom';

export function Layout() {
    return (
        <div className="flex min-h-screen bg-[#f8f9fa] dark:bg-slate-900">
            <Sidebar />
            <main className="flex-1 ml-64 flex flex-col h-screen overflow-hidden">
                <Outlet />
            </main>
        </div>
    );
}
