import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import UserDashboard from './pages/UserDashboard'
import AdminDashboard from './pages/AdminDashboard'
import OfficerDashboard from './pages/OfficerDashboard'
import DistrictOfficerDashboard from './pages/DistrictOfficerDashboard'
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
    case 'district_officer':
      return <Navigate to="/district-officer" />
    case 'zonal_officer':
      return <Navigate to="/officer" />
    case 'local_officer':
      return <Navigate to="/officer" />
    default:
      return <Navigate to="/dashboard" />
  }
}

const OFFICER_ROLES = ['local_officer', 'zonal_officer', 'district_officer']

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/" />} />

      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<RoleBasedRedirect />} />

        {/* User routes */}
        <Route path="dashboard" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
        <Route path="complaints/new" element={<ProtectedRoute><ComplaintForm /></ProtectedRoute>} />
        <Route path="complaints/:id" element={<ProtectedRoute><ComplaintDetail /></ProtectedRoute>} />

        {/* Officer routes (local + zonal) */}
        <Route
          path="officer"
          element={
            <ProtectedRoute allowedRoles={['local_officer', 'zonal_officer', 'district_officer']}>
              <OfficerDashboard />
            </ProtectedRoute>
          }
        />

        {/* Admin dashboard — district_officer only */}
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['district_officer']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* District Officer routes */}
        <Route
          path="district-officer"
          element={
            <ProtectedRoute allowedRoles={['district_officer']}>
              <DistrictOfficerDashboard />
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
