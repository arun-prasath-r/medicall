import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { ProtectedRoute } from './routes/ProtectedRoute';

// Public pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DoctorDirectoryPage } from './pages/DoctorDirectoryPage';
import { DoctorDetailPage } from './pages/DoctorDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Patient pages
import { PatientDashboardPage } from './pages/PatientDashboardPage';
import { PatientAppointmentsPage } from './pages/PatientAppointmentsPage';
import { VoiceAssistantPage } from './pages/VoiceAssistantPage';

// Doctor pages
import { DoctorDashboardPage } from './pages/DoctorDashboardPage';

// Admin pages
import { AdminVerificationPage } from './pages/AdminVerificationPage';

export const App = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        {/* Public Routes */}
        <Route index element={<LandingPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="doctors" element={<DoctorDirectoryPage />} />
        <Route path="doctors/:id" element={<DoctorDetailPage />} />

        {/* Patient Protected Routes */}
        <Route
          path="dashboard"
          element={
            <ProtectedRoute allowedRoles={['PATIENT']}>
              <PatientDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="appointments"
          element={
            <ProtectedRoute allowedRoles={['PATIENT']}>
              <PatientAppointmentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="assistant"
          element={
            <ProtectedRoute allowedRoles={['PATIENT']}>
              <VoiceAssistantPage />
            </ProtectedRoute>
          }
        />

        {/* Doctor Protected Routes */}
        <Route
          path="doctor/dashboard"
          element={
            <ProtectedRoute allowedRoles={['DOCTOR']}>
              <DoctorDashboardPage />
            </ProtectedRoute>
          }
        />

        {/* Admin Protected Routes */}
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminVerificationPage />
            </ProtectedRoute>
          }
        />

        {/* 404 Route */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

export default App;

