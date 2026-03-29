import { Link } from 'react-router-dom'
import {
  MapPinIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

const statusConfig = {
  pending: {
    color: 'bg-caution-orange/20 text-caution-orange',
    icon: ClockIcon,
    label: 'Pending',
  },
  in_progress: {
    color: 'bg-engagement-blue/20 text-engagement-blue',
    icon: ArrowPathIcon,
    label: 'In Progress',
  },
  resolved: {
    color: 'bg-growth-green/20 text-growth-green',
    icon: CheckCircleIcon,
    label: 'Resolved',
  },
  escalated: {
    color: 'bg-alert-red/20 text-alert-red',
    icon: ExclamationTriangleIcon,
    label: 'Escalated',
  },
}

const categoryLabels = {
  encroachment: 'Encroachment',
  garbage_dump: 'Garbage Dump',
  road_damage: 'Road Damage',
  water_issue: 'Water Issue',
  drainage: 'Drainage',
  street_light: 'Street Light',
  other: 'Other',
}

export default function ComplaintCard({ complaint }) {
  const status = statusConfig[complaint.status] || statusConfig.pending
  const StatusIcon = status.icon

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="text-xs text-slate-500 font-mono">{complaint.ticket_id}</span>
          <h3 className="font-semibold text-slate-800 mt-1">{complaint.title}</h3>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${status.color}`}>
          <StatusIcon className="h-3 w-3" />
          {status.label}
        </span>
      </div>

      <p className="text-sm text-slate-600 line-clamp-2 mb-3">{complaint.description}</p>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <MapPinIcon className="h-3 w-3" />
            {categoryLabels[complaint.category] || complaint.category}
          </span>
          <span className="flex items-center gap-1">
            <ClockIcon className="h-3 w-3" />
            {formatDate(complaint.created_at)}
          </span>
        </div>

        <Link
          to={`/complaints/${complaint.id}`}
          className="text-trust-blue hover:text-engagement-blue font-medium"
        >
          View Details
        </Link>
      </div>
    </div>
  )
}