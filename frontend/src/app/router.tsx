import React from 'react';
import { createBrowserRouter, Outlet, Navigate } from 'react-router-dom';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { Home } from '../routes/Home';
import { Features } from '../routes/Features';
import { About } from '../routes/About';
import { Contact } from '../routes/Contact';
import { Login } from '../routes/Login';
import { Signup } from '../routes/Signup';
import { Dashboard } from '../routes/Dashboard';
import { CropAssistant } from '../routes/CropAssistant';
import { EquipmentDiscovery } from '../routes/EquipmentDiscovery';
import { MyEquipment } from '../routes/MyEquipment';
import { RentalRequests } from '../routes/RentalRequests';
import { WeatherPlanning } from '../routes/WeatherPlanning';
import { CropMarketplace } from '../routes/CropMarketplace';
import { MyCropListings } from '../routes/MyCropListings';
import { MessagesInbox } from '../routes/MessagesInbox';
import { OfflineKnowledge } from '../routes/OfflineKnowledge';
import { SyncQueue } from '../routes/SyncQueue';
import { AdminDashboard } from '../routes/AdminDashboard';
import { ExpertPortal } from '../routes/ExpertPortal';
import { PrivacyPolicy } from '../routes/PrivacyPolicy';
import { TermsOfService } from '../routes/TermsOfService';
import { UserGuide } from '../routes/UserGuide';
import { SupportCenter } from '../routes/SupportCenter';
import { OfflineBanner } from '../features/offline/components/OfflineBanner';
import { NotFound } from '../routes/NotFound';
import { useAuth } from '../features/auth/AuthContext';
import { AccountApprovalLock } from '../features/auth/components/AccountApprovalLock';

const RootLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-canvas text-ink-900 selection:bg-leaf-100 selection:text-forest-900">
      <OfflineBanner />
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

const AppRouteGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-sm text-slate-500">
        লোড হচ্ছে...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const isPrivileged = user.role === 'admin' || user.role === 'moderator';
  if (!isPrivileged && user.nidVerificationStatus !== 'approved') {
    return <AccountApprovalLock user={user} />;
  }

  return <>{children}</>;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'features', element: <Features /> },
      { path: 'about', element: <About /> },
      { path: 'contact', element: <Contact /> },
      { path: 'login', element: <Login /> },
      { path: 'signup', element: <Signup /> },
      { path: 'app', element: <Dashboard /> },
      { path: 'app/guide', element: <UserGuide /> },
      { path: 'app/crop-assistant', element: <AppRouteGuard><CropAssistant /></AppRouteGuard> },
      { path: 'app/equipment', element: <AppRouteGuard><EquipmentDiscovery /></AppRouteGuard> },
      { path: 'app/my-equipment', element: <AppRouteGuard><MyEquipment /></AppRouteGuard> },
      { path: 'app/rental-requests', element: <AppRouteGuard><RentalRequests /></AppRouteGuard> },
      { path: 'app/weather', element: <AppRouteGuard><WeatherPlanning /></AppRouteGuard> },
      { path: 'app/crops', element: <AppRouteGuard><CropMarketplace /></AppRouteGuard> },
      { path: 'app/my-crops', element: <AppRouteGuard><MyCropListings /></AppRouteGuard> },
      { path: 'app/messages', element: <AppRouteGuard><MessagesInbox /></AppRouteGuard> },
      { path: 'app/knowledge', element: <AppRouteGuard><OfflineKnowledge /></AppRouteGuard> },
      { path: 'app/sync-queue', element: <AppRouteGuard><SyncQueue /></AppRouteGuard> },
      { path: 'app/admin', element: <AdminDashboard /> },
      { path: 'app/expert-portal', element: <AppRouteGuard><ExpertPortal /></AppRouteGuard> },
      { path: 'privacy', element: <PrivacyPolicy /> },
      { path: 'terms', element: <TermsOfService /> },
      { path: 'support', element: <SupportCenter /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]);
