"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  ArrowLeft,
  FileStack,
  GraduationCap,
  Users,
  AlertCircle,
  Calendar,
  Clock,
  User,
  Hash,
  Plus
} from "lucide-react"
import { ShadcnRequestsTree } from "@/components/requests/ShadcnRequestsTree"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface RequestType {
  id: string
  name: string
  description: string
  category: string
  table_name: string
  total_count: number
  recent_count: number
}

interface RequestCategory {
  id: string
  name: string
  description: string
  icon: string
  requests: RequestType[]
  total_count: number
}

interface DetailedRequest {
  id: string
  type?: string
  type_id?: string
  serial?: string
  order_date?: string
  request_date?: string
  reservation_date?: string
  status?: string | number
  type_name?: string
  type_name_en?: string
  people_count?: number
  status_name?: string
  teacher_id?: string
  person_id?: string
  resource_edition_id?: string
  active?: boolean | number
  // Person information fields
  firstname?: string
  lastname?: string
  patronymic?: string
  pincode?: string
  birthdate?: string
  gender_name?: string
  citizenship_name?: string
  nationality_name?: string
  education_type_name?: string
  score?: number
}

interface CategoryDetails {
  category: string
  name: string
  total_count: number
  requests: DetailedRequest[]
}

const iconMap = {
  GraduationCap,
  Users,
  AlertCircle,
  FileStack
}

export default function RequestsPage() {
  const router = useRouter()
  const [selectedCategory, setSelectedCategory] = useState<RequestCategory | null>(null)
  const [categoryDetails, setCategoryDetails] = useState<CategoryDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [creating, setCreating] = useState(false)

  // Form state for creating new request
  const [newRequest, setNewRequest] = useState({
    student_id: '',
    request_type: 'official',
    delivery_method: 'email',
    purpose: '',
    copies_requested: 1,
    rush_processing: false,
    recipient_name: '',
    recipient_organization: '',
    notes: ''
  })

  const handleCategorySelect = async (category: RequestCategory) => {
    setSelectedCategory(category)
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE_URL}/requests/category/${category.id}`
      )
      if (!response.ok) {
        throw new Error(`Failed to fetch category details: ${response.statusText}`)
      }
      
      // Get the response as text first to avoid automatic number parsing
      const text = await response.text()
      
      // Use a custom JSON parser that preserves large integers as strings
      const data = JSON.parse(text, (key, value) => {
        // Handle all numeric IDs as strings to preserve precision
        if (key === 'id' && typeof value === 'number') {
          return value.toString()
        }
        // Convert any large numbers to strings to preserve precision
        if (typeof value === 'number' && (value > Number.MAX_SAFE_INTEGER || value < Number.MIN_SAFE_INTEGER)) {
          return value.toString()
        }
        // Also handle numeric strings that might be large integers
        if (typeof value === 'string' && /^\d{15,}$/.test(value)) {
          return value // Keep as string
        }
        return value
      })
      
      // Ensure all request IDs are strings
      if (data.requests) {
        data.requests = data.requests.map((request: DetailedRequest) => ({
          ...request,
          id: String(request.id) // Force conversion to string
        }))
      }
      
      // Debug: Log the first request to see what data we're getting
      if (data.requests && data.requests.length > 0) {
        console.log('First request data:', data.requests[0])
      }
      
      setCategoryDetails(data)
    } catch (err) {
      console.error("Error fetching category details:", err)
      setError(err instanceof Error ? err.message : "Unknown error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleBackToTree = () => {
    setSelectedCategory(null)
    setCategoryDetails(null)
    setError(null)
  }

  const handleCreateRequest = async () => {
    if (!newRequest.student_id.trim()) {
      alert('Please enter a student ID')
      return
    }

    setCreating(true)
    try {
      const response = await fetch(`${API_BASE_URL}/requests/transcript-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newRequest)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create request')
      }

      const data = await response.json()
      alert(`Request created successfully! ID: ${data.id}`)

      // Reset form
      setNewRequest({
        student_id: '',
        request_type: 'official',
        delivery_method: 'email',
        purpose: '',
        copies_requested: 1,
        rush_processing: false,
        recipient_name: '',
        recipient_organization: '',
        notes: ''
      })
      setCreateDialogOpen(false)

      // Refresh if we're viewing document_services category
      if (selectedCategory?.id === 'document_services') {
        handleCategorySelect(selectedCategory)
      }
    } catch (err) {
      console.error('Error creating request:', err)
      alert(err instanceof Error ? err.message : 'Failed to create request')
    } finally {
      setCreating(false)
    }
  }

  const handleRequestClick = (request: DetailedRequest) => {
    if (!selectedCategory) return
    
    // Use the actual type from the request data, with smart fallbacks
    let requestType = request.type || "orders" // Use the type from the request data
    
    // If no type is specified, determine based on category and data structure
    if (!request.type) {
      if (selectedCategory.id === "academic_documents") {
        requestType = "orders"
      } else if (selectedCategory.id === "teacher_services") {
        requestType = "teacher_request"
      } else if (selectedCategory.id === "document_services") {
        // Check if it has document-specific fields
        if (request.type_name) {
          requestType = "documents"
        } else {
          requestType = "student_transcript"
        }
      } else if (selectedCategory.id === "student_services") {
        // Check if it has resource-specific fields
        if (request.resource_edition_id || request.reservation_date) {
          requestType = "resource_request"
        } else {
          requestType = "teacher_request"
        }
      } else if (selectedCategory.id === "resource_services") {
        requestType = "resource_request"
      }
    }

    console.log('Navigating to:', {
      category: selectedCategory.id,
      type: requestType,
      id: request.id,
      originalRequestType: request.type
    });

    // Navigate to the detailed view
    router.push(`/requests/${selectedCategory.id}/${requestType}/${request.id}`)
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return "N/A"
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric"
      })
    } catch {
      return dateString
    }
  }

  const formatStatus = (status: string | number | undefined) => {
    if (status === undefined || status === null) return "Unknown"
    return status.toString()
  }

  const renderRequestCard = (request: DetailedRequest, index: number) => {
    const fullName = [request.firstname, request.lastname, request.patronymic]
      .filter(Boolean)
      .join(' ') || null

    // Debug: Log request data to see what's available
    if (index === 0) {
      console.log('Rendering request:', {
        id: request.id,
        firstname: request.firstname,
        lastname: request.lastname,
        patronymic: request.patronymic,
        pincode: request.pincode,
        fullName: fullName
      })
    }

    return (
      <Card 
        key={`${request.id}-${index}`} 
        className="mb-4 cursor-pointer hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-primary/20 hover:border-l-primary" 
        onClick={() => handleRequestClick(request)}
      >
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Basic Information */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Hash className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">ID: {request.id}</span>
              </div>
              
              {request.type && (
                <div className="flex items-center space-x-2">
                  <FileStack className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Type: {request.type}</span>
                </div>
              )}
              
              {request.serial && (
                <div className="flex items-center space-x-2">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Serial: {request.serial}</span>
                </div>
              )}
            </div>

            {/* Person Information */}
            <div className="space-y-2">
              {fullName && (
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-primary">{fullName}</span>
                </div>
              )}
              
              {!fullName && (request.firstname || request.lastname || request.patronymic) && (
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-primary">
                    {[request.firstname, request.lastname, request.patronymic].filter(Boolean).join(' ')}
                  </span>
                </div>
              )}
              
              {!fullName && !request.firstname && !request.lastname && !request.patronymic && (
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">No person data</span>
                </div>
              )}
              
              {request.pincode && (
                <div className="flex items-center space-x-2">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">PIN: {request.pincode}</span>
                </div>
              )}
              
              {request.birthdate && (
                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Birth: {formatDate(request.birthdate)}</span>
                </div>
              )}
            </div>

            {/* Date and Status */}
            <div className="space-y-2">
              {(request.order_date || request.request_date || request.reservation_date) && (
                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    Date: {formatDate(
                      request.order_date || request.request_date || request.reservation_date
                    )}
                  </span>
                </div>
              )}
              
              {request.status !== undefined && (
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <Badge variant={
                    request.status_name?.toLowerCase().includes("approved") ? "default" :
                    request.status_name?.toLowerCase().includes("rejected") ? "destructive" :
                    "secondary"
                  }>
                    {request.status_name || formatStatus(request.status)}
                  </Badge>
                </div>
              )}
            </div>

            {/* Additional Information */}
            <div className="space-y-2">
              {request.gender_name && (
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{request.gender_name}</span>
                </div>
              )}
              
              {request.education_type_name && (
                <div className="flex items-center space-x-2">
                  <GraduationCap className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{request.education_type_name}</span>
                </div>
              )}
              
              {request.score !== undefined && request.score !== null && String(request.score).trim() !== "" && (
                <div className="flex items-center space-x-2">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Score: {request.score}</span>
                </div>
              )}
              
              {request.citizenship_name && (
                <div className="text-sm text-muted-foreground">
                  {request.citizenship_name}
                </div>
              )}
              
              {request.type_name && (
                <div className="text-sm text-muted-foreground">
                  {request.type_name} {request.type_name_en && `(${request.type_name_en})`}
                </div>
              )}
            </div>
          </div>
          
          {/* View Details Button */}
          <div className="mt-4 pt-4 border-t">
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full"
              onClick={(e) => {
                e.stopPropagation()
                handleRequestClick(request)
              }}
            >
              View Full Details
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (selectedCategory) {
    const IconComponent = iconMap[selectedCategory.icon as keyof typeof iconMap] || FileStack

    return (
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={handleBackToTree} size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Requests
          </Button>
          <div className="flex items-center space-x-3">
            <IconComponent className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">{selectedCategory.name}</h1>
              <p className="text-muted-foreground">{selectedCategory.description}</p>
            </div>
          </div>
        </div>

        <Separator />

        {/* Category Details */}
        {loading && (
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <span className="text-sm text-muted-foreground">Loading detailed requests...</span>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <Card>
            <CardContent className="py-8">
              <div className="text-center space-y-4">
                <AlertCircle className="h-8 w-8 text-destructive mx-auto" />
                <div>
                  <h3 className="font-medium text-destructive">Error Loading Details</h3>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                </div>
                <Button onClick={() => handleCategorySelect(selectedCategory)} variant="outline" size="sm">
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {categoryDetails && !loading && (
          <div className="space-y-6">
            {/* Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Category Summary</CardTitle>
                <CardDescription>
                  Overview of {categoryDetails.name.toLowerCase()} in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">
                      {categoryDetails.total_count.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Requests Shown</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">
                      {selectedCategory.requests.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Request Types</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Requests */}
            <div>
              <h2 className="text-lg font-semibold mb-4">
                Detailed Requests ({categoryDetails.requests.length})
              </h2>
              
              {categoryDetails.requests.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-8">
                    <FileStack className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
                    <h3 className="font-medium text-muted-foreground">No Requests Found</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      No detailed requests are available for this category.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {categoryDetails.requests.map((request, index) => 
                    renderRequestCard(request, index)
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Academic Requests</h1>
          <p className="text-muted-foreground mt-2">
            Manage and view academic requests, document services, and student services
          </p>
        </div>

        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create New Request
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Transcript Request</DialogTitle>
              <DialogDescription>
                Submit a new transcript request for a student
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="student_id">Student ID *</Label>
                  <Input
                    id="student_id"
                    placeholder="Enter student UUID"
                    value={newRequest.student_id}
                    onChange={(e) => setNewRequest({ ...newRequest, student_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="request_type">Request Type *</Label>
                  <Select
                    value={newRequest.request_type}
                    onValueChange={(value) => setNewRequest({ ...newRequest, request_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="official">Official</SelectItem>
                      <SelectItem value="unofficial">Unofficial</SelectItem>
                      <SelectItem value="verification">Verification</SelectItem>
                      <SelectItem value="duplicate">Duplicate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="delivery_method">Delivery Method *</Label>
                  <Select
                    value={newRequest.delivery_method}
                    onValueChange={(value) => setNewRequest({ ...newRequest, delivery_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="postal_mail">Postal Mail</SelectItem>
                      <SelectItem value="pickup">Pickup</SelectItem>
                      <SelectItem value="digital">Digital</SelectItem>
                      <SelectItem value="courier">Courier</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="copies">Copies Requested</Label>
                  <Input
                    id="copies"
                    type="number"
                    min="1"
                    max="10"
                    value={newRequest.copies_requested}
                    onChange={(e) => setNewRequest({ ...newRequest, copies_requested: parseInt(e.target.value) || 1 })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="purpose">Purpose</Label>
                <Input
                  id="purpose"
                  placeholder="e.g., Graduate school application"
                  value={newRequest.purpose}
                  onChange={(e) => setNewRequest({ ...newRequest, purpose: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="recipient_name">Recipient Name</Label>
                  <Input
                    id="recipient_name"
                    placeholder="e.g., Admissions Office"
                    value={newRequest.recipient_name}
                    onChange={(e) => setNewRequest({ ...newRequest, recipient_name: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="recipient_org">Recipient Organization</Label>
                  <Input
                    id="recipient_org"
                    placeholder="e.g., Harvard University"
                    value={newRequest.recipient_organization}
                    onChange={(e) => setNewRequest({ ...newRequest, recipient_organization: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  placeholder="Additional notes or special instructions"
                  rows={3}
                  value={newRequest.notes}
                  onChange={(e) => setNewRequest({ ...newRequest, notes: e.target.value })}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="rush"
                  checked={newRequest.rush_processing}
                  onCheckedChange={(checked) => setNewRequest({ ...newRequest, rush_processing: checked as boolean })}
                />
                <Label htmlFor="rush" className="text-sm font-normal">
                  Rush Processing (+50% fee)
                </Label>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)} disabled={creating}>
                Cancel
              </Button>
              <Button onClick={handleCreateRequest} disabled={creating}>
                {creating ? 'Creating...' : 'Create Request'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Separator />

      {/* Requests Tree */}
      <ShadcnRequestsTree onCategorySelect={handleCategorySelect} />
    </div>
  )
}