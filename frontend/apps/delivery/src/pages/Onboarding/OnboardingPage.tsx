import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Input } from '@/packages/ui/components/input'
import { cn } from '@/packages/utils/cn'

interface OnboardingData {
  status: string
  current_step: number
  completion_percentage: number
  profile_completed: boolean
  documents_uploaded: boolean
  bank_details_added: boolean
  background_check_completed: boolean
  agreement_signed: boolean
}

export default function OnboardingPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [currentStep, setCurrentStep] = useState(1)
  const [error, setError] = useState('')

  // Fetch onboarding status
  const { data: onboarding, isLoading } = useQuery({
    queryKey: ['onboarding'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/onboarding/status/')
      return response.data as OnboardingData
    },
    retry: false,
  })

  // Start onboarding mutation
  const startMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/deliveries/onboarding/start/')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding'] })
    }
  })

  // Submit onboarding mutation
  const submitMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post('/deliveries/onboarding/submit/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding'] })
      if (currentStep < 5) {
        setCurrentStep(currentStep + 1)
      } else {
        navigate('/')
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to save. Please try again.')
    }
  })

  useEffect(() => {
    if (onboarding) {
      if (onboarding.status === 'COMPLETED' && onboarding.agreement_signed) {
        navigate('/')
        return
      }
      // Set current step based on progress
      if (!onboarding.profile_completed) {
        setCurrentStep(1)
      } else if (!onboarding.documents_uploaded) {
        setCurrentStep(2)
      } else if (!onboarding.bank_details_added) {
        setCurrentStep(3)
      } else if (!onboarding.background_check_completed) {
        setCurrentStep(4)
      } else if (!onboarding.agreement_signed) {
        setCurrentStep(5)
      }
    }
  }, [onboarding, navigate])

  useEffect(() => {
    if (onboarding && onboarding.status === 'NOT_STARTED') {
      startMutation.mutate()
    }
  }, [onboarding])

  if (isLoading || startMutation.isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading onboarding...</p>
        </div>
      </div>
    )
  }

  const steps = [
    { number: 1, title: 'Personal Info', description: 'Complete your profile' },
    { number: 2, title: 'Documents', description: 'Upload KYC documents' },
    { number: 3, title: 'Bank Details', description: 'Add payout information' },
    { number: 4, title: 'Background Check', description: 'Complete verification' },
    { number: 5, title: 'Agreement', description: 'Review and sign agreement' },
  ]

  const completionPercentage = onboarding?.completion_percentage || 0

  return (
    <div className="min-h-screen delivery-page-background py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-2xl font-bold">Rider Onboarding</h1>
            <span className="text-sm font-medium text-gray-600">
              {completionPercentage}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Step Indicators */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-colors',
                    currentStep > step.number
                      ? 'bg-green-600 text-white'
                      : currentStep === step.number
                      ? 'bg-green-600 text-white ring-4 ring-green-200'
                      : 'bg-gray-200 text-gray-600'
                  )}
                >
                  {currentStep > step.number ? '✓' : step.number}
                </div>
                <div className="mt-2 text-center">
                  <p className="text-xs font-medium text-gray-900">{step.title}</p>
                  <p className="text-xs text-gray-500">{step.description}</p>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 mx-2',
                    currentStep > step.number ? 'bg-green-600' : 'bg-gray-200'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <Card className="mb-8">
          <CardContent className="p-6">
            {currentStep === 1 && (
              <PersonalInfoStep
                onSubmit={(data) => submitMutation.mutate(data)}
                error={error}
              />
            )}
            {currentStep === 2 && (
              <DocumentsStep
                onSubmit={(data) => submitMutation.mutate(data)}
                error={error}
              />
            )}
            {currentStep === 3 && (
              <BankDetailsStep
                onSubmit={(data) => submitMutation.mutate(data)}
                error={error}
              />
            )}
            {currentStep === 4 && (
              <BackgroundCheckStep
                onSubmit={(data) => submitMutation.mutate(data)}
                error={error}
              />
            )}
            {currentStep === 5 && (
              <AgreementStep
                onSubmit={(data) => submitMutation.mutate(data)}
                error={error}
              />
            )}
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
          >
            Previous
          </Button>
          <div className="text-sm text-gray-600">
            Step {currentStep} of {steps.length}
          </div>
        </div>
      </div>
    </div>
  )
}

// Step 1: Personal Info
function PersonalInfoStep({ onSubmit, error }: { onSubmit: (data: any) => void; error: string }) {
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [governmentIdNumber, setGovernmentIdNumber] = useState('')
  const [vehicleType, setVehicleType] = useState('')
  const [vehicleModel, setVehicleModel] = useState('')
  const [vehicleColor, setVehicleColor] = useState('')
  const [vehicleRegNumber, setVehicleRegNumber] = useState('')
  const [driverLicenseNumber, setDriverLicenseNumber] = useState('')
  const [driverLicenseExpiry, setDriverLicenseExpiry] = useState('')
  const [emergencyContactName, setEmergencyContactName] = useState('')
  const [emergencyContactPhone, setEmergencyContactPhone] = useState('')
  const [emergencyContactRelationship, setEmergencyContactRelationship] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      date_of_birth: dateOfBirth,
      government_id_number: governmentIdNumber,
      vehicle_type: vehicleType,
      vehicle_model: vehicleModel,
      vehicle_color: vehicleColor,
      vehicle_registration_number: vehicleRegNumber,
      driver_license_number: driverLicenseNumber,
      driver_license_expiry: driverLicenseExpiry,
      emergency_contact_name: emergencyContactName,
      emergency_contact_phone: emergencyContactPhone,
      emergency_contact_relationship: emergencyContactRelationship,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Date of Birth *
        </label>
        <Input
          type="date"
          value={dateOfBirth}
          onChange={(e) => setDateOfBirth(e.target.value)}
          required
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Government ID Number *
        </label>
        <Input
          type="text"
          value={governmentIdNumber}
          onChange={(e) => setGovernmentIdNumber(e.target.value)}
          required
          placeholder="Enter your ID number"
          className="w-full"
        />
      </div>

      <div className="border-t pt-4">
        <h3 className="font-medium mb-4">Vehicle Information</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vehicle Type *
            </label>
            <select
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">Select type</option>
              <option value="BIKE">Bike</option>
              <option value="SCOOTER">Scooter</option>
              <option value="CAR">Car</option>
              <option value="BICYCLE">Bicycle</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vehicle Model
            </label>
            <Input
              type="text"
              value={vehicleModel}
              onChange={(e) => setVehicleModel(e.target.value)}
              placeholder="e.g., Honda Activa"
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vehicle Color
            </label>
            <Input
              type="text"
              value={vehicleColor}
              onChange={(e) => setVehicleColor(e.target.value)}
              placeholder="e.g., Red"
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Registration Number *
            </label>
            <Input
              type="text"
              value={vehicleRegNumber}
              onChange={(e) => setVehicleRegNumber(e.target.value)}
              required
              placeholder="Vehicle registration"
              className="w-full"
            />
          </div>
        </div>
      </div>

      <div className="border-t pt-4">
        <h3 className="font-medium mb-4">Driver License</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              License Number *
            </label>
            <Input
              type="text"
              value={driverLicenseNumber}
              onChange={(e) => setDriverLicenseNumber(e.target.value)}
              required
              placeholder="License number"
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              License Expiry *
            </label>
            <Input
              type="date"
              value={driverLicenseExpiry}
              onChange={(e) => setDriverLicenseExpiry(e.target.value)}
              required
              className="w-full"
            />
          </div>
        </div>
      </div>

      <div className="border-t pt-4">
        <h3 className="font-medium mb-4">Emergency Contact</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Name *
            </label>
            <Input
              type="text"
              value={emergencyContactName}
              onChange={(e) => setEmergencyContactName(e.target.value)}
              required
              placeholder="Name"
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number *
            </label>
            <Input
              type="tel"
              value={emergencyContactPhone}
              onChange={(e) => setEmergencyContactPhone(e.target.value)}
              required
              placeholder="Phone number"
              className="w-full"
            />
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Relationship *
            </label>
            <Input
              type="text"
              value={emergencyContactRelationship}
              onChange={(e) => setEmergencyContactRelationship(e.target.value)}
              required
              placeholder="e.g., Spouse, Parent, Sibling"
              className="w-full"
            />
          </div>
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      <Button type="submit" className="w-full">Save & Continue</Button>
    </form>
  )
}

// Step 2: Documents
function DocumentsStep({ onSubmit, error }: { onSubmit: (data: any) => void; error: string }) {
  const [governmentIdFile, setGovernmentIdFile] = useState<File | null>(null)
  const [selfiePhoto, setSelfiePhoto] = useState<File | null>(null)
  const [vehicleRegistrationFile, setVehicleRegistrationFile] = useState<File | null>(null)
  const [driverLicenseFile, setDriverLicenseFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = (setter: (file: File | null) => void) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setter(file)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUploading(true)

    const formData = new FormData()
    if (governmentIdFile) formData.append('government_id_file', governmentIdFile)
    if (selfiePhoto) formData.append('selfie_photo', selfiePhoto)
    if (vehicleRegistrationFile) formData.append('vehicle_registration_file', vehicleRegistrationFile)
    if (driverLicenseFile) formData.append('driver_license_file', driverLicenseFile)

    try {
      // Upload profile first
      if (formData.has('government_id_file') || formData.has('selfie_photo') || 
          formData.has('vehicle_registration_file') || formData.has('driver_license_file')) {
        const profileResponse = await apiClient.patch('/deliveries/profiles/me/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }
      
      onSubmit({})
    } catch (err: any) {
      console.error('Upload error:', err)
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Government ID Document *
          </label>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileChange(setGovernmentIdFile)}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
          {governmentIdFile && (
            <p className="mt-1 text-sm text-gray-600">Selected: {governmentIdFile.name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Selfie Photo *
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange(setSelfiePhoto)}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
          {selfiePhoto && (
            <p className="mt-1 text-sm text-gray-600">Selected: {selfiePhoto.name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Vehicle Registration Document *
          </label>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileChange(setVehicleRegistrationFile)}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
          {vehicleRegistrationFile && (
            <p className="mt-1 text-sm text-gray-600">Selected: {vehicleRegistrationFile.name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Driver License Document *
          </label>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileChange(setDriverLicenseFile)}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
          {driverLicenseFile && (
            <p className="mt-1 text-sm text-gray-600">Selected: {driverLicenseFile.name}</p>
          )}
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      <Button type="submit" className="w-full" disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload & Continue'}
      </Button>
    </form>
  )
}

// Step 3: Bank Details
function BankDetailsStep({ onSubmit, error }: { onSubmit: (data: any) => void; error: string }) {
  const [bankName, setBankName] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [accountHolderName, setAccountHolderName] = useState('')
  const [ifscCode, setIfscCode] = useState('')
  const [branchName, setBranchName] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      // Create or update bank details
      await apiClient.post('/deliveries/bank-details/', {
        bank_name: bankName,
        account_number: accountNumber,
        account_holder_name: accountHolderName,
        ifsc_code: ifscCode,
        branch_name: branchName,
      })
      
      onSubmit({})
    } catch (err: any) {
      console.error('Bank details error:', err)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Bank Details for Payouts</h2>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Bank Name *
        </label>
        <Input
          type="text"
          value={bankName}
          onChange={(e) => setBankName(e.target.value)}
          required
          placeholder="Enter bank name"
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Account Number *
        </label>
        <Input
          type="text"
          value={accountNumber}
          onChange={(e) => setAccountNumber(e.target.value)}
          required
          placeholder="Enter account number"
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Account Holder Name *
        </label>
        <Input
          type="text"
          value={accountHolderName}
          onChange={(e) => setAccountHolderName(e.target.value)}
          required
          placeholder="Name as in bank account"
          className="w-full"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            IFSC Code *
          </label>
          <Input
            type="text"
            value={ifscCode}
            onChange={(e) => setIfscCode(e.target.value.toUpperCase())}
            required
            placeholder="IFSC code"
            className="w-full"
            maxLength={11}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Branch Name
          </label>
          <Input
            type="text"
            value={branchName}
            onChange={(e) => setBranchName(e.target.value)}
            placeholder="Branch name"
            className="w-full"
          />
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      <Button type="submit" className="w-full">Save & Continue</Button>
    </form>
  )
}

// Step 4: Background Check
function BackgroundCheckStep({ onSubmit, error }: { onSubmit: (data: any) => void; error: string }) {
  const { data: backgroundCheck } = useQuery({
    queryKey: ['background-check'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/background-checks/')
      return response.data.results?.[0] || response.data
    },
  })

  useEffect(() => {
    if (backgroundCheck?.status === 'APPROVED') {
      onSubmit({})
    }
  }, [backgroundCheck, onSubmit])

  const status = backgroundCheck?.status || 'PENDING'

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Background Check</h2>
      
      <div className="text-center py-8">
        {status === 'PENDING' && (
          <>
            <div className="text-4xl mb-4">⏳</div>
            <h3 className="text-lg font-semibold mb-2">Background Check Pending</h3>
            <p className="text-gray-600 mb-4">
              Your background check is being processed. This usually takes 1-3 business days.
            </p>
            <p className="text-sm text-gray-500">
              We'll notify you once it's complete.
            </p>
          </>
        )}
        {status === 'IN_PROGRESS' && (
          <>
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold mb-2">Background Check In Progress</h3>
            <p className="text-gray-600 mb-4">
              We're currently verifying your information. Please wait.
            </p>
          </>
        )}
        {status === 'APPROVED' && (
          <>
            <div className="text-4xl mb-4">✅</div>
            <h3 className="text-lg font-semibold mb-2 text-green-600">Background Check Approved</h3>
            <p className="text-gray-600 mb-4">
              Your background check has been completed and approved.
            </p>
            <Button onClick={() => onSubmit({})}>Continue</Button>
          </>
        )}
        {status === 'REJECTED' && (
          <>
            <div className="text-4xl mb-4">❌</div>
            <h3 className="text-lg font-semibold mb-2 text-red-600">Background Check Rejected</h3>
            <p className="text-gray-600 mb-4">
              {backgroundCheck?.rejection_reason || 'Your background check could not be completed.'}
            </p>
            <p className="text-sm text-gray-500">
              Please contact support for assistance.
            </p>
          </>
        )}
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
    </div>
  )
}

// Step 5: Agreement
function AgreementStep({ onSubmit, error }: { onSubmit: (data: any) => void; error: string }) {
  const { data: agreement } = useQuery({
    queryKey: ['rider-agreement'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/agreements/latest/')
      return response.data
    },
  })

  const [accepted, setAccepted] = useState(false)

  const acceptMutation = useMutation({
    mutationFn: async () => {
      if (agreement) {
        const response = await apiClient.post(`/deliveries/agreements/${agreement.id}/accept/`)
        return response.data
      }
    },
    onSuccess: () => {
      onSubmit({})
    }
  })

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Rider Agreement</h2>
      
      {agreement && (
        <div className="bg-gray-50 p-6 rounded-lg max-h-96 overflow-y-auto mb-4">
          <h3 className="font-semibold mb-2">Version {agreement.agreement_version}</h3>
          <div className="text-sm text-gray-700 whitespace-pre-wrap">
            {agreement.agreement_text || 'Please review and accept the rider agreement.'}
          </div>
        </div>
      )}

      <div className="flex items-start space-x-3">
        <input
          type="checkbox"
          id="accept"
          checked={accepted}
          onChange={(e) => setAccepted(e.target.checked)}
          required
          className="mt-1 w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
        />
        <label htmlFor="accept" className="text-sm text-gray-700">
          I have read and agree to the terms and conditions of the Rider Agreement *
        </label>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      <Button
        onClick={() => acceptMutation.mutate()}
        disabled={!accepted || acceptMutation.isPending}
        className="w-full"
      >
        {acceptMutation.isPending ? 'Processing...' : 'Accept & Complete Onboarding'}
      </Button>
    </div>
  )
}

