import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Consultation from './pages/Consultation';
import PatientHistory from './pages/PatientHistory';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import DiagnosticResults from './pages/DiagnosticResults';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route — no auth required */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes — redirect to /login if not authenticated */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="consultation" element={<Consultation />} />
            <Route path="history" element={<PatientHistory />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="results" element={<Results />} />
            <Route path="diagnostic-results" element={<DiagnosticResults />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
