import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getComplaint } from '../services/complaints'
import StatusBadge from '../components/StatusBadge'
import {
  ArrowLeftIcon,
  MapPinIcon,
  CalendarIcon,
  UserIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { MapContainer, TileLayer, Marker } from 'react-leaflet'

const DEFAULT_POS = [12.9716, 77.5946]

const categoryLabels = {
  encroachment: 'Encroachment',
  garbage_dump: 'Garbage Dump',
  road_damage: 'Road Damage',
  water_issue: 'Water Issue',
  drainage: 'Drainage',
  street_light: 'Street Light',
  other: 'Other',
}

export default function ComplaintDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [complaint, setComplaint] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchComplaint()
  }, [id])

  const fetchComplaint = async () => {
    setLoading(true)
    try {
      const res = await getComplaint(id)
      setComplaint(res.data)
    } catch (err) {
      console.error('Failed to fetch complaint:', err)
    } finally {
      setLoading(false)
    }
  }

  // Safely extract coordinates with defaults
  const mapPosition = useMemo(() => {
    if (!complaint?.location?.coordinates) return DEFAULT_POS
    const [lon, lat] = complaint.location.coordinates
    if (typeof lat === 'number' && typeof lon === 'number') {
      return [lat, lon]
    }
    return DEFAULT_POS
  }, [complaint])

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-IN', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
      </div>
    )
  }

  if (!complaint) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Complaint not found.</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-trust-blue hover:underline">Go back</button>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-6"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back
      </button>

      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <span className="text-sm text-slate-500 font-mono">{complaint.ticket_id}</span>
              <h1 className="text-2xl font-bold text-slate-800 mt-1">{complaint.title}</h1>
            </div>
            <StatusBadge status={complaint.status} />
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-slate-500">
            <span className="flex items-center gap-1.5">
              <ClipboardDocumentListIcon className="h-4 w-4" />
              {categoryLabels[complaint.category] || complaint.category}
            </span>
            <span className="flex items-center gap-1.5">
              <UserIcon className="h-4 w-4" />
              {complaint.submitted_by_name || 'You'}
            </span>
            <span className="flex items-center gap-1.5">
              <CalendarIcon className="h-4 w-4" />
              {formatDate(complaint.created_at)}
            </span>
          </div>

          {complaint.escalated && (
            <div className="mt-4 p-3 rounded-lg bg-alert-red/10 border border-alert-red/20 text-alert-red text-sm flex items-center gap-2">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              This complaint has been escalated to higher authority.
              {complaint.escalated_at && <span>Escalated on: {formatDate(complaint.escalated_at)}</span>}
            </div>
          )}
        </div>

        {/* Description */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-3">Description</h2>
          <p className="text-slate-600 whitespace-pre-line">{complaint.description}</p>
        </div>

        {/* Location */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
            <MapPinIcon className="h-5 w-5" />
            Location
          </h2>
          {complaint.address && <p className="text-slate-600 text-sm mb-3">{complaint.address}</p>}
          <div className="h-64 rounded-lg overflow-hidden border border-slate-300">
            <MapContainer center={mapPosition} zoom={14} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={mapPosition} />
            </MapContainer>
          </div>
        </div>

        {/* Images */}
        {complaint.images && complaint.images.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            <h2 className="font-semibold text-slate-800 mb-3">Photos</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {complaint.images.map((url, i) => (
                <img
                  key={i}
                  src={url}
                  alt={`Complaint photo ${i + 1}`}
                  className="w-full h-40 object-cover rounded-lg border border-slate-200"
                />
              ))}
            </div>
          </div>
        )}

        {/* Resolution */}
        {complaint.status === 'resolved' && (
          <div className="bg-growth-green/5 rounded-lg border border-growth-green/20 p-6">
            <h2 className="font-semibold text-growth-green flex items-center gap-2 mb-3">
              <CheckCircleIcon className="h-5 w-5" />
              Resolution
            </h2>
            {complaint.resolution_notes && (
              <p className="text-slate-700 mb-3">{complaint.resolution_notes}</p>
            )}
            {complaint.resolved_at && (
              <p className="text-sm text-slate-500">
                Resolved on: {formatDate(complaint.resolved_at)}
              </p>
            )}
            {complaint.resolution_images && complaint.resolution_images.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-3">
                {complaint.resolution_images.map((url, i) => (
                  <img
                    key={i}
                    src={url}
                    alt={`Resolution photo ${i + 1}`}
                    className="w-full h-40 object-cover rounded-lg border border-slate-200"
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timeline */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Timeline</h2>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className="w-3 h-3 rounded-full bg-trust-blue mt-1.5"></div>
                <div className="w-0.5 h-full bg-slate-200"></div>
              </div>
              <div className="pb-4">
                <p className="text-sm font-medium text-slate-800">Complaint Submitted</p>
                <p className="text-xs text-slate-500">{formatDate(complaint.created_at)}</p>
              </div>
            </div>

            {complaint.assigned_to && (
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-engagement-blue mt-1.5"></div>
                  <div className="w-0.5 h-full bg-slate-200"></div>
                </div>
                <div className="pb-4">
                  <p className="text-sm font-medium text-slate-800">Assigned to Officer</p>
                  <p className="text-xs text-slate-500">{complaint.assigned_to_name || 'Officer'}</p>
                </div>
              </div>
            )}

            {complaint.escalated && (
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-alert-red mt-1.5"></div>
                </div>
                <div>
                  <p className="text-sm font-medium text-alert-red">Escalated</p>
                  <p className="text-xs text-slate-500">
                    {complaint.escalated_at ? formatDate(complaint.escalated_at) : 'N/A'}
                  </p>
                </div>
              </div>
            )}

            {complaint.status === 'resolved' && (
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-growth-green mt-1.5"></div>
                </div>
                <div>
                  <p className="text-sm font-medium text-growth-green">Resolved</p>
                  <p className="text-xs text-slate-500">
                    {complaint.resolved_at ? formatDate(complaint.resolved_at) : 'N/A'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}