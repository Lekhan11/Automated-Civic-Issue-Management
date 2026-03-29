import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import StatusBadge from '../components/StatusBadge'
import api from '../services/api'
import {
  UserGroupIcon,
  ShieldCheckIcon,
  ClipboardDocumentListIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

export default function SuperAdminDashboard() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('users')
  const [users, setUsers] = useState([])
  const [officers, setOfficers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateOfficer, setShowCreateOfficer] = useState(false)
  const [officerForm, setOfficerForm] = useState({ name: '', email: '', password: '', phone: '' })
  const [formError, setFormError] = useState('')
  const [formLoading, setFormLoading] = useState(false)

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'users') {
        const res = await api.get('/api/admin/users')
        setUsers(res.data.users)
      } else if (activeTab === 'officers') {
        const res = await api.get('/api/admin/officers')
        setOfficers(res.data)
      }
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateOfficer = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormLoading(true)

    try {
      await api.post('/api/admin/officers', officerForm)
      setShowCreateOfficer(false)
      setOfficerForm({ name: '', email: '', password: '', phone: '' })
      fetchData()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create officer')
    } finally {
      setFormLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Super Admin Panel</h1>
        <p className="text-slate-500">Manage users, officers, and system settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
            activeTab === 'users'
              ? 'bg-trust-blue text-white'
              : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
          }`}
        >
          <UserGroupIcon className="h-5 w-5" />
          Users
        </button>
        <button
          onClick={() => setActiveTab('officers')}
          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
            activeTab === 'officers'
              ? 'bg-trust-blue text-white'
              : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
          }`}
        >
          <ShieldCheckIcon className="h-5 w-5" />
          Officers
        </button>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200">
          <div className="p-4 border-b border-slate-200">
            <h2 className="font-semibold text-slate-800">All Users</h2>
            <p className="text-sm text-slate-500">{users.length} registered users</p>
          </div>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {users.map((u) => (
                <div key={u.id} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
                      <span className="text-slate-600 font-medium">{u.name.charAt(0).toUpperCase()}</span>
                    </div>
                    <div>
                      <p className="font-medium text-slate-800">{u.name}</p>
                      <p className="text-sm text-slate-500">{u.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                      u.role === 'super_admin'
                        ? 'bg-alert-red/10 text-alert-red'
                        : u.role === 'local_officer'
                        ? 'bg-engagement-blue/10 text-engagement-blue'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {u.role.replace('_', ' ')}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      u.is_active ? 'bg-growth-green/10 text-growth-green' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Officers Tab */}
      {activeTab === 'officers' && (
        <div>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreateOfficer(true)}
              className="flex items-center gap-2 bg-trust-blue text-white px-4 py-2 rounded-lg hover:bg-engagement-blue"
            >
              <PlusIcon className="h-5 w-5" />
              Add Officer
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-200">
              <h2 className="font-semibold text-slate-800">Officers & Admins</h2>
              <p className="text-sm text-slate-500">{officers.length} officers</p>
            </div>
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {officers.map((o) => (
                  <div key={o.id} className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-trust-blue/10 flex items-center justify-center">
                        <ShieldCheckIcon className="h-5 w-5 text-trust-blue" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">{o.name}</p>
                        <p className="text-sm text-slate-500">{o.email}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                      o.role === 'super_admin'
                        ? 'bg-alert-red/10 text-alert-red'
                        : 'bg-engagement-blue/10 text-engagement-blue'
                    }`}>
                      {o.role.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Officer Modal */}
      {showCreateOfficer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-800">Create New Officer</h3>
              <button onClick={() => setShowCreateOfficer(false)} className="text-slate-400 hover:text-slate-600">
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreateOfficer} className="p-4 space-y-4">
              {formError && (
                <div className="p-3 rounded-lg bg-alert-red/10 border border-alert-red/20 text-alert-red text-sm">
                  {formError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                <input
                  type="text"
                  value={officerForm.name}
                  onChange={(e) => setOfficerForm({ ...officerForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  value={officerForm.email}
                  onChange={(e) => setOfficerForm({ ...officerForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  value={officerForm.password}
                  onChange={(e) => setOfficerForm({ ...officerForm, password: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone (Optional)</label>
                <input
                  type="tel"
                  value={officerForm.phone}
                  onChange={(e) => setOfficerForm({ ...officerForm, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateOfficer(false)}
                  className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 px-4 py-2 bg-trust-blue text-white rounded-lg hover:bg-engagement-blue disabled:opacity-50"
                >
                  {formLoading ? 'Creating...' : 'Create Officer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}