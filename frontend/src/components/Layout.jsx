import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  HomeIcon,
  PlusCircleIcon,
  ClipboardDocumentListIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  const isAdmin = user?.role === 'local_officer' || user?.role === 'super_admin'
  const isSuperAdmin = user?.role === 'super_admin'

  // Get dashboard link based on role
  const getDashboardLink = () => {
    switch (user?.role) {
      case 'super_admin':
        return '/super-admin'
      case 'local_officer':
        return '/officer'
      default:
        return '/dashboard'
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <Link to={getDashboardLink()} className="flex items-center gap-2">
                <ClipboardDocumentListIcon className="h-8 w-8 text-trust-blue" />
                <span className="font-bold text-xl text-slate-800">CivicFix</span>
              </Link>

              <nav className="hidden md:flex items-center gap-1">
                {/* User nav */}
                {user?.role === 'user' && (
                  <>
                    <Link
                      to="/dashboard"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/dashboard') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <HomeIcon className="h-4 w-4" />
                      My Complaints
                    </Link>
                    <Link
                      to="/complaints/new"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/complaints/new') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <PlusCircleIcon className="h-4 w-4" />
                      New Complaint
                    </Link>
                  </>
                )}

                {/* Officer nav */}
                {user?.role === 'local_officer' && (
                  <>
                    <Link
                      to="/officer"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/officer') && !isActive('/officer/') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <ClipboardDocumentListIcon className="h-4 w-4" />
                      My Assigned
                    </Link>
                    <Link
                      to="/admin"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/admin') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <ChartBarIcon className="h-4 w-4" />
                      All Complaints
                    </Link>
                    <Link
                      to="/complaints/new"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/complaints/new') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <PlusCircleIcon className="h-4 w-4" />
                      New Complaint
                    </Link>
                  </>
                )}

                {/* Super Admin nav */}
                {user?.role === 'super_admin' && (
                  <>
                    <Link
                      to="/super-admin"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/super-admin') && location.pathname === '/super-admin' ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <UserGroupIcon className="h-4 w-4" />
                      Users
                    </Link>
                    <Link
                      to="/admin"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/admin') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <ChartBarIcon className="h-4 w-4" />
                      Dashboard
                    </Link>
                    <Link
                      to="/officer"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/officer') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <ShieldCheckIcon className="h-4 w-4" />
                      My Assigned
                    </Link>
                    <Link
                      to="/complaints/new"
                      className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
                        isActive('/complaints/new') ? 'bg-trust-blue text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <PlusCircleIcon className="h-4 w-4" />
                      New Complaint
                    </Link>
                  </>
                )}
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <UserCircleIcon className="h-5 w-5" />
                <span>{user?.name}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full capitalize ${
                  user?.role === 'super_admin'
                    ? 'bg-alert-red/10 text-alert-red'
                    : user?.role === 'local_officer'
                    ? 'bg-engagement-blue/10 text-engagement-blue'
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {user?.role?.replace('_', ' ')}
                </span>
              </div>
              <button
                onClick={logout}
                className="p-2 text-slate-500 hover:text-alert-red hover:bg-alert-red/10 rounded-lg"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}