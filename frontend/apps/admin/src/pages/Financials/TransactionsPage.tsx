import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'

interface Transaction {
  id: number
  order: { order_number: string }
  user: { email: string }
  amount: string
  status: string
  method_type: string
  transaction_id: string
  created_at: string
}

export default function TransactionsPage() {
  const { data: transactions, isLoading } = useQuery({
    queryKey: ['admin-transactions'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/')
      return response.data.results || response.data
    },
  })

  const columns: Column<Transaction>[] = [
    {
      key: 'transaction_id',
      header: 'Transaction ID',
      accessor: (row) => row.transaction_id || 'N/A',
      sortable: true,
    },
    {
      key: 'order',
      header: 'Order',
      accessor: (row) => row.order?.order_number || 'N/A',
    },
    {
      key: 'user',
      header: 'User',
      accessor: (row) => row.user?.email || 'N/A',
    },
    {
      key: 'amount',
      header: 'Amount',
      accessor: (row) => `$${parseFloat(row.amount).toFixed(2)}`,
      sortable: true,
    },
    {
      key: 'method',
      header: 'Method',
      accessor: (row) => row.method_type,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
          row.status === 'FAILED' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Date',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-600">View all payment transactions</p>
        </div>
        <CSVExporter
          data={transactions || []}
          filename={`transactions-${new Date().toISOString().split('T')[0]}.csv`}
        />
      </div>

      <DataTable
        data={transactions || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

