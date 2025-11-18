import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
// Using native HTML elements for switches and labels
import { Input } from '@/packages/ui/components/input'
import { Moon, Sun, Globe, Bell, Lock, Cookie, Shield, Key } from 'lucide-react'
import apiClient from '@/packages/api/client'

export default function SettingsPage() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme')
    return (saved as 'light' | 'dark') || 'light'
  })

  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'en'
  })

  const queryClient = useQueryClient()

  const { data: notificationPrefs, isLoading: prefsLoading } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      const response = await apiClient.get('/notifications/notification-preferences/')
      return response.data.results?.[0] || response.data
    },
  })

  const updatePrefsMutation = useMutation({
    mutationFn: async (data: any) => {
      if (notificationPrefs?.id) {
        const response = await apiClient.patch(`/notifications/notification-preferences/${notificationPrefs.id}/`, data)
        return response.data
      } else {
        const response = await apiClient.post('/notifications/notification-preferences/', data)
        return response.data
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
    },
  })

  const [privacy, setPrivacy] = useState({
    profileVisibility: localStorage.getItem('privacy_profile') || 'public',
    showEmail: localStorage.getItem('privacy_email') !== 'false',
    showPhone: localStorage.getItem('privacy_phone') === 'true',
  })

  const [cookieConsent, setCookieConsent] = useState(() => {
    return localStorage.getItem('cookie_consent') === 'true'
  })

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
    // Persist preference to backend when available
    apiClient
      .patch('/auth/users/preferences/', { theme })
      .catch(() => {})
  }, [theme])

  const handleNotificationChange = (key: string, value: boolean) => {
    if (notificationPrefs) {
      updatePrefsMutation.mutate({ [key]: value })
    }
  }

  const handlePrivacyChange = (key: string, value: string | boolean) => {
    setPrivacy({ ...privacy, [key]: value })
    localStorage.setItem(`privacy_${key}`, value.toString())
  }

  const handleCookieConsent = (accepted: boolean) => {
    setCookieConsent(accepted)
    localStorage.setItem('cookie_consent', accepted.toString())
  }

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'hi', name: 'Hindi' },
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        {/* Theme Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              Appearance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold">Theme</h4>
                <p className="text-sm text-gray-600">Choose your preferred theme</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  onClick={() => setTheme('light')}
                >
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => setTheme('dark')}
                >
                  Dark
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Language Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Language
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {languages.map((lang) => (
                <label
                  key={lang.code}
                  className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="radio"
                    name="language"
                    value={lang.code}
                    checked={language === lang.code}
                    onChange={(e) => {
                      setLanguage(e.target.value)
                      localStorage.setItem('language', e.target.value)
                      apiClient
                        .patch('/auth/users/preferences/', { language: e.target.value })
                        .catch(() => {})
                    }}
                  />
                  <span>{lang.name}</span>
                </label>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notification Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {prefsLoading ? (
              <div>Loading preferences...</div>
            ) : (
              <>
                {/* Email Preferences */}
                <div>
                  <h4 className="font-semibold mb-3">Email Notifications</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label htmlFor="email-orders" className="text-sm font-medium">Order Updates</label>
                      <input
                        id="email-orders"
                        type="checkbox"
                        checked={notificationPrefs?.email_order_updates ?? true}
                        onChange={(e) => handleNotificationChange('email_order_updates', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="email-promotions" className="text-sm font-medium">Promotions</label>
                      <input
                        id="email-promotions"
                        type="checkbox"
                        checked={notificationPrefs?.email_promotions ?? true}
                        onChange={(e) => handleNotificationChange('email_promotions', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="email-payments" className="text-sm font-medium">Payment Updates</label>
                      <input
                        id="email-payments"
                        type="checkbox"
                        checked={notificationPrefs?.email_payment_updates ?? true}
                        onChange={(e) => handleNotificationChange('email_payment_updates', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="email-reviews" className="text-sm font-medium">Review Requests</label>
                      <input
                        id="email-reviews"
                        type="checkbox"
                        checked={notificationPrefs?.email_review_requests ?? true}
                        onChange={(e) => handleNotificationChange('email_review_requests', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                  </div>
                </div>

                {/* Push Preferences */}
                <div>
                  <h4 className="font-semibold mb-3">Push Notifications</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label htmlFor="push-orders" className="text-sm font-medium">Order Updates</label>
                      <input
                        id="push-orders"
                        type="checkbox"
                        checked={notificationPrefs?.push_order_updates ?? true}
                        onChange={(e) => handleNotificationChange('push_order_updates', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="push-promotions" className="text-sm font-medium">Promotions</label>
                      <input
                        id="push-promotions"
                        type="checkbox"
                        checked={notificationPrefs?.push_promotions ?? true}
                        onChange={(e) => handleNotificationChange('push_promotions', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="push-payments" className="text-sm font-medium">Payment Updates</label>
                      <input
                        id="push-payments"
                        type="checkbox"
                        checked={notificationPrefs?.push_payment_updates ?? true}
                        onChange={(e) => handleNotificationChange('push_payment_updates', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                  </div>
                </div>

                {/* SMS Preferences */}
                <div>
                  <h4 className="font-semibold mb-3">SMS Notifications</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label htmlFor="sms-orders" className="text-sm font-medium">Order Updates</label>
                      <input
                        id="sms-orders"
                        type="checkbox"
                        checked={notificationPrefs?.sms_order_updates ?? false}
                        onChange={(e) => handleNotificationChange('sms_order_updates', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="sms-promotions" className="text-sm font-medium">Promotions</label>
                      <input
                        id="sms-promotions"
                        type="checkbox"
                        checked={notificationPrefs?.sms_promotions ?? false}
                        onChange={(e) => handleNotificationChange('sms_promotions', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                  </div>
                </div>

                {/* Quiet Hours */}
                <div>
                  <h4 className="font-semibold mb-3">Quiet Hours</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label htmlFor="quiet-hours" className="text-sm font-medium">Enable Quiet Hours</label>
                      <input
                        id="quiet-hours"
                        type="checkbox"
                        checked={notificationPrefs?.quiet_hours_enabled ?? false}
                        onChange={(e) => handleNotificationChange('quiet_hours_enabled', e.target.checked)}
                        className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 transition-colors"
                      />
                    </div>
                    {notificationPrefs?.quiet_hours_enabled && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="quiet-start" className="block text-sm font-medium mb-1">Start Time</label>
                          <Input
                            id="quiet-start"
                            type="time"
                            value={notificationPrefs?.quiet_hours_start || '22:00'}
                            onChange={(e) => updatePrefsMutation.mutate({ quiet_hours_start: e.target.value })}
                          />
                        </div>
                        <div>
                          <label htmlFor="quiet-end" className="block text-sm font-medium mb-1">End Time</label>
                          <Input
                            id="quiet-end"
                            type="time"
                            value={notificationPrefs?.quiet_hours_end || '08:00'}
                            onChange={(e) => updatePrefsMutation.mutate({ quiet_hours_end: e.target.value })}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Security
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <TwoFactorAuthSection />
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Privacy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Profile Visibility</h4>
              <div className="space-y-2">
                {['public', 'friends', 'private'].map((option) => (
                  <label
                    key={option}
                    className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="profileVisibility"
                      value={option}
                      checked={privacy.profileVisibility === option}
                      onChange={(e) => handlePrivacyChange('profileVisibility', e.target.value)}
                    />
                    <span className="capitalize">{option}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold">Show Email</h4>
                <p className="text-sm text-gray-600">Allow others to see your email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={privacy.showEmail}
                  onChange={(e) => handlePrivacyChange('showEmail', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold">Show Phone</h4>
                <p className="text-sm text-gray-600">Allow others to see your phone number</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={privacy.showPhone}
                  onChange={(e) => handlePrivacyChange('showPhone', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Cookie Consent */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cookie className="w-5 h-5" />
              Cookie Preferences
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                We use cookies to enhance your experience. You can manage your cookie preferences here.
              </p>
              {!cookieConsent && (
                <div className="flex gap-2">
                  <Button onClick={() => handleCookieConsent(true)}>Accept All Cookies</Button>
                  <Button variant="outline" onClick={() => handleCookieConsent(false)}>
                    Reject All
                  </Button>
                </div>
              )}
              {cookieConsent && (
                <p className="text-sm text-green-600">Cookie preferences saved</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function TwoFactorAuthSection() {
  const queryClient = useQueryClient()

  const { data: twoFactorAuth, isLoading: authLoading } = useQuery({
    queryKey: ['two-factor-auth'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/two-factor-auth/')
      return response.data.results?.[0] || response.data
    },
  })

  const toggleTwoFactorMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      if (twoFactorAuth?.id) {
        const response = await apiClient.patch(`/auth/two-factor-auth/${twoFactorAuth.id}/`, {
          is_enabled: enabled,
          method: enabled ? 'EMAIL' : 'NONE',
        })
        return response.data
      } else {
        const response = await apiClient.post('/auth/two-factor-auth/', {
          is_enabled: enabled,
          method: enabled ? 'EMAIL' : 'NONE',
        })
        return response.data
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['two-factor-auth'] })
    },
  })

  const generateBackupCodesMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/auth/two-factor-auth/generate-backup-codes/', {})
      return response.data
    },
  })

  const handleToggle2FA = async (enabled: boolean) => {
    try {
      await toggleTwoFactorMutation.mutateAsync(enabled)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update 2FA settings')
    }
  }

  const handleGenerateBackupCodes = async () => {
    try {
      const result = await generateBackupCodesMutation.mutateAsync()
      alert(`Backup codes generated: ${result.backup_codes?.join(', ') || 'Check console'}`)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to generate backup codes')
    }
  }

  if (authLoading) {
    return <div className="text-sm text-gray-600">Loading security settings...</div>
  }

  const isEnabled = twoFactorAuth?.is_enabled || false

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="font-semibold flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Two-Factor Authentication
          </h4>
          <p className="text-sm text-gray-600">
            Add an extra layer of security to your account
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={(e) => handleToggle2FA(e.target.checked)}
            disabled={toggleTwoFactorMutation.isPending}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
        </label>
      </div>

      {isEnabled && (
        <div className="pl-6 border-l-2 border-gray-200 space-y-3">
          <div className="text-sm">
            <p className="font-medium">Method: {twoFactorAuth?.method || 'Email'}</p>
            <p className="text-gray-600">You'll receive a code via {twoFactorAuth?.method?.toLowerCase() || 'email'} when signing in</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateBackupCodes}
            disabled={generateBackupCodesMutation.isPending}
            className="flex items-center gap-2"
          >
            <Key className="w-4 h-4" />
            Generate Backup Codes
          </Button>
        </div>
      )}
    </div>
  )
}

