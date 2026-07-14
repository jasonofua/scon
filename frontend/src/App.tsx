// import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Chat from './components/Chat/Chat';
import SearchPage from './components/Search/SearchPage';
import DocumentsPage from './components/Documents/DocumentsPage';
import ConstitutionPage from './components/Constitution/ConstitutionPage';
import CasesPage from './components/Cases/CasesPage';
import JudgesPage from './components/Judges/JudgesPage';
import KioskMode from './components/Kiosk/KioskMode';
import KioskLayout from './components/Kiosk/KioskLayout';

function AppContent() {
  const location = useLocation();

  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case '/search':
        return 'Search - SCONIA';
      case '/documents':
        return 'Documents - SCONIA';
      case '/constitution':
        return 'Constitution - SCONIA';
      case '/cases':
        return 'Cases - SCONIA';
      case '/judges':
        return 'Judges - SCONIA';
      case '/kiosk':
        return 'Kiosk Mode - SCONIA';
      default:
        return 'SCONIA';
    }
  };

  // Check if we're in kiosk mode
  if (location.pathname === '/kiosk') {
    return (
      <KioskLayout showSettings={true}>
        <KioskMode />
      </KioskLayout>
    );
  }

  return (
    <Layout title={getPageTitle(location.pathname)} currentPath={location.pathname}>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/constitution" element={<ConstitutionPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/judges" element={<JudgesPage />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <AppContent />

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#374151',
            boxShadow: '0 10px 40px -10px rgba(0, 0, 0, 0.15)',
            border: '1px solid #e5e7eb',
          },
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </Router>
  );
}

export default App;
