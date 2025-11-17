import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { MapPin, Navigation } from 'lucide-react'
import apiClient from '@/packages/api/client'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default marker icon in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface LocationPickerProps {
  onLocationSelect: (location: { lat: number; lng: number; address?: string }) => void
  initialLocation?: { lat: number; lng: number }
  showSavedLocations?: boolean
}

function MapClickHandler({ onLocationSelect }: { onLocationSelect: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

export default function LocationPicker({ onLocationSelect, initialLocation, showSavedLocations = true }: LocationPickerProps) {
  const [position, setPosition] = useState<[number, number]>(initialLocation ? [initialLocation.lat, initialLocation.lng] : [19.0760, 72.8777]) // Default to Mumbai
  const [address, setAddress] = useState('')
  const [loading, setLoading] = useState(false)
  const [savedLocations, setSavedLocations] = useState<any[]>([])
  const [showMap, setShowMap] = useState(false)

  useEffect(() => {
    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setPosition([pos.coords.latitude, pos.coords.longitude])
        },
        () => {
          // Use default if geolocation fails
        }
      )
    }

    // Load saved locations if authenticated
    if (showSavedLocations) {
      apiClient.get('/auth/saved-locations/')
        .then((response) => {
          setSavedLocations(response.data.results || response.data || [])
        })
        .catch(() => {
          // Fallback to localStorage
          const saved = localStorage.getItem('saved_locations')
          if (saved) {
            setSavedLocations(JSON.parse(saved))
          }
        })
    }
  }, [showSavedLocations])

  const handleMapClick = async (lat: number, lng: number) => {
    setPosition([lat, lng])
    setLoading(true)
    
    try {
      // Reverse geocode to get address
      const response = await apiClient.post('/restaurants/location/detect/', {
        latitude: lat,
        longitude: lng,
      })
      setAddress(`${response.data.address}, ${response.data.city}, ${response.data.state}`)
    } catch (error) {
      setAddress('Location selected')
    } finally {
      setLoading(false)
    }
  }

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude
          const lng = pos.coords.longitude
          setPosition([lat, lng])
          handleMapClick(lat, lng)
        },
        () => {
          alert('Unable to get your location')
        }
      )
    }
  }

  const handleConfirm = () => {
    onLocationSelect({
      lat: position[0],
      lng: position[1],
      address: address || `Lat: ${position[0]}, Lng: ${position[1]}`,
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={() => setShowMap(!showMap)}
          className="flex-1"
        >
          <MapPin className="w-4 h-4 mr-2" />
          {showMap ? 'Hide Map' : 'Show Map'}
        </Button>
        <Button
          variant="outline"
          onClick={handleUseCurrentLocation}
        >
          <Navigation className="w-4 h-4 mr-2" />
          Use Current Location
        </Button>
      </div>

      {showMap && (
        <div className="h-64 w-full rounded-lg overflow-hidden border">
          <MapContainer
            center={position}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={position} />
            <MapClickHandler onLocationSelect={handleMapClick} />
          </MapContainer>
        </div>
      )}

      {showSavedLocations && savedLocations.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2">Saved Locations</h4>
          <div className="space-y-2">
            {savedLocations.map((loc) => (
              <button
                key={loc.id}
                onClick={() => {
                  setPosition([loc.latitude, loc.longitude])
                  setAddress(loc.address)
                }}
                className="w-full text-left p-3 border rounded-lg hover:bg-gray-50"
              >
                <div className="font-medium">{loc.label}</div>
                <div className="text-sm text-gray-600">{loc.address}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
        <Input
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Selected location address"
        />
      </div>

      <Button onClick={handleConfirm} className="w-full" disabled={loading}>
        {loading ? 'Loading...' : 'Confirm Location'}
      </Button>
    </div>
  )
}

