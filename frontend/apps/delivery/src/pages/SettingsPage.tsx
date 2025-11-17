import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'

interface RiderSettings {
  id: number
  location_tracking_enabled: boolean
  location_update_interval: number
  notifications_enabled: boolean
  preferred_navigation_app: string
  auto_accept_enabled: boolean
  battery_saver_mode: boolean
  dark_mode: boolean
  high_contrast: boolean
  large_tap_targets: boolean
  sound_alerts_enabled: boolean
  voice_prompts_enabled: boolean
}

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [saved, setSaved] = useState(false)

  // Get rider settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['rider-settings'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/settings/my_settings/')
      return response.data as RiderSettings
    },
  })

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: async (data: Partial<RiderSettings>) => {
      const response = await apiClient.patch('/deliveries/settings/my_settings/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rider-settings'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    )
  }

  const handleToggle = (field: keyof RiderSettings) => {
    if (settings) {
      updateMutation.mutate({
        [field]: !settings[field],
      } as Partial<RiderSettings>)
    }
  }

  const handleUpdate = (field: keyof RiderSettings, value: any) => {
    if (settings) {
      updateMutation.mutate({
        [field]: value,
      } as Partial<RiderSettings>)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      {saved && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
          Settings saved successfully!
        </div>
      )}

      {/* Location Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Location & Tracking</CardTitle>
          <CardDescription>Manage location tracking preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Location Tracking</p>
              <p className="text-sm text-gray-600">Enable GPS tracking for deliveries</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.location_tracking_enabled || false}
                onChange={() => handleToggle('location_tracking_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>

          {settings?.location_tracking_enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Update Interval (seconds)
              </label>
              <Input
                type="number"
                min="5"
                max="300"
                value={settings?.location_update_interval || 30}
                onChange={(e) => handleUpdate('location_update_interval', parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          )}

          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Battery Saver Mode</p>
              <p className="text-sm text-gray-600">Reduce location update frequency to save battery</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.battery_saver_mode || false}
                onChange={() => handleToggle('battery_saver_mode')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Navigation Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Navigation</CardTitle>
          <CardDescription>Choose your preferred navigation app</CardDescription>
        </CardHeader>
        <CardContent>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Navigation App
            </label>
            <select
              value={settings?.preferred_navigation_app || 'GOOGLE_MAPS'}
              onChange={(e) => handleUpdate('preferred_navigation_app', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="GOOGLE_MAPS">Google Maps</option>
              <option value="APPLE_MAPS">Apple Maps</option>
              <option value="WAZE">Waze</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Notifications</CardTitle>
          <CardDescription>Manage notification preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Push Notifications</p>
              <p className="text-sm text-gray-600">Receive push notifications for offers</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.notifications_enabled || false}
                onChange={() => handleToggle('notifications_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>

          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Sound Alerts</p>
              <p className="text-sm text-gray-600">Play sound for new offers</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.sound_alerts_enabled || false}
                onChange={() => handleToggle('sound_alerts_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>

          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Voice Prompts</p>
              <p className="text-sm text-gray-600">Audio prompts for navigation</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.voice_prompts_enabled || false}
                onChange={() => handleToggle('voice_prompts_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Accessibility Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Accessibility</CardTitle>
          <CardDescription>Improve app usability and accessibility</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Dark Mode</p>
              <p className="text-sm text-gray-600">Enable dark theme</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.dark_mode || false}
                onChange={() => handleToggle('dark_mode')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>

          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">High Contrast</p>
              <p className="text-sm text-gray-600">Increase color contrast for better visibility</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.high_contrast || false}
                onChange={() => handleToggle('high_contrast')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>

          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Large Tap Targets</p>
              <p className="text-sm text-gray-600">Increase button sizes for easier tapping</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.large_tap_targets || false}
                onChange={() => handleToggle('large_tap_targets')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Auto-Accept */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Auto-Accept</CardTitle>
          <CardDescription>Automatically accept offers based on rules</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium">Enable Auto-Accept</p>
              <p className="text-sm text-gray-600">Automatically accept offers matching your rules</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.auto_accept_enabled || false}
                onChange={() => handleToggle('auto_accept_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

