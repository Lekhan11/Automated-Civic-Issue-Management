import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { getAreas, createArea, getZones, getDistricts } from '../services/complaints'
import api from '../services/api'
import {
  UserGroupIcon,
  ShieldCheckIcon,
  PlusIcon,
  XMarkIcon,
  MapIcon,
} from '@heroicons/react/24/outline'

export default function DistrictOfficerDashboard() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('users')
  const [users, setUsers] = useState([])
  const [officers, setOfficers] = useState([])
  const [areas, setAreas] = useState([])
  const [zones, setZones] = useState([])
  const [districts, setDistricts] = useState([])
  const [selectedDistrict, setSelectedDistrict] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreateOfficer, setShowCreateOfficer] = useState(false)
  const [showCreateArea, setShowCreateArea] = useState(false)
  const [officerForm, setOfficerForm] = useState({
    name: '', email: '', password: '', phone: '', role: 'local_officer',
    assigned_area_id: '', assigned_zone: '',
  })
  const [areaForm, setAreaForm] = useState({ name: '', ward_number: '', zone: '', district: '' })
  const [formError, setFormError] = useState('')
  const [formLoading, setFormLoading] = useState(false)

  useEffect(() => {
    fetchData()
  }, [activeTab, selectedDistrict])

  useEffect(() => {
    if (!districts.length) {
      getDistricts().then(res => setDistricts(res.data.districts || []))
    }
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'users') {
        const res = await api.get('/api/admin/users')
        setUsers(res.data.users)
      } else if (activeTab === 'officers') {
        const [officersRes, zonesRes] = await Promise.all([
          api.get('/api/admin/officers'),
          getZones(),
        ])
        setOfficers(officersRes.data)
        setZones(zonesRes.data.zones || [])
      } else if (activeTab === 'areas') {
        const [areasRes, districtsRes] = await Promise.all([
          getAreas(selectedDistrict ? { district: selectedDistrict } : undefined),
          getDistricts(),
        ])
        setAreas(areasRes.data.areas || [])
        if (!districts.length) setDistricts(districtsRes.data.districts || [])
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
      const data = { ...officerForm }
      // Only send area/zone fields relevant to the role
      if (data.role !== 'local_officer') delete data.assigned_area_id
      if (data.role !== 'zonal_officer') delete data.assigned_zone
      if (!data.assigned_area_id) delete data.assigned_area_id
      if (!data.assigned_zone) delete data.assigned_zone

      await api.post('/api/admin/officers', data)
      setShowCreateOfficer(false)
      setOfficerForm({ name: '', email: '', password: '', phone: '', role: 'local_officer', assigned_area_id: '', assigned_zone: '' })
      fetchData()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create officer')
    } finally {
      setFormLoading(false)
    }
  }

  const fetchZonesForDistrict = async (district) => {
    if (!district) { setZones([]); return }
    const res = await getZones(district)
    setZones(res.data.zones || [])
  }

  const handleCreateArea = async (e) => {
    e.preventDefault()
    setFormError('')
    setFormLoading(true)
    try {
      await createArea({ ...areaForm, ward_number: parseInt(areaForm.ward_number) })
      setShowCreateArea(false)
      setAreaForm({ name: '', ward_number: '', zone: '', district: '' })
      fetchData()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create area')
    } finally {
      setFormLoading(false)
    }
  }

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'district_officer': return 'bg-alert-red/10 text-alert-red'
      case 'zonal_officer': return 'bg-caution-orange/10 text-caution-orange'
      case 'local_officer': return 'bg-engagement-blue/10 text-engagement-blue'
      default: return 'bg-slate-100 text-slate-600'
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">District Officer Panel</h1>
        <p className="text-slate-500">Manage users, officers, areas, and system settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button onClick={() => setActiveTab('users')} className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${activeTab === 'users' ? 'bg-trust-blue text-white' : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'}`}>
          <UserGroupIcon className="h-5 w-5" />
          Users
        </button>
        <button onClick={() => setActiveTab('officers')} className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${activeTab === 'officers' ? 'bg-trust-blue text-white' : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'}`}>
          <ShieldCheckIcon className="h-5 w-5" />
          Officers
        </button>
        <button onClick={() => setActiveTab('areas')} className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${activeTab === 'areas' ? 'bg-trust-blue text-white' : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'}`}>
          <MapIcon className="h-5 w-5" />
          Areas
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
                    <span className={`px-2 py-1 text-xs rounded-full capitalize ${getRoleBadgeColor(u.role)}`}>
                      {u.role.replace('_', ' ')}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full ${u.is_active ? 'bg-growth-green/10 text-growth-green' : 'bg-slate-100 text-slate-500'}`}>
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
            <button onClick={() => setShowCreateOfficer(true)} className="flex items-center gap-2 bg-trust-blue text-white px-4 py-2 rounded-lg hover:bg-engagement-blue">
              <PlusIcon className="h-5 w-5" />
              Add Officer
            </button>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-200">
              <h2 className="font-semibold text-slate-800">All Officers</h2>
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
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs rounded-full capitalize ${getRoleBadgeColor(o.role)}`}>
                        {o.role.replace('_', ' ')}
                      </span>
                      {o.assigned_zone && (
                        <span className="px-2 py-1 text-xs rounded-full bg-slate-100 text-slate-600">
                          Zone: {o.assigned_zone}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Areas Tab */}
      {activeTab === 'areas' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
            >
              <option value="">All Districts</option>
              {districts.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            <button onClick={() => setShowCreateArea(true)} className="flex items-center gap-2 bg-trust-blue text-white px-4 py-2 rounded-lg hover:bg-engagement-blue">
              <PlusIcon className="h-5 w-5" />
              Add Area
            </button>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-200">
              <h2 className="font-semibold text-slate-800">Areas & Wards</h2>
              <p className="text-sm text-slate-500">{areas.length} areas</p>
            </div>
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trust-blue"></div>
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {areas.map((a) => (
                  <div key={a.id} className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-growth-green/10 flex items-center justify-center">
                        <MapIcon className="h-5 w-5 text-growth-green" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">{a.name}</p>
                        <p className="text-sm text-slate-500">{a.district} — Zone: {a.zone}</p>
                      </div>
                    </div>
                    <span className="px-2 py-1 text-xs rounded-full bg-slate-100 text-slate-600">
                      {a.zone}
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
                <div className="p-3 rounded-lg bg-alert-red/10 border border-alert-red/20 text-alert-red text-sm">{formError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                <select
                  value={officerForm.role}
                  onChange={(e) => setOfficerForm({ ...officerForm, role: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                  required
                >
                  <option value="local_officer">Local Officer (Ward)</option>
                  <option value="zonal_officer">Zonal Officer (Zone)</option>
                  <option value="district_officer">District Officer</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                <input type="text" value={officerForm.name} onChange={(e) => setOfficerForm({ ...officerForm, name: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input type="email" value={officerForm.email} onChange={(e) => setOfficerForm({ ...officerForm, email: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input type="password" value={officerForm.password} onChange={(e) => setOfficerForm({ ...officerForm, password: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" required minLength={6} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone (Optional)</label>
                <input type="tel" value={officerForm.phone} onChange={(e) => setOfficerForm({ ...officerForm, phone: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" />
              </div>
              {officerForm.role === 'local_officer' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Assigned Area</label>
                  <select
                    value={officerForm.assigned_area_id}
                    onChange={(e) => setOfficerForm({ ...officerForm, assigned_area_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                  >
                    <option value="">Select area...</option>
                    {areas.map((a) => (
                      <option key={a.id} value={a.id}>{a.name} ({a.district} — {a.zone})</option>
                    ))}
                  </select>
                </div>
              )}
              {officerForm.role === 'zonal_officer' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Assigned Zone</label>
                  <select
                    value={officerForm.assigned_zone}
                    onChange={(e) => setOfficerForm({ ...officerForm, assigned_zone: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none"
                    required
                  >
                    <option value="">Select zone...</option>
                    {zones.map((z) => (
                      <option key={z} value={z}>{z}</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreateOfficer(false)} className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={formLoading} className="flex-1 px-4 py-2 bg-trust-blue text-white rounded-lg hover:bg-engagement-blue disabled:opacity-50">
                  {formLoading ? 'Creating...' : 'Create Officer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Area Modal */}
      {showCreateArea && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-800">Add New Area</h3>
              <button onClick={() => setShowCreateArea(false)} className="text-slate-400 hover:text-slate-600">
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreateArea} className="p-4 space-y-4">
              {formError && (
                <div className="p-3 rounded-lg bg-alert-red/10 border border-alert-red/20 text-alert-red text-sm">{formError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Area Name</label>
                <input type="text" value={areaForm.name} onChange={(e) => setAreaForm({ ...areaForm, name: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" placeholder="e.g., Pallipalayam" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Ward Number</label>
                <input type="number" value={areaForm.ward_number} onChange={(e) => setAreaForm({ ...areaForm, ward_number: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" placeholder="e.g., 1" required min="1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">District</label>
                <select value={areaForm.district} onChange={(e) => { setAreaForm({ ...areaForm, district: e.target.value }); if (e.target.value) { fetchZonesForDistrict(e.target.value) } }} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" required>
                  <option value="">Select district...</option>
                  {districts.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Zone (Taluk)</label>
                <select value={areaForm.zone} onChange={(e) => setAreaForm({ ...areaForm, zone: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none" required>
                  <option value="">Select zone...</option>
                  {zones.map((z) => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                  <option value="__new">Add new zone...</option>
                </select>
                {areaForm.zone === '__new' && (
                  <input type="text" placeholder="Enter zone name" onChange={(e) => setAreaForm({ ...areaForm, zone: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none mt-2" />
                )}
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreateArea(false)} className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={formLoading} className="flex-1 px-4 py-2 bg-trust-blue text-white rounded-lg hover:bg-engagement-blue disabled:opacity-50">
                  {formLoading ? 'Creating...' : 'Add Area'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
