import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getMyComplaints } from '../services/complaints'
import ComplaintCard from '../components/ComplaintCard'
import { FunnelIcon, PlusCircleIcon } from '@heroicons/react/24/outline'

export default function UserDashboard() {
  const { user } = useAuth()
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    fetchComplaints()
  }, [statusFilter])

  const fetchComplaints = async () => {
    setLoading(true)
    try {
      const res = await getMyComplaints(1, statusFilter)
      setComplaints(res.data.complaints)
    } catch (err) {
      console.error('Failed to fetch complaints:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredComplaints = complaints.map(c => ({
    ...c,
    id: c._id || c.id,
  }))

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Complaints</h1>
          <p className="text-slate-500">Track and manage your civic issue reports</p>
        </div>
        <Link
          to="/complaints/new"
          className="flex items-center gap-2 bg-trust-blue text-white px-4 py-2 rounded-lg hover:bg-engagement-blue transition-colors"
        >
          <PlusCircleIcon className="h-5 w-5" />
          New Complaint
        </Link>
      </div>

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
          {filteredComplaints.length} complaint{filteredComplaints.length !== 1 ? 's' : ''} found
        </span>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
        </div>
      ) : filteredComplaints.length === 0 ? (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
          <div className="text-slate-400 mb-4">
            <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-800 mb-2">No complaints yet</h3>
          <p className="text-slate-500 mb-4">Start by reporting a civic issue in your area.</p>
          <Link
            to="/complaints/new"
            className="inline-flex items-center gap-2 text-trust-blue hover:text-engagement-blue font-medium"
          >
            <PlusCircleIcon className="h-5 w-5" />
            Submit your first complaint
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredComplaints.map((complaint) => (
            <ComplaintCard key={complaint.id} complaint={complaint} />
          ))}
        </div>
      )}
    </div>
  )
}