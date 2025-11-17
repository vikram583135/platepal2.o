import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'

export default function OrdersPage() {
  const { data: deliveries } = useQuery({
    queryKey: ['deliveries'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/deliveries/')
      return response.data.results || response.data
    },
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Delivery Orders</h1>
      <div className="space-y-4">
        {deliveries?.map((delivery: any) => (
          <Card key={delivery.id}>
            <CardContent className="p-6">
              <h3 className="font-semibold">Order #{delivery.order?.order_number}</h3>
              <p className="text-sm text-gray-600">{delivery.status}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

