import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAssignedComplaints } from '../services/complaints'
import StatusBadge from '../components/StatusBadge'
import {
  FunnelIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

export default function OfficerDashboard() {
  const { user } = useAuth()
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [stats, setStats] = useState({ total: 0, pending: 0, inProgress: 0, resolved: 0 })

  useEffect(() => {
    fetchComplaints()
  }, [statusFilter])

  const fetchComplaints = async () => {
    setLoading(true)
    try {
      const res = await getAssignedComplaints(1, statusFilter)
      const complaintList = res.data.complaints.map(c => ({ ...c, id: c._id || c.id }))
      setComplaints(complaintList)

      // Calculate stats
      setStats({
        total: complaintList.length,
        pending: complaintList.filter(c => c.status === 'pending').length,
        inProgress: complaintList.filter(c => c.status === 'in_progress').length,
        resolved: complaintList.filter(c => c.status === 'resolved').length,
      })
    } catch (err) {
      console.error('Failed to fetch complaints:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">
          {user?.role === 'zonal_officer' ? 'My Zone Complaints' : user?.role === 'district_officer' ? 'All District Complaints' : 'My Area Complaints'}
        </h1>
        <p className="text-slate-500">
          {user?.role === 'zonal_officer' ? `Zone: ${user?.assigned_zone || 'N/A'}` : user?.role === 'district_officer' ? 'Manage all complaints in the district' : 'Manage complaints assigned to you'}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-engagement-blue/10">
              <ClipboardDocumentListIcon className="h-5 w-5 text-engagement-blue" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total</p>
              <p className="text-xl font-bold text-slate-800">{stats.total}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-caution-orange/10">
              <ClockIcon className="h-5 w-5 text-caution-orange" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Pending</p>
              <p className="text-xl font-bold text-slate-800">{stats.pending}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-trust-blue/10">
              <ArrowPathIcon className="h-5 w-5 text-trust-blue" />
            </div>
            <div>
              <p className="text-xs text-slate-500">In Progress</p>
              <p className="text-xl font-bold text-slate-800">{stats.inProgress}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-growth-green/10">
              <CheckCircleIcon className="h-5 w-5 text-growth-green" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Resolved</p>
              <p className="text-xl font-bold text-slate-800">{stats.resolved}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative">
          <FunnelIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>
        <span className="text-sm text-slate-500">
          {complaints.length} complaint{complaints.length !== 1 ? 's' : ''} assigned
        </span>
      </div>

      {/* Complaints List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
        </div>
      ) : complaints.length === 0 ? (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
          <ClipboardDocumentListIcon className="mx-auto h-16 w-16 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">No complaints assigned</h3>
          <p className="text-slate-500">You don't have any complaints assigned to you yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {complaints.map((complaint) => (
            <div key={complaint.id} className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-500 font-mono">{complaint.ticket_id}</span>
                    <StatusBadge status={complaint.status} />
                  </div>
                  <h3 className="font-semibold text-slate-800">{complaint.title}</h3>
                  {complaint.district && (
                    <span className="text-xs text-trust-blue mr-2">{complaint.district}</span>
                  )}
                  {complaint.zone && (
                    <span className="text-xs text-slate-400 mr-2">Zone: {complaint.zone}</span>
                  )}
                  {complaint.ward_number && (
                    <span className="text-xs text-slate-400">Ward #{complaint.ward_number}</span>
                  )}
                  <p className="text-sm text-slate-600 mt-1 line-clamp-2">{complaint.description}</p>
                  <p className="text-xs text-slate-400 mt-2">
                    Created: {new Date(complaint.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Link
                  to={`/complaints/${complaint.id}`}
                  className="ml-4 px-3 py-1.5 bg-trust-blue text-white text-sm rounded-lg hover:bg-engagement-blue"
                >
                  View
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}