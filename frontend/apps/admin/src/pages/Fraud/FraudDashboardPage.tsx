import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { AlertTriangle, Shield } from 'lucide-react'

interface FraudFlag {
  id: number
  user_id: number | null
  order_id: number | null
  risk_score: number
  reason: string
  status: string
  created_at: string
}

export default function FraudDashboardPage() {
  const { data: dashboard } = useQuery({
    queryKey: ['fraud-dashboard'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/fraud/dashboard/')
      return response.data
    },
  })

  const { data: flags } = useQuery({
    queryKey: ['fraud-flags'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/fraud/flags/')
      return response.data
    },
  })

  const reviewMutation = useMutation({
    mutationFn: async ({ flagId, status, notes }: { flagId: number; status: string; notes?: string }) => {
      return apiClient.post('/admin/fraud/review_flag/', {
        flag_id: flagId,
        status,
        notes
      })
    },
    onSuccess: () => {
      alert('Flag reviewed successfully')
    },
  })

  const columns: Column<FraudFlag>[] = [
    {
      key: 'risk_score',
      header: 'Risk Score',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <span className={`font-bold ${
            row.risk_score >= 80 ? 'text-red-600' :
            row.risk_score >= 60 ? 'text-yellow-600' :
            'text-green-600'
          }`}>
            {row.risk_score}
          </span>
        </div>
      ),
      sortable: true,
    },
    {
      key: 'reason',
      header: 'Reason',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.reason}>
          {row.reason}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.status === 'CONFIRMED' ? 'bg-red-100 text-red-800' :
          row.status === 'FALSE_POSITIVE' ? 'bg-green-100 text-green-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Flagged At',
      accessor: (row) => new Date(row.created_at).toLocaleString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fraud Detection</h1>
        <p className="text-gray-600">Monitor and manage fraud flags</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">Flags Today</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.flags_today || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">High Risk Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-600">{dashboard?.high_risk_pending || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">Confirmed Fraud</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.confirmed_fraud_today || 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Fraud Flags</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={flags || []}
            columns={columns}
            pageSize={20}
          />
        </CardContent>
      </Card>
    </div>
  )
}

