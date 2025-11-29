import { useState, useEffect } from 'react'
import { CreditCard, Smartphone, Wallet, Banknote, Building2 } from 'lucide-react'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'

interface PaymentMethodSelectorProps {
  selectedMethod: string | null
  onSelectMethod: (method: string) => void
  savedCards?: any[]
  onCardSelect?: (card: any) => void
  selectedCard?: any
  onPaymentDetailsChange?: (details: any) => void
  disabled?: boolean
}

export default function PaymentMethodSelector({
  selectedMethod,
  onSelectMethod,
  savedCards = [],
  onCardSelect,
  selectedCard,
  onPaymentDetailsChange,
  disabled = false,
}: PaymentMethodSelectorProps) {
  const [showCardForm, setShowCardForm] = useState(false)
  const [cardData, setCardData] = useState({
    number: '',
    expiry: '',
    cvv: '',
    name: '',
    save_card: false,
  })
  const [upiId, setUpiId] = useState('')
  const [walletProvider, setWalletProvider] = useState('paytm')

  // Notify parent of payment details changes
  useEffect(() => {
    if (!onPaymentDetailsChange) return

    if (selectedMethod === 'CARD' && selectedCard) {
      // Using saved card
      onPaymentDetailsChange({ cardId: selectedCard.id })
    } else if (selectedMethod === 'CARD' && cardData.number && cardData.expiry && cardData.cvv && cardData.name) {
      // New card entered
      onPaymentDetailsChange({
        cardData: {
          number: cardData.number,
          expiry: cardData.expiry,
          cvv: cardData.cvv,
          name: cardData.name,
          save_card: cardData.save_card,
        },
      })
    } else if (selectedMethod === 'UPI' && upiId) {
      onPaymentDetailsChange({ upiId })
    } else if (selectedMethod === 'WALLET' && walletProvider) {
      onPaymentDetailsChange({ walletProvider })
    } else if (selectedMethod === 'CASH' || selectedMethod === 'NET_BANKING') {
      onPaymentDetailsChange(null)
    } else {
      onPaymentDetailsChange(null)
    }
  }, [selectedMethod, selectedCard, cardData, upiId, walletProvider, onPaymentDetailsChange])

  const paymentMethods = [
    { id: 'CARD', label: 'Credit/Debit Card', icon: CreditCard },
    { id: 'UPI', label: 'UPI', icon: Smartphone },
    { id: 'WALLET', label: 'Wallet', icon: Wallet },
    { id: 'NET_BANKING', label: 'Net Banking', icon: Building2 },
    { id: 'CASH', label: 'Cash on Delivery', icon: Banknote },
  ]

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Select Payment Method</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {paymentMethods.map((method) => {
          const Icon = method.icon
          return (
            <button
              key={method.id}
              type="button"
              onClick={() => onSelectMethod(method.id)}
              disabled={disabled}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                selectedMethod === method.id
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-300'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <Icon className="w-6 h-6 mb-2 text-primary-600" />
              <div className="font-medium text-sm">{method.label}</div>
            </button>
          )
        })}
      </div>

      {/* Saved Cards */}
      {selectedMethod === 'CARD' && savedCards.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Saved Cards</h4>
          <div className="space-y-2">
            {savedCards.map((card) => (
              <button
                key={card.id}
                type="button"
                onClick={() => onCardSelect?.(card)}
                disabled={disabled}
                className={`w-full p-3 border rounded-lg text-left ${
                  selectedCard?.id === card.id
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-300'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">**** **** **** {card.last4}</div>
                    <div className="text-sm text-gray-600">{card.brand} • Expires {card.exp_month}/{card.exp_year}</div>
                  </div>
                  {selectedCard?.id === card.id && (
                    <Badge>Selected</Badge>
                  )}
                </div>
              </button>
            ))}
          </div>
          <Button
            type="button"
            variant="outline"
            className="mt-2"
            onClick={() => setShowCardForm(true)}
            disabled={disabled}
          >
            Use New Card
          </Button>
        </div>
      )}

      {/* Card Form */}
      {selectedMethod === 'CARD' && (showCardForm || (!selectedCard && savedCards.length === 0)) && (
        <Card className="mt-4">
          <CardContent className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Card Number</label>
              <Input
                type="text"
                placeholder="1234 5678 9012 3456"
                value={cardData.number}
                onChange={(e) => setCardData({ ...cardData, number: e.target.value })}
                maxLength={19}
                disabled={disabled}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Expiry (MM/YY)</label>
                <Input
                  type="text"
                  placeholder="12/25"
                  value={cardData.expiry}
                  onChange={(e) => setCardData({ ...cardData, expiry: e.target.value })}
                  maxLength={5}
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">CVV</label>
                <Input
                  type="text"
                  placeholder="123"
                  value={cardData.cvv}
                  onChange={(e) => setCardData({ ...cardData, cvv: e.target.value })}
                  maxLength={4}
                  disabled={disabled}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cardholder Name</label>
              <Input
                type="text"
                placeholder="John Doe"
                value={cardData.name}
                onChange={(e) => setCardData({ ...cardData, name: e.target.value })}
                disabled={disabled}
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="save_card"
                checked={cardData.save_card}
                onChange={(e) => setCardData({ ...cardData, save_card: e.target.checked })}
              />
              <label htmlFor="save_card" className="text-sm text-gray-700">
                Save card for future payments
              </label>
            </div>
          </CardContent>
        </Card>
      )}

      {/* UPI Form */}
      {selectedMethod === 'UPI' && (
        <Card className="mt-4">
          <CardContent className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">UPI ID</label>
              <Input
                type="text"
                placeholder="yourname@paytm"
                value={upiId}
                onChange={(e) => setUpiId(e.target.value)}
                disabled={disabled}
              />
            </div>
            <div className="text-sm text-gray-600">
              Popular UPI Apps: Paytm, Google Pay, PhonePe, BHIM
            </div>
          </CardContent>
        </Card>
      )}

      {/* Wallet Form */}
      {selectedMethod === 'WALLET' && (
        <Card className="mt-4">
          <CardContent className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Select Wallet</label>
              <select
                value={walletProvider}
                onChange={(e) => setWalletProvider(e.target.value)}
                className="w-full p-2 border rounded-lg"
                disabled={disabled}
              >
                <option value="paytm">Paytm</option>
                <option value="phonepe">PhonePe</option>
                <option value="amazonpay">Amazon Pay</option>
                <option value="freecharge">FreeCharge</option>
              </select>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Net Banking */}
      {selectedMethod === 'NET_BANKING' && (
        <Card className="mt-4">
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">
              Select your bank during payment confirmation
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cash on Delivery */}
      {selectedMethod === 'CASH' && (
        <Card className="mt-4">
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">
              Pay cash when your order is delivered
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

