import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import type { LucideIcon } from 'lucide-react'
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  ClipboardList,
  FileCheck,
  FileWarning,
  Lock,
  Mail,
  MapPin,
  MapPinned,
  Phone,
  PlusCircle,
  RefreshCw,
  ShieldCheck,
  Timer,
  Upload,
  UserPlus,
} from 'lucide-react'
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import type { LeafletEvent } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Input } from '@/packages/ui/components/input'
import { Badge } from '@/packages/ui/components/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/packages/ui/components/dialog'
import { cn } from '@/packages/utils/cn'
import { useRestaurantId } from '../hooks/useRestaurantId'
import { useRestaurantStore } from '../stores/restaurantStore'
import { useAuthStore } from '../stores/authStore'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const CUISINE_OPTIONS = [
  'INDIAN',
  'JAPANESE',
  'MEDITERRANEAN',
  'ITALIAN',
  'VEGAN',
  'VEGETARIAN',
  'AMERICAN',
  'THAI',
  'CHINESE',
  'MEXICAN',
  'BBQ',
  'FAST_FOOD',
] as const

const RESTAURANT_TYPES = [
  { value: 'NON_VEG', label: 'Non-veg' },
  { value: 'VEG', label: 'Veg' },
  { value: 'PURE_VEG', label: 'Pure veg' },
]

const BRANCH_TYPES = [
  { value: 'MAIN', label: 'Main kitchen' },
  { value: 'CLOUD', label: 'Cloud kitchen' },
  { value: 'PICKUP', label: 'Pickup counter' },
  { value: 'BILLING', label: 'Billing office' },
  { value: 'DINE_IN', label: 'Dine-in outlet' },
]

const MANAGER_ROLES = [
  { value: 'OWNER', label: 'Owner' },
  { value: 'GENERAL_MANAGER', label: 'General Manager' },
  { value: 'KITCHEN_MANAGER', label: 'Kitchen Manager' },
  { value: 'OPERATIONS', label: 'Operations' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'STAFF', label: 'Staff' },
]

const MANAGER_PERMISSIONS = [
  'ORDERS',
  'MENU',
  'INVENTORY',
  'FINANCE',
  'PROMOTIONS',
  'ANALYTICS',
  'COMMUNICATIONS',
  'SETTINGS',
] as const

const DOCUMENT_REQUIREMENTS = [
  {
    type: 'PAN',
    title: 'PAN Card',
    description: 'Upload the PAN card for the registered entity.',
  },
  {
    type: 'GST',
    title: 'GST Certificate',
    description: 'Latest GST registration certificate for tax compliance.',
  },
  {
    type: 'FSSAI',
    title: 'FSSAI License',
    description: 'Mandatory food safety license for the kitchen.',
  },
  {
    type: 'BANK',
    title: 'Bank Statement',
    description: 'Recent bank statement or cancelled cheque for payouts.',
  },
] as const

type DocumentType = (typeof DOCUMENT_REQUIREMENTS)[number]['type']
type StepId = 'account' | 'profile' | 'location' | 'documents' | 'managers'

interface StepConfig {
  id: StepId
  title: string
  description: string
  icon: LucideIcon
}

const STEPS: StepConfig[] = [
  {
    id: 'account',
    title: 'Account & Verification',
    description: 'Secure owner login via OTP and strong password.',
    icon: ShieldCheck,
  },
  {
    id: 'profile',
    title: 'Restaurant Profile',
    description: 'Cuisine, branding, prep times and compliance.',
    icon: ClipboardList,
  },
  {
    id: 'location',
    title: 'Addresses & Branches',
    description: 'Exact kitchen pin, billing info and branches.',
    icon: MapPinned,
  },
  {
    id: 'documents',
    title: 'KYC & Licenses',
    description: 'GST, FSSAI, PAN and payout banking docs.',
    icon: FileCheck,
  },
  {
    id: 'managers',
    title: 'Managers & Staff',
    description: 'Invite team members and assign permissions.',
    icon: UserPlus,
  },
]

const profileSchema = z.object({
  name: z.string().min(3, 'Enter a valid restaurant name'),
  description: z.string().optional(),
  cuisine_type: z.string(),
  cuisine_types: z.array(z.string()).min(1, 'Select at least one cuisine tag'),
  restaurant_type: z.string(),
  phone: z.string().min(8, 'Enter a valid phone number'),
  support_phone: z.string().optional(),
  support_email: z.string().email().or(z.literal('')).optional(),
  manager_contact_name: z.string().min(2, 'Enter manager name'),
  manager_contact_phone: z.string().min(8, 'Enter a valid phone number'),
  manager_contact_email: z.string().email('Enter a valid email'),
  gst_number: z.string().optional(),
  fssai_license_number: z.string().optional(),
  minimum_order_amount: z.coerce.number().nonnegative(),
  cost_for_two: z.coerce.number().optional(),
  logo_image_url: z.string().url().or(z.literal('')).optional(),
  hero_image_url: z.string().url().or(z.literal('')).optional(),
  is_pure_veg: z.boolean().optional(),
})

const locationSchema = z.object({
  address: z.string().min(5, 'Enter a detailed kitchen address'),
  city: z.string().min(2),
  state: z.string().min(2),
  postal_code: z.string().min(4),
  country: z.string().default('India'),
  latitude: z.coerce.number(),
  longitude: z.coerce.number(),
  delivery_radius_km: z.coerce.number().min(1),
  billing_address: z.string().optional(),
  billing_city: z.string().optional(),
  billing_state: z.string().optional(),
  billing_postal_code: z.string().optional(),
  billing_country: z.string().optional(),
})

const operationsSchema = z.object({
  default_prep_time_minutes: z.coerce.number().min(5).max(120),
  sla_threshold_minutes: z.coerce.number().min(15).max(240),
  auto_accept_orders: z.boolean().optional(),
  supports_delivery: z.boolean().optional(),
  supports_pickup: z.boolean().optional(),
  supports_dine_in: z.boolean().optional(),
  max_delivery_distance_km: z.coerce.number().min(1).max(50),
})

const branchSchema = z.object({
  name: z.string().min(3),
  branch_type: z.string(),
  address_line1: z.string().min(5),
  address_line2: z.string().optional(),
  city: z.string().min(2),
  state: z.string().min(2),
  postal_code: z.string().min(4),
  country: z.string().default('India'),
  service_radius_km: z.coerce.number().min(1).max(25),
  contact_number: z.string().optional(),
  contact_email: z.string().email().or(z.literal('')).optional(),
})

const managerSchema = z.object({
  first_name: z.string().min(2),
  last_name: z.string().optional(),
  email: z.string().email(),
  phone: z.string().min(8),
  role: z.string(),
  is_primary: z.boolean().optional(),
  permissions: z.array(z.string()).optional(),
})

const INITIAL_COORDS = {
  lat: 12.9716,
  lng: 77.5946,
}

const LabeledInput = ({
  label,
  ...props
}: { label: string } & React.ComponentProps<typeof Input>) => (
  <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
    {label}
    <Input className="mt-1" {...props} />
  </label>
)

function MapClickHandler({ onChange }: { onChange: (coords: { lat: number; lng: number }) => void }) {
  useMapEvents({
    click(event) {
      onChange({ lat: event.latlng.lat, lng: event.latlng.lng })
    },
  })
  return null
}

const statusStyles: Record<
  string,
  { bg: string; text: string; label: string }
> = {
  APPROVED: { bg: 'bg-green-50', text: 'text-green-700', label: 'Approved' },
  PENDING: { bg: 'bg-yellow-50', text: 'text-yellow-700', label: 'Pending review' },
  REJECTED: { bg: 'bg-red-50', text: 'text-red-700', label: 'Needs re-upload' },
  EXPIRED: { bg: 'bg-orange-50', text: 'text-orange-700', label: 'Expired' },
  MISSING: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Not uploaded' },
}

export default function OnboardingPage() {
  const restaurantId = useRestaurantId()
  const { restaurants, setRestaurants, setSelectedRestaurant } = useRestaurantStore()
  const { user, setUser } = useAuthStore()
  const navigate = useNavigate()

  const [activeStep, setActiveStep] = useState<StepId>('account')
  const [docNumbers, setDocNumbers] = useState<Record<string, string>>({})
  const [branchDialogOpen, setBranchDialogOpen] = useState(false)
  const [managerDialogOpen, setManagerDialogOpen] = useState(false)
  const [otpTarget, setOtpTarget] = useState<'EMAIL_VERIFICATION' | 'PHONE_VERIFICATION'>(
    'EMAIL_VERIFICATION'
  )
  const [otpCode, setOtpCode] = useState('')
  const [otpMessage, setOtpMessage] = useState<string | null>(null)
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
  const [submissionMessage, setSubmissionMessage] = useState<string | null>(null)

  const { data: restaurantsData, isLoading: isLoadingRestaurants, error: restaurantsError } = useQuery({
    queryKey: ['my-restaurants'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/restaurants/restaurants/')
        const payload = Array.isArray(response.data) ? response.data : response.data?.results || []
        if (Array.isArray(payload) && payload.length > 0) {
          setRestaurants(payload)
          // Auto-select first restaurant if none selected
          if (!restaurantId && payload[0]?.id) {
            useRestaurantStore.getState().setSelectedRestaurant(payload[0].id)
          }
        }
        return payload
      } catch (error) {
        console.error('Error loading restaurants:', error)
        return []
      }
    },
  })

  const activeRestaurantId =
    restaurantId ||
    restaurants[0]?.id ||
    (restaurantsData && restaurantsData.length > 0 ? restaurantsData[0].id : null)
  
  // Check if any restaurant has APPROVED onboarding status - redirect to dashboard
  const hasApprovedRestaurant = useMemo(() => {
    const allRestaurants = restaurants.length > 0 ? restaurants : (restaurantsData || [])
    if (Array.isArray(allRestaurants) && allRestaurants.length > 0) {
      const approved = allRestaurants.some((r: any) => r.onboarding_status === 'APPROVED')
      if (approved) {
        console.log('Found approved restaurant, redirecting to dashboard')
      }
      return approved
    }
    return false
  }, [restaurants, restaurantsData])

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['onboarding', activeRestaurantId],
    enabled: Boolean(activeRestaurantId) && !hasApprovedRestaurant,
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/onboarding/', {
        params: activeRestaurantId ? { restaurant_id: activeRestaurantId } : {},
      })
      return response.data
    },
    retry: false,
  })
  
  // Also check onboarding data for approval status
  const onboardingApproved = useMemo(() => {
    return data?.onboarding_status === 'APPROVED'
  }, [data])
  
  // Effect to handle redirect after restaurants load
  useEffect(() => {
    if (!isLoadingRestaurants && !isLoading) {
      const allRestaurants = restaurants.length > 0 ? restaurants : (restaurantsData || [])
      console.log('OnboardingPage - Restaurants loaded:', allRestaurants)
      console.log('OnboardingPage - Checking approval status:', allRestaurants.map((r: any) => ({ id: r.id, name: r.name, status: r.onboarding_status })))
      
      if (Array.isArray(allRestaurants) && allRestaurants.length > 0) {
        // Find approved restaurant
        const approvedRestaurant = allRestaurants.find((r: any) => r.onboarding_status === 'APPROVED')
        console.log('OnboardingPage - Approved restaurant:', approvedRestaurant)
        
        if (approvedRestaurant) {
          // Select the approved restaurant first
          if (!restaurantId || restaurantId !== approvedRestaurant.id) {
            console.log('Selecting approved restaurant:', approvedRestaurant.id)
            setSelectedRestaurant(approvedRestaurant.id)
          }
          
          // Small delay to ensure store is updated before redirect
          setTimeout(() => {
            console.log('Redirecting to dashboard - approved restaurant found')
            navigate('/dashboard', { replace: true })
          }, 100)
          return
        }
        
        // Auto-select first restaurant if none selected
        if (!restaurantId && allRestaurants[0]?.id) {
          console.log('Auto-selecting restaurant:', allRestaurants[0].id)
          setSelectedRestaurant(allRestaurants[0].id)
        }
      }
    }
  }, [isLoadingRestaurants, isLoading, restaurants, restaurantsData, restaurantId, navigate, setSelectedRestaurant, onboardingApproved])

  const profileForm = useForm<z.infer<typeof profileSchema>>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: '',
      description: '',
      cuisine_type: 'INDIAN',
      cuisine_types: ['INDIAN'],
      restaurant_type: 'NON_VEG',
      phone: '',
      support_phone: '',
      support_email: '',
      manager_contact_name: '',
      manager_contact_phone: '',
      manager_contact_email: '',
      gst_number: '',
      fssai_license_number: '',
      minimum_order_amount: 0,
      cost_for_two: undefined,
      logo_image_url: '',
      hero_image_url: '',
      is_pure_veg: false,
    },
  })

  const locationForm = useForm<z.infer<typeof locationSchema>>({
    resolver: zodResolver(locationSchema),
    defaultValues: {
      address: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'India',
      latitude: INITIAL_COORDS.lat,
      longitude: INITIAL_COORDS.lng,
      delivery_radius_km: 5,
      billing_address: '',
      billing_city: '',
      billing_state: '',
      billing_postal_code: '',
      billing_country: 'India',
    },
  })

  const operationsForm = useForm<z.infer<typeof operationsSchema>>({
    resolver: zodResolver(operationsSchema),
    defaultValues: {
      default_prep_time_minutes: 20,
      sla_threshold_minutes: 35,
      auto_accept_orders: false,
      supports_delivery: true,
      supports_pickup: true,
      supports_dine_in: false,
      max_delivery_distance_km: 8,
    },
  })

  const branchForm = useForm<z.infer<typeof branchSchema>>({
    resolver: zodResolver(branchSchema),
    defaultValues: {
      name: '',
      branch_type: 'MAIN',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'India',
      service_radius_km: 5,
      contact_number: '',
      contact_email: '',
    },
  })

  const managerForm = useForm<z.infer<typeof managerSchema>>({
    resolver: zodResolver(managerSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      role: 'GENERAL_MANAGER',
      is_primary: false,
      permissions: MANAGER_PERMISSIONS.slice(0, 4),
    },
  })

  useEffect(() => {
    if (!data) return
    profileForm.reset({
      name: data.restaurant?.name ?? '',
      description: data.restaurant?.description ?? '',
      cuisine_type: data.restaurant?.cuisine_type ?? 'INDIAN',
      cuisine_types:
        (data.restaurant?.cuisine_types?.length ? data.restaurant.cuisine_types : undefined) ??
        [data.restaurant?.cuisine_type ?? 'INDIAN'],
      restaurant_type: data.restaurant?.restaurant_type ?? 'NON_VEG',
      phone: data.restaurant?.phone ?? '',
      support_phone: data.restaurant?.support_phone ?? '',
      support_email: data.restaurant?.support_email ?? '',
      manager_contact_name: data.restaurant?.manager_contact_name ?? '',
      manager_contact_phone: data.restaurant?.manager_contact_phone ?? '',
      manager_contact_email: data.restaurant?.manager_contact_email ?? '',
      gst_number: data.restaurant?.gst_number ?? '',
      fssai_license_number: data.restaurant?.fssai_license_number ?? '',
      minimum_order_amount: Number(data.restaurant?.minimum_order_amount ?? 0),
      cost_for_two:
        data.restaurant?.cost_for_two !== null ? Number(data.restaurant?.cost_for_two) : undefined,
      logo_image_url: data.restaurant?.logo_image_url ?? '',
      hero_image_url: data.restaurant?.hero_image_url ?? '',
      is_pure_veg: Boolean(data.restaurant?.is_pure_veg),
    })
    locationForm.reset({
      address: data.restaurant?.address ?? '',
      city: data.restaurant?.city ?? '',
      state: data.restaurant?.state ?? '',
      postal_code: data.restaurant?.postal_code ?? '',
      country: data.restaurant?.country ?? 'India',
      latitude: Number(data.restaurant?.latitude ?? INITIAL_COORDS.lat),
      longitude: Number(data.restaurant?.longitude ?? INITIAL_COORDS.lng),
      delivery_radius_km: Number(data.restaurant?.delivery_radius_km ?? 5),
      billing_address: data.restaurant?.billing_address ?? data.restaurant?.address ?? '',
      billing_city: data.restaurant?.billing_city ?? data.restaurant?.city ?? '',
      billing_state: data.restaurant?.billing_state ?? data.restaurant?.state ?? '',
      billing_postal_code: data.restaurant?.billing_postal_code ?? data.restaurant?.postal_code ?? '',
      billing_country: data.restaurant?.billing_country ?? data.restaurant?.country ?? 'India',
    })
    operationsForm.reset({
      default_prep_time_minutes:
        data.settings?.default_prep_time_minutes ?? data.restaurant?.estimated_preparation_time ?? 20,
      sla_threshold_minutes: data.settings?.sla_threshold_minutes ?? 35,
      auto_accept_orders: data.settings?.auto_accept_orders ?? false,
      supports_delivery: data.settings?.supports_delivery ?? true,
      supports_pickup: data.settings?.supports_pickup ?? true,
      supports_dine_in: data.settings?.supports_dine_in ?? false,
      max_delivery_distance_km:
        Number(data.settings?.max_delivery_distance_km ?? data.restaurant?.delivery_radius_km ?? 8),
    })
  }, [data, profileForm, locationForm, operationsForm])

  const profileMutation = useMutation({
    mutationFn: async (values: z.infer<typeof profileSchema>) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/onboarding/basic_profile/', {
        ...values,
        restaurant_id: activeRestaurantId,
        cuisine_types: values.cuisine_types.map((tag) => tag.toUpperCase()),
      })
    },
    onSuccess: () => refetch(),
  })

  const locationMutation = useMutation({
    mutationFn: async (values: z.infer<typeof locationSchema>) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/onboarding/location/', {
        ...values,
        restaurant_id: activeRestaurantId,
      })
    },
    onSuccess: () => refetch(),
  })

  const operationsMutation = useMutation({
    mutationFn: async (values: z.infer<typeof operationsSchema>) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/onboarding/operations/', {
        ...values,
        restaurant_id: activeRestaurantId,
      })
    },
    onSuccess: () => refetch(),
  })

  const branchMutation = useMutation({
    mutationFn: async (values: z.infer<typeof branchSchema>) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/branches/', {
        ...values,
        restaurant: activeRestaurantId,
      })
    },
    onSuccess: () => {
      branchForm.reset()
      setBranchDialogOpen(false)
      refetch()
    },
  })

  const managerMutation = useMutation({
    mutationFn: async (values: z.infer<typeof managerSchema>) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/managers/', {
        ...values,
        restaurant: activeRestaurantId,
        permissions: values.permissions ?? [],
      })
    },
    onSuccess: () => {
      managerForm.reset({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        role: 'GENERAL_MANAGER',
        is_primary: false,
        permissions: MANAGER_PERMISSIONS.slice(0, 4),
      })
      setManagerDialogOpen(false)
      refetch()
    },
  })

  const primaryManagerMutation = useMutation({
    mutationFn: async (managerId: number) => {
      return apiClient.patch(`/restaurants/managers/${managerId}/`, { is_primary: true })
    },
    onSuccess: () => refetch(),
  })

  const documentUploadMutation = useMutation({
    mutationFn: async ({
      file,
      documentType,
      documentId,
      documentNumber,
    }: {
      file: File
      documentType: DocumentType
      documentId?: number
      documentNumber?: string
    }) => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      const formData = new FormData()
      formData.append('restaurant', String(activeRestaurantId))
      formData.append('document_type', documentType)
      if (documentNumber) {
        formData.append('document_number', documentNumber)
      }
      formData.append('file', file)
      if (documentId) {
        return apiClient.patch(`/restaurants/documents/${documentId}/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }
      return apiClient.post('/restaurants/documents/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: () => refetch(),
  })

  const sendOtpMutation = useMutation({
    mutationFn: async (target: 'EMAIL_VERIFICATION' | 'PHONE_VERIFICATION') => {
      return apiClient.post('/auth/otp/send/', {
        type: target,
        email: target === 'EMAIL_VERIFICATION' ? user?.email : undefined,
        phone: target === 'PHONE_VERIFICATION' ? user?.phone : undefined,
      })
    },
    onSuccess: (_, target) => {
      setOtpTarget(target)
      setOtpMessage('OTP sent successfully. Check your inbox or SMS (visible in console in dev).')
    },
    onError: (err: any) => {
      setOtpMessage(err.response?.data?.error || 'Unable to send OTP right now.')
    },
  })

  const verifyOtpMutation = useMutation({
    mutationFn: async ({
      code,
      target,
    }: {
      code: string
      target: 'EMAIL_VERIFICATION' | 'PHONE_VERIFICATION'
    }) => {
      return apiClient.post('/auth/otp/verify/', {
        type: target,
        code,
        email: target === 'EMAIL_VERIFICATION' ? user?.email : undefined,
        phone: target === 'PHONE_VERIFICATION' ? user?.phone : undefined,
      })
    },
    onSuccess: (_, variables) => {
      if (!user) return
      const updatedUser = {
        ...user,
        is_email_verified:
          variables.target === 'EMAIL_VERIFICATION' ? true : user?.is_email_verified,
        is_phone_verified:
          variables.target === 'PHONE_VERIFICATION' ? true : user?.is_phone_verified,
      }
      setUser(updatedUser)
      setOtpCode('')
      setOtpMessage('Verification successful. You can proceed to the next step.')
    },
    onError: (err: any) => {
      setOtpMessage(err.response?.data?.error || 'Invalid code. Please try again.')
    },
  })

  const passwordMutation = useMutation({
    mutationFn: async () => {
      return apiClient.post('/auth/users/change_password/', passwordForm)
    },
    onSuccess: () => {
      setPasswordMessage('Password updated successfully.')
      setPasswordForm({ old_password: '', new_password: '' })
    },
    onError: (err: any) => {
      setPasswordMessage(err.response?.data?.error || 'Unable to update password.')
    },
  })

  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!activeRestaurantId) throw new Error('No restaurant selected')
      return apiClient.post('/restaurants/onboarding/submit/', {
        restaurant_id: activeRestaurantId,
      })
    },
    onSuccess: () => {
      setSubmissionMessage('Onboarding submitted for approval. Our team will review shortly.')
      refetch()
    },
    onError: (err: any) => {
      setSubmissionMessage(err.response?.data?.error || 'Submission failed. Please try again.')
    },
  })

  const documentsByType = useMemo<Record<DocumentType, any>>(() => {
    const map = {} as Record<DocumentType, any>
    ;(data?.documents ?? []).forEach((doc: any) => {
      if (!map[doc.document_type as DocumentType]) {
        map[doc.document_type as DocumentType] = doc
      }
    })
    return map
  }, [data?.documents])

  const stepStates = useMemo(
    () => ({
      account: Boolean(user?.is_email_verified && user?.is_phone_verified),
      profile: Boolean(data?.progress?.steps?.profile),
      location: Boolean(data?.progress?.steps?.location),
      documents: Boolean(data?.progress?.steps?.documents),
      managers: Boolean(data?.progress?.steps?.managers),
    }),
    [data?.progress?.steps, user]
  )

  const progressPercentage = data?.progress?.percentage ?? 0
  const onboardingStatus = data?.restaurant?.onboarding_status ?? 'NOT_STARTED'
  const allStepsComplete = Object.values(stepStates).every(Boolean)

  const handleCuisineToggle = (tag: string) => {
    const current = profileForm.getValues('cuisine_types') ?? []
    const next = current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]
    profileForm.setValue('cuisine_types', next.length ? next : [tag], {
      shouldDirty: true,
    })
  }

  const handlePermissionToggle = (permission: string) => {
    const current = managerForm.getValues('permissions') ?? []
    const next = current.includes(permission)
      ? current.filter((item) => item !== permission)
      : [...current, permission]
    managerForm.setValue('permissions', next, { shouldDirty: true })
  }

  const handleDocumentFileChange = (
    event: React.ChangeEvent<HTMLInputElement>,
    documentType: DocumentType,
    existingId?: number
  ) => {
    const file = event.target.files?.[0]
    if (!file) return
    const documentNumber = docNumbers[documentType] || documentsByType[documentType]?.document_number
    documentUploadMutation.mutate({
      file,
      documentType,
      documentId: existingId,
      documentNumber,
    })
    event.target.value = ''
  }

  const copyKitchenToBilling = () => {
    const values = locationForm.getValues()
    locationForm.setValue('billing_address', values.address, { shouldDirty: true })
    locationForm.setValue('billing_city', values.city, { shouldDirty: true })
    locationForm.setValue('billing_state', values.state, { shouldDirty: true })
    locationForm.setValue('billing_postal_code', values.postal_code, { shouldDirty: true })
    locationForm.setValue('billing_country', values.country, { shouldDirty: true })
  }

  const coords = {
    lat: Number(locationForm.watch('latitude') ?? INITIAL_COORDS.lat),
    lng: Number(locationForm.watch('longitude') ?? INITIAL_COORDS.lng),
  }

  const renderAccountStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
            <ShieldCheck className="h-5 w-5 text-rose-500" />
            Verify owner contact
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            {[
              {
                label: 'Owner email',
                value: user?.email,
                verified: user?.is_email_verified,
                target: 'EMAIL_VERIFICATION' as const,
              },
              {
                label: 'Owner phone',
                value: user?.phone || 'Not provided',
                verified: user?.is_phone_verified,
                target: 'PHONE_VERIFICATION' as const,
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-rose-100 p-4 bg-white shadow-sm space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-rose-400">{item.label}</p>
                    <p className="text-base font-semibold text-rose-900">{item.value}</p>
                  </div>
                  <Badge
                    className={cn(
                      'px-3 py-1 text-xs',
                      item.verified ? 'bg-green-100 text-green-700' : 'bg-yellow-50 text-yellow-700'
                    )}
                  >
                    {item.verified ? 'Verified' : 'Pending'}
                  </Badge>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full text-sm"
                  onClick={() => sendOtpMutation.mutate(item.target)}
                  disabled={sendOtpMutation.isPending}
                >
                  {sendOtpMutation.isPending && otpTarget === item.target ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : item.target === 'EMAIL_VERIFICATION' ? (
                    <Mail className="mr-2 h-4 w-4" />
                  ) : (
                    <Phone className="mr-2 h-4 w-4" />
                  )}
                  Send OTP
                </Button>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-dashed border-rose-200 bg-rose-50 p-4 space-y-3">
            <p className="text-sm font-semibold text-rose-900">
              Enter the OTP for {otpTarget === 'EMAIL_VERIFICATION' ? 'email' : 'phone'} verification
            </p>
            <div className="flex flex-col gap-2 md:flex-row">
              <Input
                value={otpCode}
                onChange={(event) => setOtpCode(event.target.value)}
                placeholder="Enter 6-digit code"
                maxLength={6}
              />
              <Button
                type="button"
                className="md:w-40 bg-rose-600 hover:bg-rose-700"
                disabled={!otpCode || verifyOtpMutation.isPending}
                onClick={() => verifyOtpMutation.mutate({ code: otpCode, target: otpTarget })}
              >
                {verifyOtpMutation.isPending ? 'Verifying…' : 'Verify OTP'}
              </Button>
            </div>
            {otpMessage ? <p className="text-xs text-rose-500">{otpMessage}</p> : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
            <Lock className="h-5 w-5 text-rose-500" />
            Update password
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
              Current password
              <Input
                type="password"
                className="mt-1"
                value={passwordForm.old_password}
                onChange={(event) =>
                  setPasswordForm((prev) => ({ ...prev, old_password: event.target.value }))
                }
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
              New password
              <Input
                type="password"
                className="mt-1"
                value={passwordForm.new_password}
                onChange={(event) =>
                  setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))
                }
              />
            </label>
          </div>
          <Button
            type="button"
            className="bg-rose-600 hover:bg-rose-700"
            disabled={!passwordForm.old_password || !passwordForm.new_password || passwordMutation.isPending}
            onClick={() => passwordMutation.mutate()}
          >
            {passwordMutation.isPending ? 'Updating…' : 'Update password'}
          </Button>
          {passwordMessage ? (
            <p className="text-xs text-rose-500">{passwordMessage}</p>
          ) : (
            <p className="text-xs text-rose-400">
              Use a strong password with at least 8 characters, a number and a symbol.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderProfileStep = () => {
    const selectedCuisines = profileForm.watch('cuisine_types') || []
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
              <ClipboardList className="h-5 w-5 text-rose-500" />
              Restaurant basics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={profileForm.handleSubmit((values) => profileMutation.mutate(values))}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Restaurant name
                  <Input className="mt-1" {...profileForm.register('name')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Restaurant type
                  <div className="mt-1 flex flex-wrap gap-2">
                    {RESTAURANT_TYPES.map((type) => {
                      const selected = profileForm.watch('restaurant_type') === type.value
                      return (
                        <button
                          type="button"
                          key={type.value}
                          onClick={() => profileForm.setValue('restaurant_type', type.value)}
                          className={cn(
                            'rounded-full border px-3 py-1 text-xs font-semibold transition',
                            selected
                              ? 'border-rose-600 bg-rose-600 text-white'
                              : 'border-rose-100 text-rose-500'
                          )}
                        >
                          {type.label}
                        </button>
                      )
                    })}
                  </div>
                </label>
              </div>

              <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                Description
                <textarea
                  className="mt-1 w-full rounded-xl border border-rose-100 px-3 py-2 text-sm text-rose-900 focus:outline-none focus:ring-2 focus:ring-rose-200"
                  rows={3}
                  {...profileForm.register('description')}
                />
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Primary cuisine
                  <select
                    className="mt-1 w-full rounded-xl border border-rose-100 bg-white px-3 py-2 text-sm"
                    {...profileForm.register('cuisine_type')}
                  >
                    {CUISINE_OPTIONS.map((cuisine) => (
                      <option key={cuisine} value={cuisine}>
                        {cuisine}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Cuisine tags
                  <div className="mt-1 flex flex-wrap gap-2">
                    {CUISINE_OPTIONS.map((tag) => {
                      const active = selectedCuisines.includes(tag)
                      return (
                        <button
                          type="button"
                          key={tag}
                          className={cn(
                            'rounded-full border px-3 py-1 text-xs font-semibold',
                            active
                              ? 'border-rose-600 bg-rose-600 text-white'
                              : 'border-rose-100 text-rose-500'
                          )}
                          onClick={() => handleCuisineToggle(tag)}
                        >
                          {tag}
                        </button>
                      )
                    })}
                  </div>
                </label>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Phone
                  <Input className="mt-1" {...profileForm.register('phone')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Support phone
                  <Input className="mt-1" {...profileForm.register('support_phone')} />
                </label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Support email
                  <Input className="mt-1" {...profileForm.register('support_email')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Manager email
                  <Input className="mt-1" {...profileForm.register('manager_contact_email')} />
                </label>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Manager name
                  <Input className="mt-1" {...profileForm.register('manager_contact_name')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Manager phone
                  <Input className="mt-1" {...profileForm.register('manager_contact_phone')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Cost for two (₹)
                  <Input
                    className="mt-1"
                    type="number"
                    step="50"
                    {...profileForm.register('cost_for_two', { valueAsNumber: true })}
                  />
                </label>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  GST number
                  <Input className="mt-1" {...profileForm.register('gst_number')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  FSSAI license
                  <Input className="mt-1" {...profileForm.register('fssai_license_number')} />
                </label>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Logo URL
                  <Input className="mt-1" placeholder="https://..." {...profileForm.register('logo_image_url')} />
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Hero / Cover image URL
                  <Input className="mt-1" placeholder="https://..." {...profileForm.register('hero_image_url')} />
                </label>
              </div>

              <div className="flex items-center gap-2 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded text-rose-600"
                  checked={Boolean(profileForm.watch('is_pure_veg'))}
                  onChange={(event) => profileForm.setValue('is_pure_veg', event.target.checked)}
                />
                Mark as pure veg establishment
              </div>

              <Button
                type="submit"
                className="w-full bg-rose-600 hover:bg-rose-700"
                disabled={profileMutation.isPending}
              >
                {profileMutation.isPending ? 'Saving…' : 'Save profile'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
              <Timer className="h-5 w-5 text-rose-500" />
              Prep time & SLA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={operationsForm.handleSubmit((values) => operationsMutation.mutate(values))}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Average prep time (minutes)
                  <input
                    type="range"
                    min={5}
                    max={90}
                    step={5}
                    className="mt-2 w-full"
                    value={operationsForm.watch('default_prep_time_minutes')}
                    onChange={(event) =>
                      operationsForm.setValue('default_prep_time_minutes', Number(event.target.value))
                    }
                  />
                  <span className="text-sm text-rose-600">
                    {operationsForm.watch('default_prep_time_minutes')} minutes
                  </span>
                </label>
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  SLA threshold (minutes)
                  <input
                    type="range"
                    min={15}
                    max={180}
                    step={5}
                    className="mt-2 w-full"
                    value={operationsForm.watch('sla_threshold_minutes')}
                    onChange={(event) =>
                      operationsForm.setValue('sla_threshold_minutes', Number(event.target.value))
                    }
                  />
                  <span className="text-sm text-rose-600">
                    {operationsForm.watch('sla_threshold_minutes')} minutes
                  </span>
                </label>
              </div>
              <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                Max delivery distance
                <div className="mt-1 flex flex-col gap-2 rounded-xl border border-rose-100 p-3">
                  <input
                    type="range"
                    min={1}
                    max={30}
                    step={1}
                    value={operationsForm.watch('max_delivery_distance_km')}
                    onChange={(event) =>
                      operationsForm.setValue('max_delivery_distance_km', Number(event.target.value))
                    }
                  />
                  <span className="text-sm text-rose-600">
                    {operationsForm.watch('max_delivery_distance_km')} km
                  </span>
                </div>
              </label>
              <div className="grid gap-3 md:grid-cols-2 text-sm">
                {[
                  { name: 'auto_accept_orders', label: 'Auto-accept orders' },
                  { name: 'supports_delivery', label: 'Delivery' },
                  { name: 'supports_pickup', label: 'Pickup' },
                  { name: 'supports_dine_in', label: 'Dine-in' },
                ].map((option) => (
                  <label
                    key={option.name}
                    className="flex items-center gap-2 rounded-xl border border-rose-100 px-3 py-2"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(
                        operationsForm.watch(option.name as keyof z.infer<typeof operationsSchema>)
                      )}
                      onChange={(event) =>
                        operationsForm.setValue(
                          option.name as keyof z.infer<typeof operationsSchema>,
                          event.target.checked
                        )
                      }
                    />
                    {option.label}
                  </label>
                ))}
              </div>

              <Button
                type="submit"
                className="w-full bg-rose-600 hover:bg-rose-700"
                disabled={operationsMutation.isPending}
              >
                {operationsMutation.isPending ? 'Saving…' : 'Save prep & SLA'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderLocationStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
            <MapPin className="h-5 w-5 text-rose-500" />
            Kitchen & billing addresses
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={locationForm.handleSubmit((values) => locationMutation.mutate(values))}
          >
            <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
              Kitchen address
              <textarea
                className="mt-1 w-full rounded-xl border border-rose-100 px-3 py-2 text-sm text-rose-900 focus:outline-none focus:ring-2 focus:ring-rose-200"
                rows={2}
                {...locationForm.register('address')}
              />
            </label>
            <div className="grid gap-4 md:grid-cols-3">
              <LabeledInput label="City" {...locationForm.register('city')} />
              <LabeledInput label="State" {...locationForm.register('state')} />
              <LabeledInput label="Postal code" {...locationForm.register('postal_code')} />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <LabeledInput
                label="Latitude"
                type="number"
                step="0.0001"
                {...locationForm.register('latitude', { valueAsNumber: true })}
              />
              <LabeledInput
                label="Longitude"
                type="number"
                step="0.0001"
                {...locationForm.register('longitude', { valueAsNumber: true })}
              />
              <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                Delivery radius ({locationForm.watch('delivery_radius_km')} km)
                <input
                  type="range"
                  className="mt-2 w-full"
                  min={1}
                  max={20}
                  value={Number(locationForm.watch('delivery_radius_km'))}
                  onChange={(event) =>
                    locationForm.setValue('delivery_radius_km', Number(event.target.value))
                  }
                />
              </label>
            </div>
            <div className="rounded-2xl border border-rose-100 bg-white p-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Billing address
                </p>
                <Button type="button" variant="outline" size="sm" onClick={copyKitchenToBilling}>
                  Copy kitchen details
                </Button>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <textarea
                  className="rounded-xl border border-rose-100 px-3 py-2 text-sm text-rose-900 focus:outline-none focus:ring-2 focus:ring-rose-200"
                  rows={2}
                  placeholder="Billing address"
                  {...locationForm.register('billing_address')}
                />
                <div className="grid gap-3">
                  <LabeledInput label="Billing city" {...locationForm.register('billing_city')} />
                  <div className="grid grid-cols-2 gap-3">
                    <LabeledInput label="Billing state" {...locationForm.register('billing_state')} />
                    <LabeledInput label="Pin code" {...locationForm.register('billing_postal_code')} />
                  </div>
                </div>
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-rose-100 bg-rose-50/60 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-400">Map picker</p>
                <div className="mt-2 h-72 overflow-hidden rounded-xl">
                  <MapContainer
                    center={[coords.lat, coords.lng]}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <MapClickHandler
                      onChange={(next) => {
                        locationForm.setValue('latitude', next.lat)
                        locationForm.setValue('longitude', next.lng)
                      }}
                    />
                    <Marker
                      draggable
                      eventHandlers={{
                        dragend: (event: LeafletEvent) => {
                          const marker = event.target
                          const position = marker.getLatLng()
                          locationForm.setValue('latitude', position.lat)
                          locationForm.setValue('longitude', position.lng)
                        },
                      }}
                      position={[coords.lat, coords.lng]}
                    />
                  </MapContainer>
                </div>
                <p className="mt-2 text-xs text-rose-500">
                  Click anywhere on the map to update the exact kitchen location.
                </p>
              </div>
              <div className="rounded-2xl border border-rose-100 p-3 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Delivery settings snapshot
                </p>
                <div className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">
                  <p>
                    Customers within{' '}
                    <strong>{operationsForm.watch('max_delivery_distance_km')} km</strong> radius see your
                    restaurant as deliverable. Fine tune the polygon later in Settings → Service areas.
                  </p>
                </div>
                <ul className="space-y-2 text-sm text-rose-600">
                  <li>• Update billing address for invoice compliance</li>
                  <li>• Delivery radius auto-syncs with customer app and logistics</li>
                  <li>• Use map picker for precise last-mile navigation</li>
                </ul>
              </div>
            </div>
            <Button
              type="submit"
              className="w-full bg-rose-600 hover:bg-rose-700"
              disabled={locationMutation.isPending}
            >
              {locationMutation.isPending ? 'Saving…' : 'Save addresses'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
              <Building2 className="h-5 w-5 text-rose-500" />
              Branches & outlets
            </CardTitle>
            <p className="text-sm text-rose-500">Manage cloud kitchens, dine-in outlets and pickup hubs.</p>
          </div>
          <Button type="button" onClick={() => setBranchDialogOpen(true)}>
            <PlusCircle className="mr-2 h-4 w-4" />
            New branch
          </Button>
        </CardHeader>
        <CardContent>
          {data?.branches?.length ? (
            <div className="grid gap-4 md:grid-cols-2">
              {data.branches.map((branch: any) => (
                <div key={branch.id} className="rounded-2xl border border-rose-100 p-4 bg-white shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-base font-semibold text-rose-900">{branch.name}</p>
                      <p className="text-xs uppercase tracking-wide text-rose-400">{branch.branch_type}</p>
                    </div>
                    {branch.is_primary ? (
                      <Badge className="bg-rose-100 text-rose-600 text-[11px]">Primary</Badge>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm text-rose-600">{branch.address_line1}</p>
                  <p className="text-xs text-rose-400">
                    {branch.city}, {branch.state} • Service radius {branch.service_radius_km} km
                  </p>
                  <div className="mt-2 text-xs text-rose-400">
                    {branch.contact_number && <p>Phone: {branch.contact_number}</p>}
                    {branch.contact_email && <p>Email: {branch.contact_email}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-rose-200 bg-rose-50 p-6 text-center">
              <p className="text-sm text-rose-600">
                Add multiple branches to enable multi-outlet dashboards and branch-level analytics.
              </p>
              <Button type="button" className="mt-3" onClick={() => setBranchDialogOpen(true)}>
                Create first branch
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderDocumentsStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
            <FileCheck className="h-5 w-5 text-rose-500" />
            Required documents
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          {DOCUMENT_REQUIREMENTS.map((doc) => {
            const currentDoc = documentsByType[doc.type]
            const statusKey = currentDoc?.status || 'MISSING'
            const status = statusStyles[statusKey] || statusStyles.MISSING
            return (
              <div
                key={doc.type}
                className="rounded-2xl border border-rose-100 bg-white p-4 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-base font-semibold text-rose-900">{doc.title}</p>
                    <p className="text-xs text-rose-400">{doc.description}</p>
                  </div>
                  <span className={cn('rounded-full px-3 py-1 text-[11px] font-semibold', status.bg, status.text)}>
                    {status.label}
                  </span>
                </div>
                {currentDoc?.rejection_reason ? (
                  <div className="rounded-xl bg-red-50 p-3 text-xs text-red-700">
                    Rejected: {currentDoc.rejection_reason}
                  </div>
                ) : null}
                <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
                  Document number
                  <Input
                    className="mt-1"
                    value={docNumbers[doc.type] ?? currentDoc?.document_number ?? ''}
                    onChange={(event) =>
                      setDocNumbers((prev) => ({ ...prev, [doc.type]: event.target.value }))
                    }
                    placeholder="Enter reference number"
                  />
                </label>
                <div className="flex flex-col gap-2 md:flex-row md:items-center">
                  <input
                    type="file"
                    className="hidden"
                    id={`upload-${doc.type}`}
                    accept=".pdf,image/*"
                    onChange={(event) =>
                      handleDocumentFileChange(event, doc.type, currentDoc?.id)
                    }
                  />
                  <Button
                    type="button"
                    className="w-full bg-rose-600 hover:bg-rose-700"
                    disabled={documentUploadMutation.isPending}
                    onClick={() => document.getElementById(`upload-${doc.type}`)?.click()}
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {currentDoc ? 'Re-upload' : 'Upload'}
                  </Button>
                  {currentDoc?.file ? (
                    <a
                      href={currentDoc.file}
                      target="_blank"
                      rel="noreferrer"
                      className="text-center text-xs text-rose-500 underline"
                    >
                      View latest upload
                    </a>
                  ) : null}
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>
    </div>
  )

  const renderManagersStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-3 text-lg text-rose-900">
              <UserPlus className="h-5 w-5 text-rose-500" />
              Manager profiles
            </CardTitle>
            <p className="text-sm text-rose-500">
              Invite kitchen managers, finance owners and operations leads with role-based access.
            </p>
          </div>
          <Button type="button" onClick={() => setManagerDialogOpen(true)}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add manager
          </Button>
        </CardHeader>
        <CardContent>
          {data?.managers?.length ? (
            <div className="grid gap-4 md:grid-cols-2">
              {data.managers.map((manager: any) => (
                <div key={manager.id} className="rounded-2xl border border-rose-100 bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-base font-semibold text-rose-900">{manager.full_name}</p>
                      <p className="text-xs uppercase tracking-wide text-rose-400">{manager.role}</p>
                    </div>
                    {manager.is_primary ? (
                      <Badge className="bg-green-100 text-green-700 text-[11px]">Primary</Badge>
                    ) : (
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={primaryManagerMutation.isPending}
                        onClick={() => primaryManagerMutation.mutate(manager.id)}
                      >
                        Make primary
                      </Button>
                    )}
                  </div>
                  <div className="mt-3 grid gap-1 text-xs text-rose-500">
                    {manager.email && <p>Email: {manager.email}</p>}
                    {manager.phone && <p>Phone: {manager.phone}</p>}
                    {manager.permissions?.length ? (
                      <p>Permissions: {manager.permissions.join(', ')}</p>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-600">
              No managers added yet. Invite at least one kitchen/finance contact to proceed.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderStep = () => {
    switch (activeStep) {
      case 'account':
        return renderAccountStep()
      case 'profile':
        return renderProfileStep()
      case 'location':
        return renderLocationStep()
      case 'documents':
        return renderDocumentsStep()
      case 'managers':
        return renderManagersStep()
      default:
        return null
    }
  }

  // Redirect to dashboard if user has an approved restaurant
  // Check both restaurant list and onboarding data
  const shouldRedirect = (hasApprovedRestaurant || onboardingApproved) && !isLoading && !isLoadingRestaurants
  
  if (shouldRedirect) {
    console.log('Redirecting to dashboard - approved restaurant found')
    return <Navigate to="/dashboard" replace />
  }

  if (isLoading || isLoadingRestaurants) {
    return (
      <div className="min-h-screen page-background flex items-center justify-center">
        <div className="text-center text-rose-500">Loading onboarding wizard…</div>
      </div>
    )
  }

  // If we have restaurants but no active one selected, try to select the first one
  if (!activeRestaurantId && (restaurants.length > 0 || (restaurantsData && restaurantsData.length > 0))) {
    const firstRestaurant = restaurants[0] || restaurantsData?.[0]
    if (firstRestaurant?.id) {
      useRestaurantStore.getState().setSelectedRestaurant(firstRestaurant.id)
      // Return loading state while selecting
      return (
        <div className="min-h-screen page-background flex items-center justify-center">
          <div className="text-center text-rose-500">Loading…</div>
        </div>
      )
    }
  }

  if (!activeRestaurantId || (error && !restaurantsError)) {
    return (
      <div className="min-h-screen page-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-rose-900">No restaurant selected</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-rose-500">
              Please complete the signup flow or ensure at least one restaurant is assigned to your account.
            </p>
            {restaurantsError && (
              <p className="text-xs text-gray-500 mt-2">
                Error loading restaurants: {restaurantsError.message || 'Unknown error'}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-gradient-to-r from-rose-500 via-rose-600 to-red-500 p-6 text-white shadow-lg">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.4em] text-white/70">Onboarding progress</p>
            <h1 className="text-2xl font-semibold">
              {data?.restaurant?.name || 'Restaurant'} • Status: {onboardingStatus.replace('_', ' ')}
            </h1>
            <p className="text-sm text-white/80">
              Complete every card to unlock the dashboard and start accepting orders.
            </p>
          </div>
          <div className="flex flex-col gap-3 lg:w-1/3">
            <div className="h-2 rounded-full bg-white/30">
              <div
                className="h-full rounded-full bg-white"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <p className="text-sm font-semibold">{progressPercentage}% complete</p>
            <Button
              type="button"
              className="bg-white text-rose-600 hover:bg-rose-50"
              disabled={!allStepsComplete || submitMutation.isPending}
              onClick={() => submitMutation.mutate()}
            >
              {submitMutation.isPending ? 'Submitting…' : 'Submit for approval'}
            </Button>
            {submissionMessage ? (
              <p className="text-xs text-white/80">{submissionMessage}</p>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
        <aside className="space-y-4">
          <Card>
            <CardContent className="space-y-3 p-4">
              {STEPS.map((step) => {
                const Icon = step.icon
                const completed = stepStates[step.id]
                const active = activeStep === step.id
                return (
                  <button
                    key={step.id}
                    onClick={() => setActiveStep(step.id)}
                    className={cn(
                      'flex w-full flex-col rounded-2xl border p-3 text-left transition',
                      active ? 'border-rose-500 bg-rose-50' : 'border-rose-100 bg-white'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-semibold text-rose-900">
                        <Icon className="h-4 w-4 text-rose-500" />
                        {step.title}
                      </div>
                      {completed ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <FileWarning className="h-4 w-4 text-rose-400" />
                      )}
                    </div>
                    <p className="mt-1 text-xs text-rose-500">{step.description}</p>
                  </button>
                )
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-semibold text-rose-900">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                Pending checklist
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-rose-600">
              {Object.entries(stepStates).map(([step, done]) => (
                <div key={step} className="flex items-center gap-2">
                  {done ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <FileWarning className="h-4 w-4 text-rose-400" />
                  )}
                  <span className={done ? 'text-rose-400 line-through' : ''}>
                    {step.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>

        <section>{renderStep()}</section>
      </div>

      <Dialog open={branchDialogOpen} onOpenChange={setBranchDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add branch or kitchen</DialogTitle>
            <DialogDescription>
              Create outlets for different neighborhoods to unlock branch analytics and routing.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-3" onSubmit={branchForm.handleSubmit((values) => branchMutation.mutate(values))}>
            <LabeledInput label="Branch name" {...branchForm.register('name')} />
            <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
              Branch type
              <select
                className="mt-1 w-full rounded-xl border border-rose-100 px-3 py-2 text-sm"
                {...branchForm.register('branch_type')}
              >
                {BRANCH_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>
            <LabeledInput label="Address line 1" {...branchForm.register('address_line1')} />
            <LabeledInput label="Address line 2" {...branchForm.register('address_line2')} />
            <div className="grid gap-3 md:grid-cols-2">
              <LabeledInput label="City" {...branchForm.register('city')} />
              <LabeledInput label="State" {...branchForm.register('state')} />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <LabeledInput label="Postal code" {...branchForm.register('postal_code')} />
              <LabeledInput
                label="Service radius (km)"
                type="number"
                step="1"
                {...branchForm.register('service_radius_km', { valueAsNumber: true })}
              />
            </div>
            <LabeledInput label="Contact number" {...branchForm.register('contact_number')} />
            <LabeledInput label="Contact email" {...branchForm.register('contact_email')} />
            <Button type="submit" className="w-full bg-rose-600 hover:bg-rose-700" disabled={branchMutation.isPending}>
              {branchMutation.isPending ? 'Saving…' : 'Save branch'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={managerDialogOpen} onOpenChange={setManagerDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite manager</DialogTitle>
            <DialogDescription>Assign granular permissions for kitchen, finance or staff.</DialogDescription>
          </DialogHeader>
          <form className="space-y-3" onSubmit={managerForm.handleSubmit((values) => managerMutation.mutate(values))}>
            <div className="grid gap-3 md:grid-cols-2">
              <LabeledInput label="First name" {...managerForm.register('first_name')} />
              <LabeledInput label="Last name" {...managerForm.register('last_name')} />
            </div>
            <LabeledInput label="Email" {...managerForm.register('email')} />
            <LabeledInput label="Phone" {...managerForm.register('phone')} />
            <label className="text-xs font-semibold uppercase tracking-wide text-rose-400">
              Role
              <select
                className="mt-1 w-full rounded-xl border border-rose-100 px-3 py-2 text-sm"
                {...managerForm.register('role')}
              >
                {MANAGER_ROLES.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex items-center gap-2 rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              <input
                type="checkbox"
                checked={Boolean(managerForm.watch('is_primary'))}
                onChange={(event) => managerForm.setValue('is_primary', event.target.checked)}
              />
              Mark as primary manager
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-400">Permissions</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {MANAGER_PERMISSIONS.map((permission) => {
                  const selected = managerForm.watch('permissions')?.includes(permission)
                  return (
                    <button
                      type="button"
                      key={permission}
                      onClick={() => handlePermissionToggle(permission)}
                      className={cn(
                        'rounded-full border px-3 py-1 text-xs font-semibold',
                        selected
                          ? 'border-rose-600 bg-rose-600 text-white'
                          : 'border-rose-100 text-rose-500'
                      )}
                    >
                      {permission}
                    </button>
                  )
                })}
              </div>
            </div>
            <Button
              type="submit"
              className="w-full bg-rose-600 hover:bg-rose-700"
              disabled={managerMutation.isPending}
            >
              {managerMutation.isPending ? 'Inviting…' : 'Invite manager'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

