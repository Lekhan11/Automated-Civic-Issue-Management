import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createComplaint, uploadImages } from '../services/complaints'
import LocationPicker from '../components/LocationPicker'
import {
  PhotoIcon,
  XMarkIcon,
  MapPinIcon,
  DocumentTextIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline'

const categories = [
  { value: 'encroachment', label: 'Encroachment' },
  { value: 'garbage_dump', label: 'Garbage Dump' },
  { value: 'road_damage', label: 'Road Damage' },
  { value: 'water_issue', label: 'Water Issue' },
  { value: 'drainage', label: 'Drainage' },
  { value: 'street_light', label: 'Street Light' },
  { value: 'other', label: 'Other' },
]

export default function ComplaintForm() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [location, setLocation] = useState(null)
  const [selectedFiles, setSelectedFiles] = useState([])

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    address: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!location) {
      setError('Please select a location on the map')
      return
    }

    setLoading(true)

    try {
      const complaintData = {
        ...formData,
        ...location,
      }

      const res = await createComplaint(complaintData)
      const complaintId = res.data.complaint.id

      if (selectedFiles.length > 0) {
        await uploadImages(complaintId, selectedFiles)
      }

      navigate(`/complaints/${complaintId}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit complaint')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files)
    setSelectedFiles([...selectedFiles, ...files])
  }

  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index))
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

      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Report a New Issue</h1>
        <p className="text-slate-500 mb-6">Help us improve your community by reporting civic issues.</p>

        {error && (
          <div className="mb-4 p-4 rounded-lg bg-alert-red/10 border border-alert-red/20 text-alert-red text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
              placeholder="Brief description of the issue"
              required
              minLength={5}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Category</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
              required
            >
              <option value="">Select category</option>
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none resize-none"
              rows={4}
              placeholder="Provide detailed information about the issue..."
              required
              minLength={10}
            />
          </div>

          <LocationPicker value={location} onChange={setLocation} />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Address (Optional)</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
              placeholder="123 Main Street, City"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Photos</label>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
              <PhotoIcon className="mx-auto h-10 w-10 text-slate-400" />
              <p className="text-sm text-slate-500 mt-2">
                Click to upload or drag and drop
              </p>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="mt-3 inline-block px-4 py-2 bg-trust-blue text-white rounded-lg text-sm hover:bg-engagement-blue cursor-pointer"
              >
                Choose files
              </label>
            </div>

            {selectedFiles.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="relative inline-flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-full text-sm"
                  >
                    <span className="truncate max-w-32">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-slate-400 hover:text-alert-red"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-trust-blue text-white py-3 rounded-lg font-medium hover:bg-engagement-blue transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Submitting...' : 'Submit Complaint'}
          </button>
        </form>
      </div>
    </div>
  )
}