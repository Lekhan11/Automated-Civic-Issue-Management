import api from './api'

export const getMyComplaints = (page = 1, status) => {
  const params = new URLSearchParams({ page })
  if (status) params.append('status', status)
  return api.get(`/api/complaints/my?${params}`)
}

export const getAssignedComplaints = (page = 1, status) => {
  const params = new URLSearchParams({ page })
  if (status) params.append('status', status)
  return api.get(`/api/complaints/assigned?${params}`)
}

export const getComplaint = (id) => api.get(`/api/complaints/${id}`)

export const createComplaint = (data) => api.post('/api/complaints/', data)

export const updateComplaintStatus = (id, data) => api.put(`/api/complaints/${id}`, data)

export const uploadImages = (complaintId, files) => {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  return api.post(`/api/complaints/${complaintId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getNearbyComplaints = (lon, lat, radius = 5) =>
  api.get(`/api/complaints/nearby?longitude=${lon}&latitude=${lat}&radius=${radius}`)

export const getAllComplaints = (params) => {
  const query = new URLSearchParams(params).toString()
  return api.get(`/api/admin/complaints?${query}`)
}

export const getDashboardStats = () => api.get('/api/admin/dashboard')

export const getCategoryStats = () => api.get('/api/admin/stats/categories')

export const assignComplaint = (complaintId, officerId) =>
  api.put(`/api/admin/complaints/${complaintId}/assign?officer_id=${officerId}`)

export const getOfficers = () => api.get('/api/admin/officers')