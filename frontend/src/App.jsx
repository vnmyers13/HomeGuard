/**
 * OpenDataRemoval Frontend - Root App Component
 *
 * Sprint 2: Authentication + protected routing.
 * Sprint 4: Added Notifications page.
 * Public routes: /login, /register
 * Protected routes: / (dashboard wrapper around Overview), /profile, /household, /brokers, /scans, /notifications
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Overview from './pages/Overview';
import Profile from './pages/Profile';
import Household from './pages/Household';
import Brokers from './pages/Brokers';
import Scans from './pages/Scans';
import Notifications from './pages/Notifications';
import Requests from './pages/Requests';
import Reports from './pages/Reports';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';
import Onboarding from './pages/Onboarding';
import { useAuthStore } from './stores/authStore';

// ----------------------
// Protected Route Guard
// ----------------------
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    // Not authenticated -> redirect to login
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/onboarding" element={<Onboarding />} />

        {/* Protected dashboard routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="profile" element={<Profile />} />
          <Route path="household" element={<Household />} />
          <Route path="brokers" element={<Brokers />} />
          <Route path="scans" element={<Scans />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="requests" element={<Requests />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
          <Route path="health" element={<SystemHealth />} />
        </Route>

        {/* Fallback: redirect to dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}