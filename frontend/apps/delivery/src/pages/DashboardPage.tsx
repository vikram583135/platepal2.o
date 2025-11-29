import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { cn } from '@/packages/utils/cn'
import * as formatUtils from '@/packages/utils/format'

interface Shift {
  id: number
  status: string
  actual_start_time: string | null
  actual_end_time: string | null
  scheduled_start_time: string
  scheduled_end_time: string | null
  total_deliveries: number
  total_earnings: number
  total_distance_km: number
  total_time_minutes: number
}

interface DashboardStats {
  today_earnings: number
  today_deliveries: number
  week_earnings: number
  week_deliveries: number
  active_offers: number
  shift_status: string
}

export default function DashboardPage() {
  const queryClient = useQueryClient()
  const [shiftToggle, setShiftToggle] = useState(false)

  // Get current shift
  const { data: currentShift, isLoading: shiftLoading } = useQuery({
    queryKey: ['current-shift'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/deliveries/shifts/current/')
        return response.data as Shift | null
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null
        }
        throw error
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Get shift statistics
  const { data: shiftStats } = useQuery({
    queryKey: ['shift-summary'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/shifts/summary/')
      return response.data
    },
    enabled: !!currentShift,
  })

  // Get dashboard stats
  const { data: dashboardStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [earnings, deliveries, offers] = await Promise.all([
        apiClient.get('/deliveries/wallets/earnings_breakdown/?period=day').catch(() => ({ data: { breakdown: { total_earnings: 0, total_deliveries: 0 } } })),
        apiClient.get('/deliveries/deliveries/').catch(() => ({ data: { results: [] } })),
        apiClient.get('/deliveries/offers/nearby/').catch(() => ({ data: [] })),
      ])

      const weekEarnings = await apiClient.get('/deliveries/wallets/earnings_breakdown/?period=week').catch(() => ({ data: { breakdown: { total_earnings: 0, total_deliveries: 0 } } }))

      return {
        today_earnings: earnings.data.breakdown?.total_earnings || 0,
        today_deliveries: earnings.data.breakdown?.total_deliveries || 0,
        week_earnings: weekEarnings.data.breakdown?.total_earnings || 0,
        week_deliveries: weekEarnings.data.breakdown?.total_deliveries || 0,
        active_offers: Array.isArray(offers.data) ? offers.data.length : 0,
        shift_status: currentShift?.status || 'INACTIVE',
      } as DashboardStats
    },
    refetchInterval: 60000, // Refetch every minute
  })

  // Start shift mutation
  const startShiftMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/deliveries/shifts/start/')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      setShiftToggle(true)
    },
  })

  // Stop shift mutation
  const stopShiftMutation = useMutation({
    mutationFn: async (shiftId: number) => {
      const response = await apiClient.post(`/deliveries/shifts/${shiftId}/stop/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-shift'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      setShiftToggle(false)
    },
  })

  useEffect(() => {
    if (currentShift) {
      setShiftToggle(currentShift.status === 'ACTIVE')
    }
  }, [currentShift])

  const handleShiftToggle = () => {
    if (currentShift && currentShift.status === 'ACTIVE') {
      stopShiftMutation.mutate(currentShift.id)
    } else {
      startShiftMutation.mutate()
    }
  }

  const isShiftActive = currentShift?.status === 'ACTIVE'

  return (
    <div className="space-y-6">
      {/* Header with Shift Toggle */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isShiftActive ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className="text-sm font-medium text-gray-700">
              {isShiftActive ? 'On Shift' : 'Off Shift'}
            </span>
          </div>
          <Button
            onClick={handleShiftToggle}
            disabled={startShiftMutation.isPending || stopShiftMutation.isPending}
            variant={isShiftActive ? 'destructive' : 'default'}
            className={cn(
              'min-w-[120px]',
              isShiftActive ? 'bg-red-600 hover:bg-red-700' : 'delivery-button-primary'
            )}
          >
            {startShiftMutation.isPending || stopShiftMutation.isPending
              ? 'Processing...'
              : isShiftActive
              ? 'End Shift'
              : 'Start Shift'}
          </Button>
        </div>
      </div>

      {/* Shift Summary Cards */}
      {currentShift && isShiftActive && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="delivery-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Shift Earnings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-600">
                {formatUtils.formatCurrency(shiftStats?.total_earnings || currentShift.total_earnings || 0, 'INR')}
              </div>
            </CardContent>
          </Card>
          <Card className="delivery-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Deliveries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {shiftStats?.total_deliveries || currentShift.total_deliveries || 0}
              </div>
            </CardContent>
          </Card>
          <Card className="delivery-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Distance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {((shiftStats?.total_distance_km || currentShift.total_distance_km || 0) * 1000).toFixed(0)} km
              </div>
            </CardContent>
          </Card>
          <Card className="delivery-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.floor((shiftStats?.total_time_minutes || currentShift.total_time_minutes || 0) / 60)}h {((shiftStats?.total_time_minutes || currentShift.total_time_minutes || 0) % 60)}m
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dashboard Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="delivery-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Today's Earnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600 mb-2">
              {formatUtils.formatCurrency(dashboardStats?.today_earnings || 0, 'INR')}
            </div>
            <p className="text-sm text-gray-600">
              {dashboardStats?.today_deliveries || 0} deliveries completed
            </p>
          </CardContent>
        </Card>

        <Card className="delivery-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {formatUtils.formatCurrency(dashboardStats?.week_earnings || 0, 'INR')}
            </div>
            <p className="text-sm text-gray-600">
              {dashboardStats?.week_deliveries || 0} deliveries this week
            </p>
          </CardContent>
        </Card>

        <Card className="delivery-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Available Offers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600 mb-2">
              {dashboardStats?.active_offers || 0}
            </div>
            <p className="text-sm text-gray-600">
              Offers available nearby
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {shiftStats && (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm font-medium">Shift Started</span>
                <span className="text-sm text-gray-600">
                  {currentShift?.actual_start_time
                    ? formatUtils.formatDate(currentShift.actual_start_time) + ' ' + formatUtils.formatTime(currentShift.actual_start_time)
                    : 'Not started'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm font-medium">Active Time</span>
                <span className="text-sm text-gray-600">
                  {Math.floor((shiftStats.total_time_minutes || 0) / 60)}h {((shiftStats.total_time_minutes || 0) % 60)}m
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-sm font-medium">Average per Delivery</span>
                <span className="text-sm font-semibold text-emerald-600">
                  {formatUtils.formatCurrency(
                    (shiftStats.total_deliveries || 0) > 0
                      ? (shiftStats.total_earnings || 0) / (shiftStats.total_deliveries || 1)
                      : 0,
                    'INR'
                  )}
                </span>
              </div>
            </div>
          )}
          {!currentShift && (
            <div className="text-center py-8 text-gray-500">
              <p>Start a shift to see your activity</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

