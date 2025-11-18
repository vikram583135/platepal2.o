import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { useAuthStore } from '../stores/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Camera, Trash2, Edit2, Save, X, Shield, Smartphone, Download, AlertTriangle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import AddressForm from '../components/AddressForm'

export default function ProfilePage() {
  const { user, setUser, logout } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
  })
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [deleteExport, setDeleteExport] = useState(false)
  const [showAddressForm, setShowAddressForm] = useState(false)
  const [editingAddress, setEditingAddress] = useState<any>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')

  const { data: addresses, isLoading: addressesLoading } = useQuery({
    queryKey: ['addresses'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/addresses/')
      return response.data.results || response.data
    },
  })

  const { data: devices, isLoading: devicesLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/devices/')
      return response.data.results || response.data
    },
  })

    const revokeDeviceMutation = useMutation({
      mutationFn: async (deviceId: number) => {
        // Prefer explicit revoke endpoint; fallback to delete
        try {
          const res = await apiClient.post(`/auth/devices/${deviceId}/revoke/`)
          return res.data
        } catch (e: any) {
          await apiClient.delete(`/auth/devices/${deviceId}/`)
        }
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['devices'] })
      },
    })

  const { data: twoFactorAuth } = useQuery({
    queryKey: ['two-factor-auth'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/two-factor-auth/')
      return response.data.results?.[0] || response.data
    },
  })

  const updateProfileMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.patch(`/auth/users/${user?.id}/`, data)
      return response.data
    },
    onSuccess: (data) => {
      setUser(data)
      setEditing(false)
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })

  const uploadPhotoMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('profile_photo', file)
      const response = await apiClient.post('/auth/users/upload_profile_photo/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: (data) => {
      setUser(data)
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })

  const changePasswordMutation = useMutation({
    mutationFn: async (data: { old_password: string; new_password: string }) => {
      const response = await apiClient.post('/auth/users/change_password/', data)
      return response.data
    },
    onSuccess: () => {
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' })
      alert('Password changed successfully')
    },
  })

  const deleteAccountMutation = useMutation({
    mutationFn: async (exportData: boolean) => {
      const response = await apiClient.post('/auth/users/delete_account/', { export_data: exportData })
      return response.data
    },
    onSuccess: () => {
      logout()
      navigate('/signup')
    },
  })

  const exportDataMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.get('/auth/users/export-data/')
      return response.data
    },
    onSuccess: (data) => {
      // Create and download JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `platepal-data-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
  })

  const saveAddressMutation = useMutation({
    mutationFn: async (addressData: any) => {
      if (editingAddress) {
        const response = await apiClient.patch(`/auth/addresses/${editingAddress.id}/`, addressData)
        return response.data
      } else {
        const response = await apiClient.post('/auth/addresses/', addressData)
        return response.data
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['addresses'] })
      setShowAddressForm(false)
      setEditingAddress(null)
    },
  })

  const deleteAddressMutation = useMutation({
    mutationFn: async (addressId: number) => {
      await apiClient.delete(`/auth/addresses/${addressId}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['addresses'] })
    },
  })

  const toggle2FAMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await apiClient.patch('/auth/two-factor-auth/', { is_enabled: enabled })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['two-factor-auth'] })
    },
  })

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadPhotoMutation.mutate(file)
    }
  }

  const handleSave = () => {
    updateProfileMutation.mutate(editData)
  }

  const handleChangePassword = () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      alert('New passwords do not match')
      return
    }
    changePasswordMutation.mutate({
      old_password: passwordData.old_password,
      new_password: passwordData.new_password,
    })
  }

  const handleExportData = async () => {
    try {
      await exportDataMutation.mutateAsync()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to export data')
    }
  }

  const handleDeleteAccount = () => {
    if (deleteConfirmText !== 'DELETE') {
      return
    }
    deleteAccountMutation.mutate(deleteExport)
  }

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Profile Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Photo & Basic Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Profile Photo */}
              <div className="flex items-center gap-6">
                <div className="relative">
                  {user.profile_photo_url ? (
                    <img
                      src={user.profile_photo_url}
                      alt="Profile"
                      className="w-24 h-24 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center text-2xl font-semibold text-gray-500">
                      {user.first_name?.[0] || user.email[0].toUpperCase()}
                    </div>
                  )}
                  <label className="absolute bottom-0 right-0 bg-primary-600 text-white p-2 rounded-full cursor-pointer hover:bg-primary-700">
                    <Camera className="w-4 h-4" />
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoUpload}
                      className="hidden"
                    />
                  </label>
                </div>
                <div>
                  <h3 className="text-lg font-semibold">
                    {user.first_name} {user.last_name}
                  </h3>
                  <p className="text-gray-600">{user.email}</p>
                  {user.is_email_verified && (
                    <Badge className="mt-1">Email Verified</Badge>
                  )}
                </div>
              </div>

              {/* Edit Personal Details */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="font-semibold">Personal Details</h4>
                  {!editing ? (
                    <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                      <Edit2 className="w-4 h-4 mr-2" />
                      Edit
                    </Button>
                  ) : (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditing(false)
                          setEditData({
                            first_name: user.first_name || '',
                            last_name: user.last_name || '',
                            phone: user.phone || '',
                          })
                        }}
                      >
                        <X className="w-4 h-4 mr-2" />
                        Cancel
                      </Button>
                      <Button size="sm" onClick={handleSave} disabled={updateProfileMutation.isPending}>
                        <Save className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                    {editing ? (
                      <Input
                        value={editData.first_name}
                        onChange={(e) => setEditData({ ...editData, first_name: e.target.value })}
                      />
                    ) : (
                      <p className="text-gray-900">{user.first_name || 'Not set'}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                    {editing ? (
                      <Input
                        value={editData.last_name}
                        onChange={(e) => setEditData({ ...editData, last_name: e.target.value })}
                      />
                    ) : (
                      <p className="text-gray-900">{user.last_name || 'Not set'}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  {editing ? (
                    <Input
                      value={editData.phone}
                      onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
                      placeholder="+1234567890"
                    />
                  ) : (
                    <p className="text-gray-900">{user.phone || 'Not provided'}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Change Password */}
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                <Input
                  type="password"
                  value={passwordData.old_password}
                  onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                <Input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                <Input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                />
              </div>
              <Button
                onClick={handleChangePassword}
                disabled={changePasswordMutation.isPending || !passwordData.old_password || !passwordData.new_password}
              >
                Change Password
              </Button>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Security Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Two-Factor Authentication */}
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold">Two-Factor Authentication</h4>
                  <p className="text-sm text-gray-600">
                    Add an extra layer of security to your account
                  </p>
                </div>
                <Button
                  variant={twoFactorAuth?.is_enabled ? 'default' : 'outline'}
                  onClick={() => toggle2FAMutation.mutate(!twoFactorAuth?.is_enabled)}
                  disabled={toggle2FAMutation.isPending}
                >
                  {twoFactorAuth?.is_enabled ? 'Disable' : 'Enable'} 2FA
                </Button>
              </div>

              {/* Device Management */}
              <div>
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  <Smartphone className="w-5 h-5" />
                  Trusted Devices
                </h4>
                {devicesLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : devices && devices.length > 0 ? (
                  <div className="space-y-3">
                    {devices.map((device: any) => (
                      <div key={device.id} className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <p className="font-medium">{device.device_name}</p>
                          <p className="text-sm text-gray-600">
                            {device.device_type} • {device.os} • {device.browser}
                          </p>
                          <p className="text-xs text-gray-500">
                            Last used: {new Date(device.last_used).toLocaleDateString()}
                          </p>
                        </div>
                          <div className="flex items-center gap-2">
                            {device.is_trusted && <Badge>Trusted</Badge>}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => revokeDeviceMutation.mutate(device.id)}
                              disabled={revokeDeviceMutation.isPending}
                            >
                              Revoke
                            </Button>
                          </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">No devices registered</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Delete Account */}
          <Card>
            <CardHeader>
              <CardTitle className="text-red-600">Danger Zone</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Delete Account</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Once you delete your account, there is no going back. Please be certain.
                  </p>
                  <div className="flex items-center gap-2 mb-4">
                    <input
                      type="checkbox"
                      id="export-data"
                      checked={deleteExport}
                      onChange={(e) => setDeleteExport(e.target.checked)}
                    />
                    <label htmlFor="export-data" className="text-sm text-gray-700">
                      Export my data before deletion
                    </label>
                  </div>
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAccount}
                    disabled={deleteAccountMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Addresses Sidebar */}
        <div>
          {showAddressForm ? (
            <AddressForm
              address={editingAddress}
              onSave={(addressData) => saveAddressMutation.mutate(addressData)}
              onCancel={() => {
                setShowAddressForm(false)
                setEditingAddress(null)
              }}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Addresses</CardTitle>
              </CardHeader>
              <CardContent>
                {addressesLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : addresses && addresses.length > 0 ? (
                  <div className="space-y-4">
                    {addresses.map((address: any) => (
                      <div key={address.id} className="p-4 border rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-semibold">{address.label}</div>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingAddress(address)
                                setShowAddressForm(true)
                              }}
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                if (window.confirm('Delete this address?')) {
                                  deleteAddressMutation.mutate(address.id)
                                }
                              }}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        <div className="text-sm text-gray-600">
                          {address.street}, {address.city}, {address.state} {address.postal_code}
                        </div>
                        {address.delivery_instructions && (
                          <div className="text-xs text-gray-500 mt-1">
                            {address.delivery_instructions}
                          </div>
                        )}
                        {address.is_default && (
                          <Badge className="mt-2">Default</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 mb-4">No addresses saved</p>
                )}
                <Button
                  className="mt-4 w-full"
                  variant="outline"
                  onClick={() => {
                    setEditingAddress(null)
                    setShowAddressForm(true)
                  }}
                >
                  Add Address
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Account Management */}
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Account Management
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Export Your Data</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Download a copy of your personal data including profile, orders, and preferences.
                </p>
                <Button
                  variant="outline"
                  onClick={handleExportData}
                  disabled={exportDataMutation.isPending}
                  className="flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  {exportDataMutation.isPending ? 'Exporting...' : 'Export Data'}
                </Button>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <h4 className="font-semibold mb-2 text-red-600">Delete Account</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Permanently delete your account and all associated data. This action cannot be undone.
                </p>
                <Button
                  variant="destructive"
                  onClick={() => setShowDeleteConfirm(true)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete Account
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="text-red-600 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Confirm Account Deletion
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm">
                <p className="font-semibold">This will permanently delete:</p>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  <li>Your profile and personal information</li>
                  <li>Order history and preferences</li>
                  <li>Saved addresses and payment methods</li>
                  <li>Rewards and wallet balance</li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 p-3 rounded">
                <p className="text-sm text-yellow-800">
                  <strong>Tip:</strong> Export your data before deleting if you want to keep a copy.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Type <strong>DELETE</strong> to confirm
                </label>
                <Input
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder="DELETE"
                />
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeleteConfirmText('')
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDeleteAccount}
                  disabled={deleteConfirmText !== 'DELETE' || deleteAccountMutation.isPending}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  {deleteAccountMutation.isPending ? 'Deleting...' : 'Delete Account'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
