"use client"

import React, { useState, useEffect } from "react"
import AuthenticatedLayout from "@/components/authenticated-layout"
import { AcademicScheduleEditModal } from "@/components/academic-schedule-edit-modal"
import { SingleEventEditModal } from "@/components/single-event-edit-modal"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  Calendar,
  Clock,
  GraduationCap,
  BookOpen,
  CalendarDays,
  Timer,
  Users,
  FileText,
  ChevronDown,
  ChevronUp,
  Filter
} from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface ScheduleEvent {
  id: string
  academic_schedule_id: string
  type_id: string
  start_date: string
  end_date?: string
  event_type: string
  semester_type: string
}

interface AcademicScheduleDetails {
  education_year: string
  year_start: string
  year_end: string
  events: ScheduleEvent[]
}

interface EducationStats {
  total_education_plans: number
  total_education_groups: number
  total_scheduled_events: number
}

export default function AcademicSchedulePage() {
  const [scheduleDetails, setScheduleDetails] = useState<AcademicScheduleDetails[]>([])
  const [educationStats, setEducationStats] = useState<EducationStats | null>(null)
  const [expandedYears, setExpandedYears] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<ScheduleEvent | null>(null)
  const [isEventModalOpen, setIsEventModalOpen] = useState(false)

  useEffect(() => {
    fetchAcademicData()
  }, [])

  const fetchAcademicData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch schedule details
      const scheduleResponse = await fetch(`${API_BASE_URL}/academic-schedule/details`)
      if (!scheduleResponse.ok) {
        throw new Error(`Failed to fetch schedule details: ${scheduleResponse.statusText}`)
      }
      const scheduleData = await scheduleResponse.json()
      setScheduleDetails(scheduleData)

      // Fetch education statistics
      const statsResponse = await fetch(`${API_BASE_URL}/academic-schedule/stats`)
      if (!statsResponse.ok) {
        throw new Error(`Failed to fetch education stats: ${statsResponse.statusText}`)
      }
      const statsData = await statsResponse.json()
      setEducationStats(statsData)

    } catch (err) {
      console.error("Error fetching academic data:", err)
      setError(err instanceof Error ? err.message : "Unknown error occurred")
    } finally {
      setLoading(false)
    }
  }

  const fetchYearDetails = async (yearName: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/academic-schedule/year/${encodeURIComponent(yearName)}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch year details: ${response.statusText}`)
      }
      const yearData = await response.json()
      
      // Update the scheduleDetails with events for this year
      setScheduleDetails(prev => prev.map(year => 
        year.education_year === yearName 
          ? { ...year, events: yearData.events || [] }
          : year
      ))
    } catch (err) {
      console.error("Error fetching year details:", err)
    }
  }

    const handleEventClick = (event: ScheduleEvent) => {
    setSelectedEvent(event);
    setIsEventModalOpen(true);
  };

  const handleEventModalClose = () => {
    setIsEventModalOpen(false);
    setSelectedEvent(null);
  };

  const toggleYearExpansion = async (yearName: string) => {
    const newExpanded = new Set(expandedYears)
    if (newExpanded.has(yearName)) {
      newExpanded.delete(yearName)
    } else {
      newExpanded.add(yearName)
      // Fetch details for this year if we don't have events yet
      const yearData = scheduleDetails.find(y => y.education_year === yearName)
      if (yearData && yearData.events.length === 0) {
        await fetchYearDetails(yearName)
      }
    }
    setExpandedYears(newExpanded)
  }

  const formatDate = (dateString: string) => {
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

  const getEventTypeIcon = (eventType: string) => {
    if (eventType.includes("Academic Year Start")) return <Calendar className="h-4 w-4" />
    if (eventType.includes("Academic Year End")) return <Timer className="h-4 w-4" />
    if (eventType.includes("Spring Semester")) return <BookOpen className="h-4 w-4" />
    if (eventType.includes("Summer")) return <CalendarDays className="h-4 w-4" />
    if (eventType.includes("Winter Break")) return <Clock className="h-4 w-4" />
    return <FileText className="h-4 w-4" />
  }

  const getEventTypeBadgeVariant = (eventType: string, semesterType: string) => {
    if (eventType.includes("Academic Year Start")) return "default"
    if (eventType.includes("Academic Year End")) return "secondary"
    if (eventType.includes("Winter Break")) return "outline"
    if (semesterType === "Fall Semester") return "destructive"
    if (semesterType === "Spring Semester") return "default"
    if (semesterType === "Summer Semester") return "secondary"
    return "outline"
  }

  const getSemesterColor = (semesterType: string) => {
    if (semesterType === "Fall Semester") return "text-orange-600 bg-orange-50"
    if (semesterType === "Spring Semester") return "text-green-600 bg-green-50"
    if (semesterType === "Summer Semester") return "text-blue-600 bg-blue-50"
    return "text-gray-600 bg-gray-50"
  }

  const renderStatsCards = () => {
    if (!educationStats) return null

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Education Plans</CardTitle>
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{educationStats.total_education_plans}</div>
            <p className="text-xs text-muted-foreground">Active curriculum structures</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Education Groups</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{educationStats.total_education_groups}</div>
            <p className="text-xs text-muted-foreground">Student class groupings</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled Events</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{educationStats.total_scheduled_events}</div>
            <p className="text-xs text-muted-foreground">Academic calendar events</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderYearCard = (year: AcademicScheduleDetails, index: number) => {
    const isExpanded = expandedYears.has(year.education_year)
    const isCurrentYear = year.education_year === "2024/2025"

    // Group events by semester type
    const eventsBySemester = year.events.reduce((acc, event) => {
      if (!acc[event.semester_type]) {
        acc[event.semester_type] = []
      }
      acc[event.semester_type].push(event)
      return acc
    }, {} as Record<string, ScheduleEvent[]>)

    // Sort events within each semester by date
    Object.keys(eventsBySemester).forEach(semester => {
      eventsBySemester[semester].sort((a, b) => {
        const dateA = new Date(a.start_date.split('/').reverse().join('-'))
        const dateB = new Date(b.start_date.split('/').reverse().join('-'))
        return dateA.getTime() - dateB.getTime()
      })
    })

    const semesterOrder = ["Fall Semester", "Spring Semester", "Summer Semester"]

    // Create unique key using index and year_start to handle duplicate education_year values
    const uniqueKey = `${year.education_year}-${year.year_start}-${index}`

    return (
      <Card key={uniqueKey} className={`mb-4 ${isCurrentYear ? 'border-primary' : ''}`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Calendar className="h-6 w-6 text-primary" />
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <span>{year.education_year}</span>
                  {isCurrentYear && <Badge variant="default">Current</Badge>}
                </CardTitle>
                <CardDescription>
                  {formatDate(year.year_start)} - {formatDate(year.year_end)}
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">{year.events.length} events</Badge>
              {year.events.length > 0 && (
                <div className="flex space-x-1">
                  {semesterOrder.map(semester => {
                    const count = eventsBySemester[semester]?.length || 0
                    if (count === 0) return null
                    return (
                      <Badge 
                        key={semester} 
                        variant="secondary" 
                        className={`text-xs ${getSemesterColor(semester)}`}
                      >
                        {semester === "Fall Semester" ? "Fall" : 
                         semester === "Spring Semester" ? "Spring" : "Summer"} ({count})
                      </Badge>
                    )
                  })}
                </div>
              )}
              <AcademicScheduleEditModal 
                year={year} 
                onUpdate={fetchAcademicData}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleYearExpansion(year.education_year)}
              >
                {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>

        {isExpanded && year.events.length > 0 && (
          <CardContent>
            <div className="space-y-6">
              {semesterOrder.map(semester => {
                const semesterEvents = eventsBySemester[semester]
                if (!semesterEvents || semesterEvents.length === 0) return null

                return (
                  <div key={semester} className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${
                        semester === "Fall Semester" ? "bg-orange-500" :
                        semester === "Spring Semester" ? "bg-green-500" : "bg-blue-500"
                      }`} />
                      <h4 className="font-semibold text-sm">{semester}</h4>
                      <Badge variant="outline" className="text-xs">
                        {semesterEvents.length} events
                      </Badge>
                    </div>
                    <div className="space-y-2 ml-5">
                      {semesterEvents.map((event, index) => (
                        <div
                          key={`${event.id}-${index}`}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                          onClick={() => handleEventClick(event)}
                        >
                          <div className="flex items-center space-x-3">
                            {getEventTypeIcon(event.event_type)}
                            <div className="flex-1">
                              <div className="font-medium text-sm">{event.event_type}</div>
                              <div className="text-xs text-muted-foreground">
                                {formatDate(event.start_date)}
                              </div>
                            </div>
                          </div>
                          <Badge variant={getEventTypeBadgeVariant(event.event_type, event.semester_type)} className="text-xs">
                            {event.event_type.includes("Start") ? "Start" : 
                             event.event_type.includes("End") ? "End" : "Event"}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        )}

        {isExpanded && year.events.length === 0 && (
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              <CalendarDays className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No scheduled events for this academic year</p>
            </div>
          </CardContent>
        )}
      </Card>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading academic schedule...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Academic Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={fetchAcademicData} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <AuthenticatedLayout>
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Academic Year Schedule</h1>
            <p className="text-muted-foreground">
              Comprehensive academic calendar and education management overview
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button onClick={fetchAcademicData} variant="outline" size="sm">
              <Clock className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <Separator />

        {/* Statistics Cards */}
        {renderStatsCards()}

        {/* Academic Years */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Academic Years & Schedules</h2>
            <p className="text-sm text-muted-foreground">
              {scheduleDetails.length} academic years with detailed schedules
            </p>
          </div>

          {scheduleDetails.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <CalendarDays className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No Academic Schedules Found</h3>
                <p className="text-muted-foreground mb-4">
                  There are no academic year schedules available at the moment.
                </p>
                <Button onClick={fetchAcademicData} variant="outline">
                  Refresh Data
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {scheduleDetails.map((year, index) => renderYearCard(year, index))}
            </div>
          )}
        </div>
      </div>
      
      <SingleEventEditModal
        event={selectedEvent}
        isOpen={isEventModalOpen}
        onClose={handleEventModalClose}
        onUpdate={fetchAcademicData}
      />
    </AuthenticatedLayout>
  )
}