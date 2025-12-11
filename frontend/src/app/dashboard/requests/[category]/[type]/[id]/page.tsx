"use client"

import React, { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
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
  User,
  Hash,
  Mail,
  Building,
  BookOpen,
  Award,
  FileText,
  Settings,
  Calendar,
  CreditCard,
  MapPin,
  Globe,
  DollarSign,
  IdCard,
  School,
  Clock,
  Eye,
  Database,
  Info,
  Receipt,
  Timer,
  Edit,
  FileJson
} from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface DetailedRequestData {
  id: string
  // Order fields
  serial?: string
  order_date?: string
  status?: string | number
  create_date?: string
  update_date?: string
  note?: string
  type_id?: string
  form_id?: string
  edu_level_id?: string
  file_id?: string
  create_user_id?: string
  update_user_id?: string
  // Person information
  person_id?: string
  student_id?: string
  reason_id?: string
  person_note?: string
  firstname?: string
  lastname?: string
  patronymic?: string
  pincode?: string
  birthdate?: string
  gender_id?: string
  citizenship_id?: string
  nationality_id?: string
  // Student information
  card_number?: string
  education_line_id?: string
  education_type_id?: string
  education_payment_type_id?: string
  score?: string
  yearly_payment?: string
  payment_count?: string
  user_id?: string
  org_id?: string
  in_order_id?: string
  out_order_id?: string
  yda_order_id?: string
  order_type_id?: string
  // Teacher request fields
  course_id?: string
  meeting_id?: string
  evaluation_id?: string
  reason?: string
  access_date?: string
  // Resource request fields
  resource_edition_id?: string
  reservation_date?: string
  take_date?: string
  finish_date?: string
  return_date?: string
  request_code?: string
  penalty_price?: string
  paid_penalty_price?: string
  penalty_reason?: string
  penalty_note?: string
  user_type?: string
  // Student transcript fields
  subject_name?: string
  transcript_course_id?: string
  education_group_id?: string
  fullname?: string
  faculty_name?: string
  speciality_name?: string
  credit?: string
  end_point?: string
  before_point?: string
  exam_point?: string
  semester?: string
  education_year?: string
  type?: string
  // Document fields
  num?: string
  start_date?: string
  end_date?: string
  issuing_organization?: string
  // Status information
  status_name?: string
  type_name?: string
  type_name_en?: string
  // Dictionary translations
  gender_name?: string
  citizenship_name?: string
  nationality_name?: string
  education_type_name?: string
  education_payment_type_name?: string
  form_name?: string
  edu_level_name?: string
}

const iconMap = {
  academic_documents: GraduationCap,
  teacher_services: Users,
  student_services: BookOpen,
  document_services: FileStack,
  resource_services: Building
}

export default function RequestDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [requestData, setRequestData] = useState<DetailedRequestData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { category, type, id } = params

  useEffect(() => {
    const fetchRequestDetail = async () => {
      if (!category || !type || !id) return

      console.log('Starting fetch for:', { category, type, id });
      setLoading(true)
      setError(null)

      try {
        const url = `${API_BASE_URL}/requests/detailed/${type}/${id}`;
        console.log('Fetching URL:', url);
        
        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch(url, { signal: controller.signal })
        clearTimeout(timeoutId);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch request details: ${response.status} ${response.statusText}`)
        }
        
        // Handle large integers in the response by getting raw text first
        const text = await response.text()
        const data = JSON.parse(text, (key, value) => {
          // Handle all numeric IDs as strings to preserve precision
          if (key === 'id' && typeof value === 'number') {
            return value.toString()
          }
          // Convert any large numbers to strings to preserve precision
          if (typeof value === 'number' && (value > Number.MAX_SAFE_INTEGER || value < Number.MIN_SAFE_INTEGER)) {
            return value.toString()
          }
          return value
        })
        
        console.log('Received data:', data);
        setRequestData(data)
      } catch (err) {
        console.error("Error fetching request detail:", err)
        if (err instanceof Error && err.name === 'AbortError') {
          setError("Request timed out. Please try again.")
        } else {
          setError(err instanceof Error ? err.message : "Unknown error occurred")
        }
      } finally {
        console.log('Setting loading to false');
        setLoading(false)
      }
    }

    fetchRequestDetail()
  }, [category, type, id])

  const handleBack = () => {
    router.push("/dashboard/requests")
  }

  const handleExportJSON = () => {
    if (!requestData) return

    const dataStr = JSON.stringify(requestData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `request_${requestData.id}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleExportPDF = () => {
    if (!requestData) return

    // Create a printable version
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const fullName = [requestData.firstname, requestData.lastname, requestData.patronymic].filter(Boolean).join(' ')

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Request Details - ${requestData.id}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            .section { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }
            .section h2 { color: #555; margin-top: 0; font-size: 18px; }
            .field { margin: 10px 0; display: grid; grid-template-columns: 200px 1fr; gap: 10px; }
            .field label { font-weight: bold; color: #666; }
            .field value { color: #333; }
            @media print { .no-print { display: none; } }
          </style>
        </head>
        <body>
          <h1>Request Details</h1>
          <div class="section">
            <h2>Basic Information</h2>
            <div class="field"><label>Request ID:</label><value>${requestData.id}</value></div>
            ${requestData.serial ? `<div class="field"><label>Serial Number:</label><value>${requestData.serial}</value></div>` : ''}
            ${requestData.status_name ? `<div class="field"><label>Status:</label><value>${requestData.status_name}</value></div>` : ''}
            ${requestData.order_date || requestData.create_date ? `<div class="field"><label>Date:</label><value>${requestData.order_date || requestData.create_date}</value></div>` : ''}
          </div>
          ${fullName ? `
          <div class="section">
            <h2>Person Information</h2>
            <div class="field"><label>Full Name:</label><value>${fullName}</value></div>
            ${requestData.pincode ? `<div class="field"><label>PIN Code:</label><value>${requestData.pincode}</value></div>` : ''}
            ${requestData.birthdate ? `<div class="field"><label>Date of Birth:</label><value>${requestData.birthdate}</value></div>` : ''}
          </div>` : ''}
          <div class="section no-print" style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">Print / Save as PDF</button>
            <button onclick="window.close()" style="padding: 10px 20px; background: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">Close</button>
          </div>
        </body>
      </html>
    `)
    printWindow.document.close()
  }

  const handleEdit = () => {
    if (!type || !id) return
    // Navigate to edit mode or show edit modal
    router.push(`/dashboard/requests/${category}/${type}/${id}/edit`)
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return "N/A"
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      })
    } catch {
      return dateString
    }
  }

  const formatStatus = (status: string | number | undefined) => {
    if (status === undefined || status === null) return "Unknown"
    return status.toString()
  }

  const getStatusVariant = (status: string | undefined): "default" | "secondary" | "destructive" => {
    if (!status) return "secondary"
    const statusLower = status.toLowerCase()
    if (statusLower.includes("approved") || statusLower.includes("complete")) return "default"
    if (statusLower.includes("rejected") || statusLower.includes("cancelled")) return "destructive"
    return "secondary"
  }

  const getTypeDisplayName = (type: string) => {
    const typeMap: { [key: string]: string } = {
      orders: "Academic Order",
      teacher_request: "Teacher Evaluation Request",
      resource_request: "Resource Request",
      student_transcript: "Student Transcript",
      documents: "Document Request"
    }
    return typeMap[type] || type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())
  }

  const getCategoryDisplayName = (category: string) => {
    const categoryMap: { [key: string]: string } = {
      academic_documents: "Academic Documents",
      teacher_services: "Teacher Services",
      student_services: "Student Services", 
      document_services: "Document Services",
      resource_services: "Resource Services"
    }
    return categoryMap[category] || category.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())
  }

  const IconComponent = iconMap[category as keyof typeof iconMap] || FileStack

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={handleBack} size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Requests
          </Button>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span className="text-muted-foreground">Loading request details...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={handleBack} size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Requests
          </Button>
        </div>
        
        <Card>
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
              <div>
                <h3 className="text-lg font-medium text-destructive">Error Loading Request Details</h3>
                <p className="text-muted-foreground mt-1">{error}</p>
              </div>
              <Button onClick={() => window.location.reload()} variant="outline">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!requestData) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={handleBack} size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Requests
          </Button>
        </div>
        
        <Card>
          <CardContent className="text-center py-12">
            <FileStack className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground">Request Not Found</h3>
            <p className="text-muted-foreground mt-1">
              The requested details could not be found.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button variant="outline" onClick={handleBack} size="sm">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Requests
        </Button>
        <div className="flex items-center space-x-3">
          <IconComponent className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">{getTypeDisplayName(type as string)}</h1>
            <p className="text-muted-foreground">
              {getCategoryDisplayName(category as string)} • ID: {requestData.id}
            </p>
          </div>
        </div>
      </div>

      <Separator />

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Hash className="h-5 w-5" />
              <span>Basic Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Request ID</label>
                <div className="text-sm">{requestData.id}</div>
              </div>
              
              {requestData.serial && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Serial Number</label>
                  <div className="text-sm">{requestData.serial}</div>
                </div>
              )}
              
              {requestData.status !== undefined && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Status</label>
                  <div>
                    <Badge variant={getStatusVariant(requestData.status_name)}>
                      {requestData.status_name || formatStatus(requestData.status)}
                    </Badge>
                  </div>
                </div>
              )}
              
              {(requestData.order_date || requestData.create_date || requestData.reservation_date || requestData.access_date) && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Date</label>
                  <div className="text-sm">
                    {formatDate(
                      requestData.order_date || 
                      requestData.create_date || 
                      requestData.reservation_date || 
                      requestData.access_date
                    )}
                  </div>
                </div>
              )}
            </div>

            {(requestData.type_name || requestData.form_name || requestData.subject_name || requestData.issuing_organization) && (
              <div>
                <label className="text-sm font-medium text-muted-foreground">Additional Details</label>
                <div className="text-sm space-y-1">
                  {requestData.type_name && (
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Type:</span> 
                      <span>{requestData.type_name}</span>
                      {requestData.type_name_en && <span className="text-muted-foreground">({requestData.type_name_en})</span>}
                    </div>
                  )}
                  {requestData.form_name && (
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Form:</span> 
                      <span>{requestData.form_name}</span>
                    </div>
                  )}
                  {requestData.subject_name && (
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Subject:</span> 
                      <span>{requestData.subject_name}</span>
                    </div>
                  )}
                  {requestData.issuing_organization && (
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Issuing Organization:</span> 
                      <span>{requestData.issuing_organization}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {(requestData.note || requestData.reason) && (
              <div>
                <label className="text-sm font-medium text-muted-foreground">Notes/Reason</label>
                <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                  {requestData.note || requestData.reason}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Person Information */}
        {(requestData.firstname || requestData.lastname || requestData.person_id || requestData.student_id) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Person Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(requestData.firstname || requestData.lastname) && (
                  <div className="col-span-full">
                    <label className="text-sm font-medium text-muted-foreground">Full Name</label>
                    <div className="text-lg font-medium">
                      {[requestData.firstname, requestData.lastname, requestData.patronymic].filter(Boolean).join(" ") || "N/A"}
                    </div>
                  </div>
                )}
                
                {requestData.pincode && (
                  <div className="flex items-center space-x-2">
                    <IdCard className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">PIN Code</label>
                      <div className="text-sm font-mono">{requestData.pincode}</div>
                    </div>
                  </div>
                )}

                {requestData.birthdate && (
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Date of Birth</label>
                      <div className="text-sm">{requestData.birthdate}</div>
                    </div>
                  </div>
                )}

                {requestData.gender_name && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Gender</label>
                    <div className="text-sm">{requestData.gender_name}</div>
                  </div>
                )}

                {requestData.citizenship_name && (
                  <div className="flex items-center space-x-2">
                    <Globe className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Citizenship</label>
                      <div className="text-sm">{requestData.citizenship_name}</div>
                    </div>
                  </div>
                )}

                {requestData.nationality_name && (
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Nationality</label>
                      <div className="text-sm">{requestData.nationality_name}</div>
                    </div>
                  </div>
                )}
                
                {requestData.person_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Person ID</label>
                    <div className="text-sm font-mono">{requestData.person_id}</div>
                  </div>
                )}
                
                {requestData.student_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Student ID</label>
                    <div className="text-sm font-mono">{requestData.student_id}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Academic Information */}
        {(requestData.score || requestData.education_type_name || requestData.education_payment_type_name || requestData.card_number || requestData.yearly_payment || requestData.edu_level_name) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <School className="h-5 w-5" />
                <span>Academic Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requestData.edu_level_name && (
                  <div className="flex items-center space-x-2">
                    <GraduationCap className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Education Level</label>
                      <div className="text-sm">{requestData.edu_level_name}</div>
                    </div>
                  </div>
                )}

                {requestData.education_type_name && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Education Type</label>
                    <div className="text-sm">{requestData.education_type_name}</div>
                  </div>
                )}

                {requestData.education_payment_type_name && (
                  <div className="flex items-center space-x-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Payment Type</label>
                      <div className="text-sm">{requestData.education_payment_type_name}</div>
                    </div>
                  </div>
                )}

                {requestData.score && (
                  <div className="flex items-center space-x-2">
                    <Award className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Academic Score</label>
                      <div className="text-sm font-semibold">{requestData.score}</div>
                    </div>
                  </div>
                )}

                {requestData.card_number && (
                  <div className="flex items-center space-x-2">
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Student Card</label>
                      <div className="text-sm font-mono">{requestData.card_number}</div>
                    </div>
                  </div>
                )}

                {requestData.yearly_payment && (
                  <div className="flex items-center space-x-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Yearly Payment</label>
                      <div className="text-sm">{requestData.yearly_payment}</div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dates & Timeline */}
        {(requestData.order_date || requestData.create_date || requestData.update_date || requestData.reservation_date || requestData.take_date || requestData.finish_date || requestData.return_date || requestData.access_date || requestData.start_date || requestData.end_date) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span>Dates & Timeline</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requestData.order_date && (
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Order Date</label>
                      <div className="text-sm">{requestData.order_date}</div>
                    </div>
                  </div>
                )}

                {requestData.create_date && (
                  <div className="flex items-center space-x-2">
                    <Timer className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Created</label>
                      <div className="text-sm">{formatDate(requestData.create_date)}</div>
                    </div>
                  </div>
                )}

                {requestData.update_date && (
                  <div className="flex items-center space-x-2">
                    <Timer className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Last Updated</label>
                      <div className="text-sm">{formatDate(requestData.update_date)}</div>
                    </div>
                  </div>
                )}

                {requestData.reservation_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Reserved</label>
                    <div className="text-sm">{requestData.reservation_date}</div>
                  </div>
                )}

                {requestData.take_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Taken</label>
                    <div className="text-sm">{requestData.take_date}</div>
                  </div>
                )}

                {requestData.finish_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Expected Return</label>
                    <div className="text-sm">{requestData.finish_date}</div>
                  </div>
                )}

                {requestData.return_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Returned</label>
                    <div className="text-sm">{requestData.return_date}</div>
                  </div>
                )}

                {requestData.access_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Access Date</label>
                    <div className="text-sm">{requestData.access_date}</div>
                  </div>
                )}

                {requestData.start_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Start Date</label>
                    <div className="text-sm">{requestData.start_date}</div>
                  </div>
                )}

                {requestData.end_date && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">End Date</label>
                    <div className="text-sm">{requestData.end_date}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Resource & Financial Information */}
        {(requestData.request_code || requestData.penalty_price || requestData.paid_penalty_price || requestData.penalty_reason || requestData.penalty_note || requestData.yearly_payment || requestData.payment_count) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Receipt className="h-5 w-5" />
                <span>Resource & Financial Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requestData.request_code && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Request Code</label>
                    <div className="text-sm font-mono">{requestData.request_code}</div>
                  </div>
                )}

                {requestData.penalty_price && (
                  <div className="flex items-center space-x-2">
                    <DollarSign className="h-4 w-4 text-destructive" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Penalty Amount</label>
                      <div className="text-sm text-destructive font-medium">{requestData.penalty_price}</div>
                    </div>
                  </div>
                )}

                {requestData.paid_penalty_price && (
                  <div className="flex items-center space-x-2">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Paid Penalty</label>
                      <div className="text-sm text-green-600 font-medium">{requestData.paid_penalty_price}</div>
                    </div>
                  </div>
                )}

                {requestData.payment_count && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Payment Count</label>
                    <div className="text-sm">{requestData.payment_count}</div>
                  </div>
                )}
              </div>

              {requestData.penalty_note && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Penalty Note</label>
                  <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                    {requestData.penalty_note}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Academic Transcript Information */}
        {(requestData.fullname || requestData.faculty_name || requestData.speciality_name || requestData.credit || requestData.end_point || requestData.before_point || requestData.exam_point || requestData.semester || requestData.education_year) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5" />
                <span>Academic Transcript Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requestData.fullname && (
                  <div className="col-span-full">
                    <label className="text-sm font-medium text-muted-foreground">Student Name</label>
                    <div className="text-lg font-medium">{requestData.fullname}</div>
                  </div>
                )}

                {requestData.faculty_name && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Faculty</label>
                    <div className="text-sm">{requestData.faculty_name}</div>
                  </div>
                )}

                {requestData.speciality_name && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Speciality</label>
                    <div className="text-sm">{requestData.speciality_name}</div>
                  </div>
                )}

                {requestData.semester && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Semester</label>
                    <div className="text-sm">{requestData.semester}</div>
                  </div>
                )}

                {requestData.education_year && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Education Year</label>
                    <div className="text-sm">{requestData.education_year}</div>
                  </div>
                )}

                {requestData.credit && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Credits</label>
                    <div className="text-sm font-medium">{requestData.credit}</div>
                  </div>
                )}

                {requestData.before_point && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Before Point</label>
                    <div className="text-sm">{requestData.before_point}</div>
                  </div>
                )}

                {requestData.exam_point && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Exam Point</label>
                    <div className="text-sm font-medium">{requestData.exam_point}</div>
                  </div>
                )}

                {requestData.end_point && (
                  <div className="flex items-center space-x-2">
                    <Award className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Final Point</label>
                      <div className="text-sm font-semibold">{requestData.end_point}</div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Document Information */}
        {(requestData.num || requestData.issuing_organization || requestData.file_id) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Document Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requestData.num && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Document Number</label>
                    <div className="text-sm font-mono">{requestData.num}</div>
                  </div>
                )}

                {requestData.issuing_organization && (
                  <div className="flex items-center space-x-2">
                    <Building className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Issuing Organization</label>
                      <div className="text-sm">{requestData.issuing_organization}</div>
                    </div>
                  </div>
                )}

                {requestData.file_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">File ID</label>
                    <div className="text-sm font-mono">{requestData.file_id}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* System Information */}
        {(requestData.type_id || requestData.form_id || requestData.edu_level_id || requestData.create_user_id || requestData.update_user_id || requestData.user_id || requestData.org_id || requestData.education_group_id) && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <span>System Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                {requestData.type_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Type ID</label>
                    <div className="text-xs font-mono">{requestData.type_id}</div>
                  </div>
                )}

                {requestData.form_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Form ID</label>
                    <div className="text-xs font-mono">{requestData.form_id}</div>
                  </div>
                )}

                {requestData.edu_level_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Education Level ID</label>
                    <div className="text-xs font-mono">{requestData.edu_level_id}</div>
                  </div>
                )}

                {requestData.create_user_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Created By</label>
                    <div className="text-xs font-mono">{requestData.create_user_id}</div>
                  </div>
                )}

                {requestData.update_user_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Updated By</label>
                    <div className="text-xs font-mono">{requestData.update_user_id}</div>
                  </div>
                )}

                {requestData.user_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">User ID</label>
                    <div className="text-xs font-mono">{requestData.user_id}</div>
                  </div>
                )}

                {requestData.org_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Organization ID</label>
                    <div className="text-xs font-mono">{requestData.org_id}</div>
                  </div>
                )}

                {requestData.education_group_id && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Education Group ID</label>
                    <div className="text-xs font-mono">{requestData.education_group_id}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Additional Notes */}
        {(requestData.person_note || requestData.penalty_note) && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Info className="h-5 w-5" />
                <span>Additional Notes</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {requestData.person_note && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Person Note</label>
                  <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                    {requestData.person_note}
                  </div>
                </div>
              )}

              {requestData.penalty_note && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Penalty Note</label>
                  <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md border-l-4 border-destructive">
                    {requestData.penalty_note}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Technical Details */}
        {(requestData.course_id || requestData.meeting_id || requestData.evaluation_id || requestData.resource_edition_id || requestData.reason_id || requestData.transcript_course_id || requestData.in_order_id || requestData.out_order_id || requestData.yda_order_id || requestData.order_type_id) && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>Technical & Reference Details</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {requestData.course_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Course ID</label>
                    <div className="text-sm font-mono">{requestData.course_id}</div>
                  </div>
                )}

                {requestData.transcript_course_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Transcript Course ID</label>
                    <div className="text-sm font-mono">{requestData.transcript_course_id}</div>
                  </div>
                )}
                
                {requestData.meeting_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Meeting ID</label>
                    <div className="text-sm font-mono">{requestData.meeting_id}</div>
                  </div>
                )}
                
                {requestData.evaluation_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Evaluation ID</label>
                    <div className="text-sm font-mono">{requestData.evaluation_id}</div>
                  </div>
                )}
                
                {requestData.resource_edition_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Resource Edition ID</label>
                    <div className="text-sm font-mono">{requestData.resource_edition_id}</div>
                  </div>
                )}
                
                {requestData.reason_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Reason ID</label>
                    <div className="text-sm font-mono">{requestData.reason_id}</div>
                  </div>
                )}

                {requestData.in_order_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">In Order ID</label>
                    <div className="text-sm font-mono">{requestData.in_order_id}</div>
                  </div>
                )}

                {requestData.out_order_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Out Order ID</label>
                    <div className="text-sm font-mono">{requestData.out_order_id}</div>
                  </div>
                )}

                {requestData.yda_order_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">YDA Order ID</label>
                    <div className="text-sm font-mono">{requestData.yda_order_id}</div>
                  </div>
                )}

                {requestData.order_type_id && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Order Type ID</label>
                    <div className="text-sm font-mono">{requestData.order_type_id}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Actions & Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Eye className="h-5 w-5" />
            <span>Request Summary & Actions</span>
          </CardTitle>
          <CardDescription>
            Complete overview and available actions for request #{requestData.serial || requestData.id}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{requestData.serial || 'N/A'}</div>
              <div className="text-xs text-muted-foreground">Serial Number</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {requestData.status_name ? (
                  <Badge variant={getStatusVariant(requestData.status_name)}>{requestData.status_name}</Badge>
                ) : 'Unknown'}
              </div>
              <div className="text-xs text-muted-foreground">Status</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{requestData.score || 'N/A'}</div>
              <div className="text-xs text-muted-foreground">Academic Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {requestData.order_date || requestData.create_date?.split('T')[0] || 'N/A'}
              </div>
              <div className="text-xs text-muted-foreground">Date</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button variant="default" size="sm" onClick={handleEdit}>
              <Edit className="h-4 w-4 mr-2" />
              Edit Request
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportPDF}>
              <FileText className="h-4 w-4 mr-2" />
              Export as PDF
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportJSON}>
              <FileJson className="h-4 w-4 mr-2" />
              Export as JSON
            </Button>
            <Button variant="outline" size="sm">
              <Award className="h-4 w-4 mr-2" />
              View Academic History
            </Button>
            {requestData.firstname && (
              <Button variant="outline" size="sm">
                <Mail className="h-4 w-4 mr-2" />
                Contact {requestData.firstname}
              </Button>
            )}
            {requestData.penalty_price && (
              <Button variant="outline" size="sm" className="text-destructive">
                <DollarSign className="h-4 w-4 mr-2" />
                View Penalty Details
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}