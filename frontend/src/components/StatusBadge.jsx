import {
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

const statusConfig = {
  pending: {
    color: 'bg-caution-orange/20 text-caution-orange border-caution-orange/30',
    icon: ClockIcon,
    label: 'Pending',
  },
  in_progress: {
    color: 'bg-engagement-blue/20 text-engagement-blue border-engagement-blue/30',
    icon: ArrowPathIcon,
    label: 'In Progress',
  },
  resolved: {
    color: 'bg-growth-green/20 text-growth-green border-growth-green/30',
    icon: CheckCircleIcon,
    label: 'Resolved',
  },
  escalated: {
    color: 'bg-alert-red/20 text-alert-red border-alert-red/30',
    icon: ExclamationTriangleIcon,
    label: 'Escalated',
  },
}

export default function StatusBadge({ status }) {
  const config = statusConfig[status] || statusConfig.pending
  const Icon = config.icon

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${config.color}`}>
      <Icon className="h-4 w-4" />
      {config.label}
    </span>
  )
}