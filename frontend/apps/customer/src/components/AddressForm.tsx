import { useState, useEffect } from 'react'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { MapPin, Navigation, Save, X } from 'lucide-react'
import LocationPicker from './LocationPicker'
import apiClient from '@/packages/api/client'

interface AddressFormProps {
  address?: any
  onSave: (address: any) => void
  onCancel: () => void
}

export default function AddressForm({ address, onSave, onCancel }: AddressFormProps) {
  const [formData, setFormData] = useState({
    label: address?.label || '',
    street: address?.street || '',
    city: address?.city || '',
    state: address?.state || '',
    postal_code: address?.postal_code || '',
    country: address?.country || 'India',
    delivery_instructions: address?.delivery_instructions || '',
    latitude: address?.latitude || null,
    longitude: address?.longitude || null,
    is_default: address?.is_default || false,
  })
  const [showMapPicker, setShowMapPicker] = useState(false)
  const [autoCompleteSuggestions, setAutoCompleteSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Auto-complete for address (mock - in production, use Google Places API)
  useEffect(() => {
    if (formData.street.length >= 3) {
      // Mock suggestions - in production, call Google Places API
      const mockSuggestions = [
        { description: `${formData.street}, ${formData.city || 'Mumbai'}, Maharashtra`, place_id: '1' },
        { description: `${formData.street} Street, ${formData.city || 'Mumbai'}, Maharashtra`, place_id: '2' },
      ]
      setAutoCompleteSuggestions(mockSuggestions)
      setShowSuggestions(true)
    } else {
      setAutoCompleteSuggestions([])
      setShowSuggestions(false)
    }
  }, [formData.street, formData.city])

  const handleLocationSelect = (location: { lat: number; lng: number; address?: string }) => {
    setFormData({
      ...formData,
      latitude: location.lat,
      longitude: location.lng,
    })
    if (location.address) {
      // Parse address (basic - in production, use geocoding service)
      const parts = location.address.split(',')
      if (parts.length >= 3) {
        setFormData(prev => ({
          ...prev,
          street: parts[0].trim(),
          city: parts[1].trim(),
          state: parts[2].trim(),
          latitude: location.lat,
          longitude: location.lng,
        }))
      }
    }
    setShowMapPicker(false)
  }

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude
          const lng = pos.coords.longitude
          
          try {
            const response = await apiClient.post('/restaurants/location/detect/', {
              latitude: lat,
              longitude: lng,
            })
            setFormData({
              ...formData,
              street: response.data.address,
              city: response.data.city,
              state: response.data.state,
              postal_code: response.data.postal_code,
              latitude: lat,
              longitude: lng,
            })
          } catch (error) {
            setFormData({
              ...formData,
              latitude: lat,
              longitude: lng,
            })
          }
        },
        () => {
          alert('Unable to get your location')
        }
      )
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{address ? 'Edit Address' : 'Add New Address'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Label *</label>
            <select
              value={formData.label}
              onChange={(e) => setFormData({ ...formData, label: e.target.value })}
              className="w-full p-2 border rounded-lg"
              required
            >
              <option value="">Select label</option>
              <option value="Home">Home</option>
              <option value="Work">Work</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">Street Address *</label>
            <Input
              value={formData.street}
              onChange={(e) => setFormData({ ...formData, street: e.target.value })}
              placeholder="Enter street address"
              required
            />
            {showSuggestions && autoCompleteSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10">
                {autoCompleteSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => {
                      setFormData({ ...formData, street: suggestion.description })
                      setShowSuggestions(false)
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 border-b last:border-0"
                  >
                    {suggestion.description}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <Input
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State *</label>
              <Input
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Postal Code</label>
              <Input
                value={formData.postal_code}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
              <Input
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Delivery Instructions (Floor, Flat, Landmark)
            </label>
            <textarea
              value={formData.delivery_instructions}
              onChange={(e) => setFormData({ ...formData, delivery_instructions: e.target.value })}
              placeholder="e.g., 3rd floor, Flat 301, Near ABC Building"
              className="w-full p-2 border rounded-lg"
              rows={3}
            />
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleUseCurrentLocation}
              className="flex-1"
            >
              <Navigation className="w-4 h-4 mr-2" />
              Use Current Location
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowMapPicker(true)}
              className="flex-1"
            >
              <MapPin className="w-4 h-4 mr-2" />
              Pick on Map
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_default"
              checked={formData.is_default}
              onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
            />
            <label htmlFor="is_default" className="text-sm text-gray-700">
              Set as default address
            </label>
          </div>

          <div className="flex gap-2">
            <Button type="submit" className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              Save Address
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        </form>

        {showMapPicker && (
          <div className="mt-4">
            <LocationPicker
              onLocationSelect={handleLocationSelect}
              initialLocation={formData.latitude && formData.longitude ? { lat: formData.latitude, lng: formData.longitude } : undefined}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

