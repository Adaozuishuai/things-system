import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { IntelPage } from '@/pages/IntelPage';
import { IntelDetailPage } from '@/pages/IntelDetailPage';
import { FavoritesPage } from '@/pages/FavoritesPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { SourcesPage } from '@/pages/SourcesPage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import { AuthProvider, useAuth } from '@/context/AuthContext';

function PlaceholderPage({ title }: { title: string }) {
    return (
        <div className="p-10">
            <h1 className="text-2xl font-bold mb-4">{title}</h1>
            <p className="text-gray-500">此功能正在开发中...</p>
        </div>
    );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated, authLoading } = useAuth();
  const location = useLocation();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/intel" replace />} />
          <Route path="intel" element={<RequireAuth><IntelPage /></RequireAuth>} />
          <Route path="intel/:id" element={<RequireAuth><IntelDetailPage /></RequireAuth>} />
          <Route path="favorites" element={<FavoritesPage />} />
          <Route path="sources" element={<RequireAuth><SourcesPage /></RequireAuth>} />
          <Route path="overview" element={<PlaceholderPage title="数据概览" />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
