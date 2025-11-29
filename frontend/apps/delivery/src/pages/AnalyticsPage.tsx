import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import * as formatUtils from '@/packages/utils/format'

interface TripLog {
  id: number
  delivery: {
    order: {
      order_number: string
    }
  }
  start_time: string
  end_time: string
  distance_km: number
  duration_minutes: number
  earnings: number
  status: string
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('week')

  // Get trip logs
  const { data: tripLogs, isLoading } = useQuery({
    queryKey: ['trip-logs', period],
    queryFn: async () => {
      const response = await apiClient.get(`/deliveries/trip-logs/?period=${period}`)
      return (response.data.results || response.data) as TripLog[]
    },
  })

  // Get analytics summary
  const { data: analytics } = useQuery({
    queryKey: ['trip-analytics', period],
    queryFn: async () => {
      const response = await apiClient.get(`/deliveries/trip-logs/analytics/?period=${period}`)
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  const totalTrips = tripLogs?.length || 0
  const totalDistance = tripLogs?.reduce((sum, log) => sum + (log.distance_km || 0), 0) || 0
  const totalEarnings = tripLogs?.reduce((sum, log) => sum + (log.earnings || 0), 0) || 0
  const totalTime = tripLogs?.reduce((sum, log) => sum + (log.duration_minutes || 0), 0) || 0
  const avgDistance = totalTrips > 0 ? totalDistance / totalTrips : 0
  const avgEarnings = totalTrips > 0 ? totalEarnings / totalTrips : 0
  const avgTime = totalTrips > 0 ? totalTime / totalTrips : 0

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Analytics</h1>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as typeof period)}
          className="px-4 py-2 border border-gray-300 rounded-md"
        >
          <option value="day">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Trips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTrips}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Distance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDistance.toFixed(1)} km</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Earnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatUtils.formatCurrency(totalEarnings, 'INR')}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.floor(totalTime / 60)}h {totalTime % 60}m
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Average Metrics */}
      {totalTrips > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Average Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Avg Distance per Trip</p>
                <p className="text-2xl font-bold">{avgDistance.toFixed(2)} km</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Avg Earnings per Trip</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatUtils.formatCurrency(avgEarnings, 'INR')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Avg Time per Trip</p>
                <p className="text-2xl font-bold">
                  {Math.floor(avgTime)} min
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Trip Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Trip History</CardTitle>
        </CardHeader>
        <CardContent>
          {tripLogs && tripLogs.length > 0 ? (
            <div className="space-y-4">
              {tripLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex justify-between items-center py-3 border-b last:border-0"
                >
                  <div>
                    <p className="font-medium">
                      Order #{log.delivery.order.order_number}
                    </p>
                    <p className="text-sm text-gray-600">
                      {formatUtils.formatDate(log.start_time)} - {formatUtils.formatTime(log.start_time)}
                    </p>
                  </div>
                  <div className="text-right space-y-1">
                    <p className="font-semibold text-green-600">
                      {formatUtils.formatCurrency(log.earnings, 'INR')}
                    </p>
                    <p className="text-sm text-gray-600">
                      {log.distance_km?.toFixed(1)} km · {log.duration_minutes} min
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No trip logs available for this period</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

