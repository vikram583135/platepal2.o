import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Button } from '@/packages/ui/components/button'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Tag, Percent, Gift, Smartphone, Building2 } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency } from '@/packages/utils/format'

export default function OffersPage() {
  const [selectedType, setSelectedType] = useState<string | null>(null)

  const { data: offers, isLoading } = useQuery({
    queryKey: ['available-offers', selectedType],
    queryFn: async () => {
      const response = await apiClient.get(`/restaurants/promotions/available/?${selectedType ? `offer_type=${selectedType}` : ''}`)
      return response.data.offers || []
    },
  })

  const getOfferIcon = (type: string) => {
    switch (type) {
      case 'RESTAURANT':
        return <Tag className="w-5 h-5" />
      case 'PLATFORM':
        return <Gift className="w-5 h-5" />
      case 'BANK':
        return <Building2 className="w-5 h-5" />
      case 'UPI':
        return <Smartphone className="w-5 h-5" />
      default:
        return <Percent className="w-5 h-5" />
    }
  }

  const getOfferColor = (type: string) => {
    switch (type) {
      case 'RESTAURANT':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'PLATFORM':
        return 'bg-purple-50 text-purple-700 border-purple-200'
      case 'BANK':
        return 'bg-green-50 text-green-700 border-green-200'
      case 'UPI':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  const groupedOffers = offers?.reduce((acc: any, offer: any) => {
    const type = offer.offer_type || 'OTHER'
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(offer)
    return acc
  }, {}) || {}

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Available Offers</h1>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        <Button
          variant={selectedType === null ? 'default' : 'outline'}
          onClick={() => setSelectedType(null)}
        >
          All Offers
        </Button>
        <Button
          variant={selectedType === 'RESTAURANT' ? 'default' : 'outline'}
          onClick={() => setSelectedType('RESTAURANT')}
        >
          Restaurant Offers
        </Button>
        <Button
          variant={selectedType === 'PLATFORM' ? 'default' : 'outline'}
          onClick={() => setSelectedType('PLATFORM')}
        >
          Platform Offers
        </Button>
        <Button
          variant={selectedType === 'BANK' ? 'default' : 'outline'}
          onClick={() => setSelectedType('BANK')}
        >
          Bank Offers
        </Button>
        <Button
          variant={selectedType === 'UPI' ? 'default' : 'outline'}
          onClick={() => setSelectedType('UPI')}
        >
          UPI Offers
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : offers && offers.length > 0 ? (
        <div className="space-y-6">
          {Object.entries(groupedOffers).map(([type, typeOffers]: [string, any]) => (
            <div key={type}>
              <h2 className="text-xl font-semibold mb-4 capitalize">
                {type.replace('_', ' ')} Offers
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {typeOffers.map((offer: any) => (
                  <Card key={offer.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {getOfferIcon(offer.offer_type)}
                          <CardTitle className="text-lg">{offer.name}</CardTitle>
                        </div>
                        <Badge className={getOfferColor(offer.offer_type)}>
                          {offer.offer_type.replace('_', ' ')}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-4">{offer.description}</p>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Discount:</span>
                          <span className="text-lg font-bold text-primary-600">
                            {offer.discount_display}
                          </span>
                        </div>
                        {offer.minimum_order_amount > 0 && (
                          <div className="text-xs text-gray-500">
                            Min order: {formatCurrency(offer.minimum_order_amount, 'INR')}
                          </div>
                        )}
                        {offer.maximum_discount && (
                          <div className="text-xs text-gray-500">
                            Max discount: {formatCurrency(offer.maximum_discount, 'INR')}
                          </div>
                        )}
                        {offer.cashback_percentage && (
                          <div className="text-xs text-green-600">
                            Cashback: {offer.cashback_percentage}% (max {formatCurrency(offer.cashback_max_amount, 'INR')})
                          </div>
                        )}
                        {offer.applicable_banks && offer.applicable_banks.length > 0 && (
                          <div className="text-xs text-gray-500">
                            Banks: {offer.applicable_banks.join(', ')}
                          </div>
                        )}
                        {offer.applicable_upi_providers && offer.applicable_upi_providers.length > 0 && (
                          <div className="text-xs text-gray-500">
                            UPI: {offer.applicable_upi_providers.join(', ')}
                          </div>
                        )}
                        {offer.restaurant_name && (
                          <div className="text-xs text-gray-500">
                            Restaurant: {offer.restaurant_name}
                          </div>
                        )}
                      </div>

                      {offer.code && (
                        <div className="p-2 bg-gray-50 rounded border border-dashed mb-4">
                          <div className="text-xs text-gray-600 mb-1">Use Code:</div>
                          <div className="font-mono font-semibold text-center">{offer.code}</div>
                        </div>
                      )}

                      <div className="text-xs text-gray-500">
                        Valid until: {new Date(offer.valid_until).toLocaleDateString()}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600">No offers available at the moment</p>
        </div>
      )}
    </div>
  )
}

