import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { AuditTimeline, AuditEvent } from '@/packages/ui/components/AuditTimeline'
import { ArrowLeft, Ban, Unlock, Key, Mail, Phone, MapPin } from 'lucide-react'

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: userData, isLoading } = useQuery({
    queryKey: ['admin-user', id],
    queryFn: async () => {
      const response = await apiClient.get(`/admin/management/users/${id}/profile/`)
      return response.data
    },
  })

  const user = userData?.user

  const orders = userData?.orders || []

  const { data: auditLogs } = useQuery({
    queryKey: ['user-audit-logs', id],
    queryFn: async () => {
      const response = await apiClient.get(`/admin/management/users/${id}/activity/`)
      return response.data
    },
    enabled: !!id,
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return <div>User not found</div>
  }

  const auditEvents: AuditEvent[] = (auditLogs || []).map((log: any) => ({
    id: log.id.toString(),
    action: log.action,
    user: log.user_email,
    timestamp: log.created_at,
    beforeState: log.before_state,
    afterState: log.after_state,
    reason: log.reason,
    metadata: log.metadata,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/users')}
          className="p-2 hover:bg-gray-100 rounded-md"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {user.first_name} {user.last_name}
          </h1>
          <p className="text-gray-600">{user.email}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-gray-500" />
              <span className="text-gray-700">{user.email}</span>
            </div>
            {user.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700">{user.phone}</span>
              </div>
            )}
            <div>
              <span className="text-sm text-gray-500">Role:</span>
              <span className="ml-2 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                {user.role}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-500">Status:</span>
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {user.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-500">Email Verified:</span>
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                user.is_email_verified ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {user.is_email_verified ? 'Yes' : 'No'}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-500">Joined:</span>
              <span className="ml-2 text-gray-700">
                {new Date(user.date_joined).toLocaleDateString()}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <button className="w-full flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
              <Ban className="w-4 h-4" />
              Ban User
            </button>
            <button className="w-full flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
              <Unlock className="w-4 h-4" />
              Unban User
            </button>
            <button className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              <Key className="w-4 h-4" />
              Reset Password
            </button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Order History</CardTitle>
        </CardHeader>
        <CardContent>
          {orders && orders.length > 0 ? (
            <div className="space-y-2">
              {orders.slice(0, 10).map((order: any) => (
                <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{order.order_number}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">${order.total_amount}</div>
                    <div className="text-sm text-gray-500">{order.status}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No orders found</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Audit Log</CardTitle>
        </CardHeader>
        <CardContent>
          <AuditTimeline events={auditEvents} />
        </CardContent>
      </Card>
    </div>
  )
}

