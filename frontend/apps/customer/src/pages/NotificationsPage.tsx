import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Bell, CheckCircle2, Package, Truck, Utensils, CreditCard, Tag, Star, XCircle, AlertCircle, Trash2, CheckCheck } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatDate } from '@/packages/utils/format'
import { useNavigate } from 'react-router-dom'

const iconMap: Record<string, any> = {
  package: Package,
  'check-circle': CheckCircle2,
  utensils: Utensils,
  truck: Truck,
  'check-circle-2': CheckCircle2,
  'x-circle': XCircle,
  'credit-card': CreditCard,
  'alert-circle': AlertCircle,
  tag: Tag,
  star: Star,
  bell: Bell,
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: notifications, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await apiClient.get('/notifications/notifications/recent/')
      return response.data.notifications || []
    },
  })

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      const response = await apiClient.get('/notifications/notifications/unread_count/')
      return response.data.count || 0
    },
  })

  const markReadMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.post(`/notifications/notifications/${id}/mark_read/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/notifications/notifications/mark_all_read/')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] })
    },
  })

  const clearAllMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.delete('/notifications/notifications/clear_all/')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const handleNotificationClick = (notification: any) => {
    markReadMutation.mutate(notification.id)
    
    // Navigate based on notification type
    if (notification.data?.order_id) {
      navigate(`/orders/${notification.data.order_id}`)
    } else if (notification.type === 'PROMOTION' && notification.data?.offer_id) {
      navigate('/offers')
    } else if (notification.type === 'REVIEW_REQUEST' && notification.data?.order_id) {
      navigate(`/orders/${notification.data.order_id}`)
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-32 w-full mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const unreadNotifications = notifications?.filter((n: any) => !n.is_read) || []
  const readNotifications = notifications?.filter((n: any) => n.is_read) || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Notifications</h1>
          {unreadCount > 0 && (
            <p className="text-gray-600">{unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}</p>
          )}
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <Button
              variant="outline"
              onClick={() => markAllReadMutation.mutate()}
              disabled={markAllReadMutation.isPending}
            >
              <CheckCheck className="w-4 h-4 mr-2" />
              Mark All Read
            </Button>
          )}
          {readNotifications.length > 0 && (
            <Button
              variant="outline"
              onClick={() => clearAllMutation.mutate()}
              disabled={clearAllMutation.isPending}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear Read
            </Button>
          )}
        </div>
      </div>

      {notifications && notifications.length > 0 ? (
        <div className="space-y-4">
          {/* Unread Notifications */}
          {unreadNotifications.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Unread</h2>
              <div className="space-y-3">
                {unreadNotifications.map((notification: any) => {
                  const IconComponent = iconMap[notification.icon] || Bell
                  return (
                    <Card
                      key={notification.id}
                      className={`cursor-pointer hover:shadow-md transition-shadow ${
                        !notification.is_read ? 'border-primary-300 bg-primary-50' : ''
                      }`}
                      onClick={() => handleNotificationClick(notification)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div className={`p-2 rounded-full ${
                            !notification.is_read ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'
                          }`}>
                            <IconComponent className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-start justify-between mb-1">
                              <h3 className="font-semibold">{notification.title}</h3>
                              {!notification.is_read && (
                                <Badge variant="default" className="ml-2">New</Badge>
                              )}
                            </div>
                            <p className="text-gray-700 text-sm mb-2">{notification.message}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>{formatDate(notification.created_at)}</span>
                              {notification.sent_via_push && <span>• Push</span>}
                              {notification.sent_via_email && <span>• Email</span>}
                              {notification.sent_via_sms && <span>• SMS</span>}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>
          )}

          {/* Read Notifications */}
          {readNotifications.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Earlier</h2>
              <div className="space-y-3">
                {readNotifications.map((notification: any) => {
                  const IconComponent = iconMap[notification.icon] || Bell
                  return (
                    <Card
                      key={notification.id}
                      className="cursor-pointer hover:shadow-md transition-shadow opacity-75"
                      onClick={() => handleNotificationClick(notification)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div className="p-2 rounded-full bg-gray-100 text-gray-600">
                            <IconComponent className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold mb-1">{notification.title}</h3>
                            <p className="text-gray-700 text-sm mb-2">{notification.message}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>{formatDate(notification.created_at)}</span>
                              {notification.sent_via_push && <span>• Push</span>}
                              {notification.sent_via_email && <span>• Email</span>}
                              {notification.sent_via_sms && <span>• SMS</span>}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No notifications yet</p>
        </div>
      )}
    </div>
  )
}

