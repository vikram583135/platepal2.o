import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'

export default function StaffPage() {
  const { selectedRestaurantId } = useRestaurantStore()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', role: 'GENERAL_MANAGER' })
  const [formError, setFormError] = useState('')

  const staffQuery = useQuery({
    queryKey: ['staff', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/restaurants/managers/', {
        params: { restaurant: selectedRestaurantId },
      })
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || [])
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const inviteMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      if (!form.email.trim()) {
        throw new Error('Email is required')
      }
      if (!form.first_name.trim()) {
        throw new Error('First name is required')
      }
      
      // Normalize email
      const normalizedEmail = form.email.trim().toLowerCase()
      
      return apiClient.post('/restaurants/managers/', {
        restaurant: selectedRestaurantId,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: normalizedEmail,
        role: form.role,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff', selectedRestaurantId] })
      setForm({ first_name: '', last_name: '', email: '', role: 'GENERAL_MANAGER' })
      setFormError('')
    },
    onError: (error: any) => {
      setFormError(error.message || error.response?.data?.detail || 'Failed to invite staff member')
      console.error('Failed to invite staff:', error)
    },
  })

  const handleInvite = () => {
    setFormError('')
    if (!form.email.trim()) {
      setFormError('Email is required')
      return
    }
    if (!form.first_name.trim()) {
      setFormError('First name is required')
      return
    }
    inviteMutation.mutate()
  }

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to manage staff</p>
        </div>
      </div>
    )
  }

  if (staffQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading staff...</p>
      </div>
    )
  }

  if (staffQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load staff</p>
          <p className="text-zomato-gray text-sm">
            {staffQuery.error instanceof Error ? staffQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const staff = staffQuery.data || []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Staff & permissions</h1>
        <p className="text-sm text-slate-500">Granular access for managers, kitchen leads, delivery coordinators.</p>
      </header>

      <Card className="shadow-md">
        <CardHeader>
          <CardTitle>Invite teammate</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <Input placeholder="First name" value={form.first_name} onChange={(event) => setForm((prev) => ({ ...prev, first_name: event.target.value }))} />
          <Input placeholder="Last name" value={form.last_name} onChange={(event) => setForm((prev) => ({ ...prev, last_name: event.target.value }))} />
          <Input placeholder="Email" value={form.email} onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))} />
          <select
            value={form.role}
            onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
          >
            <option value="GENERAL_MANAGER">General manager</option>
            <option value="KITCHEN_MANAGER">Kitchen manager</option>
            <option value="OPERATIONS">Operations</option>
            <option value="FINANCE">Finance</option>
            <option value="STAFF">Staff</option>
          </select>
          <Button disabled={!form.email || !form.first_name || inviteMutation.isPending} onClick={handleInvite}>
            {inviteMutation.isPending ? 'Sending…' : 'Invite'}
          </Button>
          {formError && (
            <div className="md:col-span-4 text-sm text-red-600 mt-1">{formError}</div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {staff.length > 0 ? (
          staff.map((staffMember: any) => (
          <Card key={staffMember.id} className="border-white/70 bg-white/90">
            <CardHeader>
              <CardTitle className="text-base">{staffMember.full_name || `${staffMember.first_name || ''} ${staffMember.last_name || ''}`.trim() || 'Unknown'}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-1">
              <p>{staffMember.email || 'No email'}</p>
              <p className="text-xs uppercase text-slate-500">{staffMember.role?.replace('_', ' ') || 'Unknown role'}</p>
            </CardContent>
          </Card>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <p className="text-sm text-slate-500">No staff added yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}


