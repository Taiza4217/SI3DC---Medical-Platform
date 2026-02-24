import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import JoinUs from './pages/JoinUs';
import Login from './pages/Login';
import DashboardPage from './pages/DashboardPage';
import EmergencyModePage from './pages/EmergencyModePage';
import SearchPatientPage from './pages/SearchPatientPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import UploadPage from './pages/UploadPage';
import ScrollToTop from './components/ScrollToTop';

function Layout() {
  const location = useLocation();
  const isAuthPage = ['/login', '/dashboard', '/emergency', '/search-patient', '/history', '/settings', '/upload'].includes(location.pathname);

  return (
    <div className="flex flex-col min-h-screen font-sans text-slate-900 antialiased">
      {!isAuthPage && <Header />}
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/join-us" element={<JoinUs />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/emergency" element={<EmergencyModePage />} />
          <Route path="/search-patient" element={<SearchPatientPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/upload" element={<UploadPage />} />
        </Routes>
      </main>
      {!isAuthPage && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <ScrollToTop />
      <Layout />
    </Router>
  );
}
