import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getDashboardStats, getCategoryStats, getAllComplaints, getOfficers, assignComplaint, updateComplaintStatus } from '../services/complaints'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import {
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  UserGroupIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const COLORS = ['#caution-orange', '#engagement-blue', '#growth-green', '#alert-red']

export default function AdminDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [categoryStats, setCategoryStats] = useState([])
  const [complaints, setComplaints] = useState([])
  const [officers, setOfficers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedComplaint, setSelectedComplaint] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    fetchData()
  }, [statusFilter])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsRes, catRes, complaintsRes, officersRes] = await Promise.all([
        getDashboardStats(),
        getCategoryStats(),
        getAllComplaints({ page: 1, limit: 10, status: statusFilter }),
        getOfficers(),
      ])
      setStats(statsRes.data)
      setCategoryStats(catRes.data)
      setComplaints(complaintsRes.data.complaints)
      setOfficers(officersRes.data)
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAssign = async (complaintId, officerId) => {
    try {
      await assignComplaint(complaintId, officerId)
      fetchData()
    } catch (err) {
      alert('Failed to assign complaint')
    }
  }

  const handleStatusUpdate = async (complaintId, status) => {
    try {
      await updateComplaintStatus(complaintId, { status })
      fetchData()
    } catch (err) {
      alert('Failed to update status')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
      </div>
    )
  }

  const pieData = categoryStats.map(c => ({ name: c.category, value: c.count }))

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Admin Dashboard</h1>
        <p className="text-slate-500">Overview of civic complaints and resolution status</p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <StatCard title="Total" value={stats.total_complaints} icon={DocumentTextIcon} color="blue" />
          <StatCard title="Pending" value={stats.pending} icon={ClockIcon} color="orange" />
          <StatCard title="In Progress" value={stats.in_progress} icon={ArrowPathIcon} color="blue" />
          <StatCard title="Resolved" value={stats.resolved} icon={CheckCircleIcon} color="green" />
          <StatCard title="Escalated" value={stats.escalated} icon={ExclamationTriangleIcon} color="red" />
          <StatCard title="Resolution Rate" value={`${stats.resolution_rate}%`} color="green" subtitle={stats.avg_resolution_time_hours ? `Avg: ${stats.avg_resolution_time_hours}h` : null} />
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Complaints by Category</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={['#f59e0b', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#ec4899'][index % 6]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-center py-12">No data available</p>
          )}
        </div>

        {/* Complaints List */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-semibold text-slate-800">Recent Complaints</h2>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="escalated">Escalated</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                  <th className="pb-2">Ticket</th>
                  <th className="pb-2">Title</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Assigned</th>
                  <th className="pb-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map((c) => (
                  <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 text-sm font-mono text-slate-600">{c.ticket_id}</td>
                    <td className="py-3">
                      <Link to={`/complaints/${c.id}`} className="text-sm text-trust-blue hover:underline">
                        {c.title.substring(0, 25)}...
                      </Link>
                    </td>
                    <td className="py-3"><StatusBadge status={c.status} /></td>
                    <td className="py-3 text-sm text-slate-600">{c.assigned_to_name || 'Unassigned'}</td>
                    <td className="py-3">
                      <select
                        value={c.assigned_to || ''}
                        onChange={(e) => handleAssign(c.id, e.target.value)}
                        className="text-xs px-2 py-1 border border-slate-300 rounded"
                      >
                        <option value="">Assign to...</option>
                        {officers.map((o) => (
                          <option key={o.id} value={o.id}>{o.name}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Officers Section */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <UserGroupIcon className="h-5 w-5" />
          Officers
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {officers.map((officer) => (
            <div key={officer.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <div className="w-10 h-10 rounded-full bg-trust-blue/10 flex items-center justify-center">
                <span className="text-trust-blue font-medium">{officer.name.charAt(0)}</span>
              </div>
              <div>
                <p className="font-medium text-slate-800">{officer.name}</p>
                <p className="text-xs text-slate-500 capitalize">{officer.role.replace('_', ' ')}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}