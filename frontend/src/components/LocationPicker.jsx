import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet'
import { MapPinIcon } from '@heroicons/react/24/outline'
import '../utils/leaflet-icons'

const DEFAULT_POS = [12.9716, 77.5946]

function MapEvents({ onLocationSelect }) {
  useMapEvents({
    click: (e) => {
      if (e?.latlng) {
        onLocationSelect(e.latlng.lat, e.latlng.lng)
      }
    },
  })
  return null
}

function MapController({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.setView(center, 13)
    }
  }, [center, map])
  return null
}

export default function LocationPicker({ value, onChange }) {
  const [position, setPosition] = useState(
    value?.latitude && value?.longitude
      ? [value.latitude, value.longitude]
      : DEFAULT_POS
  )

  useEffect(() => {
    if (value?.latitude && value?.longitude) {
      setPosition([value.latitude, value.longitude])
    }
  }, [value?.latitude, value?.longitude])

  const handleLocationSelect = (lat, lng) => {
    setPosition([lat, lng])
    onChange({ latitude: lat, longitude: lng })
  }

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (pos?.coords?.latitude && pos?.coords?.longitude) {
          handleLocationSelect(pos.coords.latitude, pos.coords.longitude)
        }
      },
      (err) => {
        console.error('Geolocation error:', err)
        alert('Unable to get your location. Please click on the map to select a location.')
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  const lat = position[0]
  const lon = position[1]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-700">Location</label>
        <button
          type="button"
          onClick={useCurrentLocation}
          className="flex items-center gap-1 text-sm text-trust-blue hover:text-engagement-blue"
        >
          <MapPinIcon className="h-4 w-4" />
          Use my location
        </button>
      </div>
      <div className="h-64 rounded-lg overflow-hidden border border-slate-300 bg-slate-100">
        <MapContainer
          center={position}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position} />
          <MapEvents onLocationSelect={handleLocationSelect} />
          <MapController center={position} />
        </MapContainer>
      </div>
      <p className="text-xs text-slate-500">
        Click on the map to select location. Lat: {lat.toFixed(4)}, Lon: {lon.toFixed(4)}
      </p>
    </div>
  )
}