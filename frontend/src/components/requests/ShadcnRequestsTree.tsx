"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { 
  ChevronDown, 
  ChevronRight, 
  GraduationCap, 
  Users, 
  AlertCircle, 
  FileStack,
  LoaderIcon,
  RefreshCw
} from "lucide-react"

interface PersonInfo {
  person_id?: number
  first_name?: string
  last_name?: string
  pincode?: string
  email?: string
}

interface DetailedRequest {
  id: number
  type: string
  title: string
  description?: string
  status: string
  status_name?: string
  created_date?: string
  updated_date?: string
  person?: PersonInfo
  metadata?: Record<string, unknown>
}

interface RequestStats {
  total: number
  pending?: number
  approved?: number
  rejected?: number
  reserved?: number
  taken?: number
  returned?: number
}

interface RequestType {
  id: string
  name: string
  description: string
  category: string
  table_name: string
  total_count: number
  recent_count: number
  stats?: RequestStats
  sample_requests?: DetailedRequest[]
}

interface RequestCategory {
  id: string
  name: string
  description: string
  icon: string
  requests: RequestType[]
  total_count: number
}

interface RequestSummary {
  categories: RequestCategory[]
  total_requests: number
  total_categories: number
}

const iconMap = {
  GraduationCap,
  Users,
  AlertCircle,
  FileStack
}

const RequestCategoryCard: React.FC<{
  category: RequestCategory
  isExpanded: boolean
  onToggle: () => void
  onViewDetails: (category: RequestCategory) => void
  onRequestTypeSelect?: (requestType: RequestType) => void
}> = ({ category, isExpanded, onToggle, onViewDetails, onRequestTypeSelect }) => {
  const IconComponent = iconMap[category.icon as keyof typeof iconMap] || FileStack

  return (
    <Card className="w-full mb-4">
      <Collapsible open={isExpanded} onOpenChange={onToggle}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                  <IconComponent className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-lg">{category.name}</CardTitle>
                  <CardDescription className="text-sm">
                    {category.description}
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary" className="text-sm">
                  {category.total_count.toLocaleString()} total
                </Badge>
                <Badge variant="outline" className="text-sm">
                  {category.requests.length} types
                </Badge>
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-3">
              {category.requests.map((request) => (
                <div
                  key={request.id}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-sm">{request.name}</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        {request.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {request.total_count.toLocaleString()} total
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {request.recent_count.toLocaleString()} recent
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Table: {request.table_name}
                        </span>
                      </div>
                      
                      {request.stats && (
                        <div className="flex items-center space-x-2 mt-2">
                          {(request.stats.pending ?? 0) > 0 && (
                            <Badge variant="outline" className="text-xs border-orange-200 text-orange-700">
                              {request.stats.pending} pending
                            </Badge>
                          )}
                          {(request.stats.approved ?? 0) > 0 && (
                            <Badge variant="outline" className="text-xs border-green-200 text-green-700">
                              {request.stats.approved} approved
                            </Badge>
                          )}
                          {(request.stats.rejected ?? 0) > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              {request.stats.rejected} rejected
                            </Badge>
                          )}
                          {(request.stats.reserved ?? 0) > 0 && (
                            <Badge variant="secondary" className="text-xs">
                              {request.stats.reserved} reserved
                            </Badge>
                          )}
                        </div>
                      )}
                      
                      {request.sample_requests && request.sample_requests.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <h5 className="text-xs font-medium text-muted-foreground">Recent Requests:</h5>
                          {request.sample_requests.slice(0, 2).map((sample) => (
                            <div key={sample.id} className="text-xs bg-muted/30 rounded p-2">
                              <div className="flex items-center justify-between">
                                <span className="font-medium">{sample.title}</span>
                                <Badge variant="outline" className="text-xs">
                                  {sample.status_name || sample.status}
                                </Badge>
                              </div>
                              {sample.description && (
                                <p className="text-muted-foreground mt-1 truncate">
                                  {sample.description}
                                </p>
                              )}
                              {sample.person && (
                                <p className="text-muted-foreground mt-1">
                                  By: {sample.person.first_name} {sample.person.last_name}
                                  {sample.person.pincode && ` (${sample.person.pincode})`}
                                </p>
                              )}
                              {sample.created_date && (
                                <p className="text-muted-foreground mt-1">
                                  Date: {new Date(sample.created_date).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          ))}
                          {request.sample_requests.length > 2 && (
                            <p className="text-xs text-muted-foreground text-center">
                              +{request.sample_requests.length - 2} more requests
                            </p>
                          )}
                        </div>
                      )}
                      
                      {onRequestTypeSelect && (
                        <div className="mt-3">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => onRequestTypeSelect(request)}
                            className="w-full text-xs"
                          >
                            View All {request.name}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              <div className="pt-2 border-t">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => onViewDetails(category)}
                  className="w-full"
                >
                  View Detailed Requests
                </Button>
              </div>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

export const ShadcnRequestsTree: React.FC<{
  onCategorySelect?: (category: RequestCategory) => void
  onRequestTypeSelect?: (requestType: RequestType) => void
}> = ({ onCategorySelect, onRequestTypeSelect }) => {
  const [requestsData, setRequestsData] = useState<RequestSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())

  const fetchRequestsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch("http://127.0.0.1:8000/api/v1/requests/summary")
      if (!response.ok) {
        throw new Error(`Failed to fetch requests data: ${response.statusText}`)
      }
      
      const data = await response.json()
      setRequestsData(data)
      
      // Auto-expand categories with fewer than 3 request types
      const autoExpand = new Set<string>()
      data.categories.forEach((category: RequestCategory) => {
        if (category.requests.length <= 3) {
          autoExpand.add(category.id)
        }
      })
      setExpandedCategories(autoExpand)
      
    } catch (err) {
      console.error("Error fetching requests data:", err)
      setError(err instanceof Error ? err.message : "Unknown error occurred")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequestsData()
  }, [])

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(categoryId)) {
        next.delete(categoryId)
      } else {
        next.add(categoryId)
      }
      return next
    })
  }

  const handleViewDetails = (category: RequestCategory) => {
    if (onCategorySelect) {
      onCategorySelect(category)
    }
  }

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <LoaderIcon className="h-4 w-4 animate-spin" />
            <span className="text-sm text-muted-foreground">Loading requests data...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="py-8">
          <div className="text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto" />
            <div>
              <h3 className="font-medium text-destructive">Error Loading Requests</h3>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
            <Button onClick={fetchRequestsData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!requestsData || requestsData.categories.length === 0) {
    return (
      <Card className="w-full">
        <CardContent className="text-center py-8">
          <FileStack className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
          <h3 className="font-medium text-muted-foreground">No Requests Found</h3>
          <p className="text-sm text-muted-foreground mt-1">
            No request categories are available in the system.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="w-full space-y-4">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileStack className="h-5 w-5" />
            <span>Academic Requests Overview</span>
          </CardTitle>
          <CardDescription>
            Comprehensive view of all academic request types and document services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {requestsData.total_requests.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Total Requests</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {requestsData.total_categories}
              </div>
              <div className="text-sm text-muted-foreground">Categories</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {requestsData.categories.reduce((sum, cat) => sum + cat.requests.length, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Request Types</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Request Categories */}
      <div className="space-y-4">
        {requestsData.categories.map((category) => (
          <RequestCategoryCard
            key={category.id}
            category={category}
            isExpanded={expandedCategories.has(category.id)}
            onToggle={() => toggleCategory(category.id)}
            onViewDetails={handleViewDetails}
            onRequestTypeSelect={onRequestTypeSelect}
          />
        ))}
      </div>
    </div>
  )
}