import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Trends from './pages/Trends';
import ContentGenerator from './pages/ContentGenerator';
import Analytics from './pages/Analytics';
import BrandVoice from './pages/BrandVoice';
import ContentVault from './pages/ContentVault';

function App() {
  return (
    <Router>
      <div className="App">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/generate" element={<ContentGenerator />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/brand-voice" element={<BrandVoice />} />
            <Route path="/vault" element={<ContentVault />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;