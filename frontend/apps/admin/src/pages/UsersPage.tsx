import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'

export default function UsersPage() {
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/users/')
      return response.data.results || response.data
    },
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Users</h1>
      <div className="space-y-4">
        {users?.map((user: any) => (
          <Card key={user.id}>
            <CardContent className="p-6">
              <h3 className="font-semibold">{user.email}</h3>
              <p className="text-sm text-gray-600">{user.role}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

