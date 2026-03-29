import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import UserDashboard from './pages/UserDashboard'
import AdminDashboard from './pages/AdminDashboard'
import OfficerDashboard from './pages/OfficerDashboard'
import SuperAdminDashboard from './pages/SuperAdminDashboard'
import ComplaintForm from './pages/ComplaintForm'
import ComplaintDetail from './pages/ComplaintDetail'
import Layout from './components/Layout'

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" />
  }

  return children
}

// Redirect based on role
function RoleBasedRedirect() {
  const { user } = useAuth()

  if (!user) return <Navigate to="/login" />

  switch (user.role) {
    case 'super_admin':
      return <Navigate to="/super-admin" />
    case 'local_officer':
      return <Navigate to="/officer" />
    default:
      return <Navigate to="/dashboard" />
  }
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/" />} />

      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        {/* Role-based redirect */}
        <Route index element={<RoleBasedRedirect />} />

        {/* User routes */}
        <Route path="dashboard" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
        <Route path="complaints/new" element={<ProtectedRoute><ComplaintForm /></ProtectedRoute>} />
        <Route path="complaints/:id" element={<ProtectedRoute><ComplaintDetail /></ProtectedRoute>} />

        {/* Officer routes */}
        <Route
          path="officer"
          element={
            <ProtectedRoute allowedRoles={['local_officer', 'super_admin']}>
              <OfficerDashboard />
            </ProtectedRoute>
          }
        />

        {/* Admin dashboard (complaints overview) */}
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['local_officer', 'super_admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Super Admin routes */}
        <Route
          path="super-admin"
          element={
            <ProtectedRoute allowedRoles={['super_admin']}>
              <SuperAdminDashboard />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}