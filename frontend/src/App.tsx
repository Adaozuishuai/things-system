import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { IntelPage } from '@/pages/IntelPage';
import { IntelDetailPage } from '@/pages/IntelDetailPage';
import { FavoritesPage } from '@/pages/FavoritesPage';

function PlaceholderPage({ title }: { title: string }) {
    return (
        <div className="p-10">
            <h1 className="text-2xl font-bold mb-4">{title}</h1>
            <p className="text-gray-500">此功能正在开发中...</p>
        </div>
    );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/intel" replace />} />
        <Route path="intel" element={<IntelPage />} />
        <Route path="intel/:id" element={<IntelDetailPage />} />
        <Route path="favorites" element={<FavoritesPage />} />
        <Route path="overview" element={<PlaceholderPage title="数据概览" />} />
        <Route path="settings" element={<PlaceholderPage title="系统设置" />} />
      </Route>
    </Routes>
  );
}

export default App;
