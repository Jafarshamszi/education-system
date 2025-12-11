'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { CalendarDays, Clock, Users, MapPin, BookOpen, ChevronLeft, ChevronRight, AlertCircle, CalendarIcon, List, GraduationCap, Table as TableIcon } from 'lucide-react';
import { format } from 'date-fns';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { EventClickArg, DatesSetArg } from '@fullcalendar/core';
import '@/styles/calendar.css';

// Types
interface ScheduleClass {
  schedule_id: string;
  day_of_week: number;
  day_name: string;
  start_time: string;
  end_time: string;
  course_code: string;
  course_name: string;
  section_code: string;
  room_id: string | null;
  schedule_type: string | null;
  enrolled_count: number;
  max_enrollment: number;
}

interface ScheduleEvent {
  id: string;
  title: string;
  course_code: string;
  course_name: string;
  section_code: string;
  start: string;
  end: string;
  day_of_week: number;
  day_name: string;
  room_id: string | null;
  schedule_type: string | null;
  enrolled_count: number;
  max_enrollment: number;
  background_color: string;
}

interface CalendarScheduleResponse {
  teacher_id: string;
  employee_number: string;
  full_name: string;
  schedule_events: ScheduleEvent[];
}

export default function SchedulePage() {
  const router = useRouter();

  // View mode state
  const [viewMode, setViewMode] = useState<'table' | 'calendar'>('table');

  // Table view state
  const [schedule, setSchedule] = useState<ScheduleClass[]>([]);
  const [selectedDay, setSelectedDay] = useState<number>(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);

  // Calendar view state
  const [calendarData, setCalendarData] = useState<CalendarScheduleResponse | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ScheduleEvent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentView, setCurrentView] = useState('timeGridWeek');
  const [viewedDate, setViewedDate] = useState(new Date());
  const calendarRef = useRef<FullCalendar>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Common state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentDate] = useState(new Date());

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  // Fetch table view schedule (daily)
  const fetchTableSchedule = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/teachers/me/schedule?day=${selectedDay}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid - clear storage and redirect to login
          localStorage.clear();
          router.push('/login');
          return;
        }
        const errorText = await response.text();
        console.error('Schedule fetch error:', response.status, errorText);
        throw new Error(`Failed to fetch schedule: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Table schedule data:', data);
      setSchedule(data);
    } catch (err) {
      console.error('Error fetching table schedule:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load schedule. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedDay, router]);

  // Fetch calendar view schedule (date range)
  const fetchCalendarSchedule = useCallback(async (startDate: string, endDate: string) => {
    try {
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('No authentication token found. Please log in.');
        setIsInitialLoad(false);
        router.push('/login');
        return;
      }

      console.log(`Fetching calendar data for ${startDate} to ${endDate}`);

      const response = await fetch(
        `http://localhost:8000/api/v1/teachers/me/schedule/calendar?start_date=${startDate}&end_date=${endDate}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication failed - redirecting to login');
          localStorage.clear();
          setError('Session expired. Please log in again.');
          setTimeout(() => {
            router.push('/login');
          }, 1500);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Calendar schedule data received:', data.schedule_events?.length || 0, 'events');

      // Debug: Check for duplicate event IDs
      const eventIds = data.schedule_events?.map((e: ScheduleEvent) => e.id) || [];
      const uniqueIds = new Set(eventIds);
      if (eventIds.length !== uniqueIds.size) {
        console.warn(`WARNING: Received ${eventIds.length} events but only ${uniqueIds.size} unique IDs`);
      }

      //Debug: Log date distribution
      const dateGroups: Record<string, number> = {};
      data.schedule_events?.forEach((e: ScheduleEvent) => {
        const date = e.start.split('T')[0];
        dateGroups[date] = (dateGroups[date] || 0) + 1;
      });
      console.log('Events by date:', dateGroups);

      setCalendarData(data);
      setIsInitialLoad(false);
    } catch (err) {
      console.error('Error fetching calendar schedule:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load calendar schedule. Please try again.';
      setError(errorMessage);
      setIsInitialLoad(false);
    }
  }, [router]);

  // Handle calendar date range changes (lazy loading trigger)
  const handleDatesSet = useCallback((dateInfo: DatesSetArg) => {
    setViewedDate(dateInfo.view.currentStart);

    // Use the actual visible range from FullCalendar
    const startDate = new Date(dateInfo.start);
    const endDate = new Date(dateInfo.end);

    // Fetch data for this range from API
    const startStr = startDate.toISOString().split('T')[0];
    const endStr = endDate.toISOString().split('T')[0];

    console.log(`Requesting schedule from ${startStr} to ${endStr}`);
    fetchCalendarSchedule(startStr, endStr);
  }, [fetchCalendarSchedule]);

  // Use visible events from backend
  const visibleEvents = useMemo(() => {
    if (!calendarData) return [];
    console.log(`Showing ${calendarData.schedule_events.length} events from backend`);
    return calendarData.schedule_events;
  }, [calendarData]);

  // Convert schedule events to FullCalendar format
  const calendarEvents = useMemo(() => {
    const events = visibleEvents.map(event => ({
      id: event.id,
      title: event.course_name,
      start: event.start,
      end: event.end,
      backgroundColor: event.background_color,
      borderColor: event.background_color,
      extendedProps: {
        course_code: event.course_code,
        course_name: event.course_name,
        section_code: event.section_code,
        room_id: event.room_id,
        schedule_type: event.schedule_type,
        enrolled_count: event.enrolled_count,
        max_enrollment: event.max_enrollment,
        day_name: event.day_name,
      }
    }));

    // Debug: Log first few events to see their dates
    if (events.length > 0) {
      console.log('Sample events:', events.slice(0, 5).map(e => ({
        id: e.id,
        title: e.title,
        start: e.start,
        end: e.end
      })));
    }

    return events;
  }, [visibleEvents]);

  // Handle event click
  const handleEventClick = (clickInfo: EventClickArg) => {
    clickInfo.jsEvent.preventDefault();
    // Find the event from visible events
    const event = visibleEvents.find(e => e.id === clickInfo.event.id);

    if (event) {
      setSelectedEvent(event);
      setDialogOpen(true);
    }
  };

  // Calendar navigation functions
  const goToToday = () => {
    const calendarApi = calendarRef.current?.getApi();
    calendarApi?.today();
  };

  const goPrev = () => {
    const calendarApi = calendarRef.current?.getApi();
    calendarApi?.prev();
  };

  const goNext = () => {
    const calendarApi = calendarRef.current?.getApi();
    calendarApi?.next();
  };

  const changeView = (view: string) => {
    const calendarApi = calendarRef.current?.getApi();
    calendarApi?.changeView(view);
    setCurrentView(view);
  };

  // Handle view mode changes
  useEffect(() => {
    if (viewMode === 'table') {
      fetchTableSchedule();
    } else {
      // For calendar view, reset isInitialLoad so the loading overlay shows
      setIsInitialLoad(true);
    }
  }, [viewMode, fetchTableSchedule]);

  const formatTime = (timeStr: string) => {
    try {
      // timeStr is in format "HH:MM:SS" or ISO datetime
      if (timeStr.includes('T')) {
        const date = new Date(timeStr);
        return format(date, 'HH:mm');
      }
      const [hours, minutes] = timeStr.split(':');
      return `${hours}:${minutes}`;
    } catch {
      return timeStr;
    }
  };

  const getDuration = (startTime: string, endTime: string) => {
    try {
      const [startHours, startMinutes] = startTime.split(':').map(Number);
      const [endHours, endMinutes] = endTime.split(':').map(Number);
      const durationMinutes = (endHours * 60 + endMinutes) - (startHours * 60 + startMinutes);
      return `${durationMinutes} min`;
    } catch {
      return 'N/A';
    }
  };

  const getEnrollmentBadgeColor = (enrolled: number, max: number): string => {
    if (max === 0) return 'bg-gray-500';
    const percentage = (enrolled / max) * 100;
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-orange-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const navigateDay = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setSelectedDay((prev) => (prev === 0 ? 6 : prev - 1));
    } else {
      setSelectedDay((prev) => (prev === 6 ? 0 : prev + 1));
    }
  };

  const goToTodayTable = () => {
    const today = new Date().getDay();
    setSelectedDay(today === 0 ? 6 : today - 1);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header with View Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Teaching Schedule</h1>
          <p className="text-gray-500 mt-1">
            {viewMode === 'table' ? 'View your daily class schedule' : 'View your weekly calendar'}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <CalendarDays className="h-5 w-5 text-gray-500" />
            <span>{format(currentDate, 'MMMM dd, yyyy')}</span>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'table' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('table')}
              className="gap-2"
            >
              <List className="h-4 w-4" />
              Table
            </Button>
            <Button
              variant={viewMode === 'calendar' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('calendar')}
              className="gap-2"
            >
              <CalendarIcon className="h-4 w-4" />
              Calendar
            </Button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TABLE VIEW */}
      {viewMode === 'table' && (
        <>
          {/* Day Navigation */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => navigateDay('prev')}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>

                  <div className="text-center">
                    <CardTitle className="text-2xl">{daysOfWeek[selectedDay]}</CardTitle>
                    <CardDescription className="mt-1">
                      {schedule.length} {schedule.length === 1 ? 'class' : 'classes'} scheduled
                    </CardDescription>
                  </div>

                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => navigateDay('next')}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                <Button onClick={goToTodayTable} variant="outline">
                  Today
                </Button>
              </div>
            </CardHeader>
          </Card>

          {/* Quick Stats */}
          {!loading && schedule.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Clock className="h-8 w-8 text-blue-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">First Class</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatTime(schedule[0].start_time)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <BookOpen className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Classes</p>
                      <p className="text-2xl font-bold text-gray-900">{schedule.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-purple-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Students</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {schedule.reduce((sum, cls) => sum + cls.enrolled_count, 0)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <Card>
              <CardHeader>
                <Skeleton className="h-8 w-[200px]" />
                <Skeleton className="h-4 w-[300px] mt-2" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Schedule Table */}
          {!loading && schedule.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <CalendarDays className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  No Classes Scheduled
                </h3>
                <p className="text-gray-500">
                  You don&apos;t have any classes scheduled for {daysOfWeek[selectedDay]}.
                </p>
              </CardContent>
            </Card>
          )}

          {!loading && schedule.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Class Schedule</CardTitle>
                <CardDescription>
                  Your teaching schedule for {daysOfWeek[selectedDay]}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Course</TableHead>
                      <TableHead>Section</TableHead>
                      <TableHead>Room</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Students</TableHead>
                      <TableHead>Duration</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedule.map((cls) => (
                      <TableRow key={cls.schedule_id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-gray-500" />
                            <div>
                              <div className="font-semibold">
                                {formatTime(cls.start_time)}
                              </div>
                              <div className="text-xs text-gray-500">
                                to {formatTime(cls.end_time)}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-semibold text-blue-600">
                              {cls.course_code}
                            </div>
                            <div className="text-sm text-gray-600">
                              {cls.course_name}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{cls.section_code}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm">
                            <MapPin className="h-4 w-4 text-gray-500" />
                            {cls.room_id || 'TBA'}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="capitalize">
                            {cls.schedule_type || 'Lecture'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={`${getEnrollmentBadgeColor(
                              cls.enrolled_count,
                              cls.max_enrollment
                            )} text-white`}
                          >
                            {cls.enrolled_count} / {cls.max_enrollment}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {getDuration(cls.start_time, cls.end_time)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Weekly Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Navigation</CardTitle>
              <CardDescription>Jump to any day of the week</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-2">
                {daysOfWeek.map((day, index) => (
                  <Button
                    key={day}
                    variant={selectedDay === index ? 'default' : 'outline'}
                    onClick={() => setSelectedDay(index)}
                    className="w-full"
                  >
                    <div className="text-center">
                      <div className="text-xs font-semibold">{day.substring(0, 3)}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* CALENDAR VIEW */}
      {viewMode === 'calendar' && (
        <>
          {/* Loading Overlay */}
          {isInitialLoad && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                <p className="mt-4 text-muted-foreground">Loading your schedule...</p>
              </div>
            </div>
          )}

          {/* Info message if no events */}
          {calendarEvents.length === 0 && !isInitialLoad && calendarData && (
            <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <CardContent className="pt-4">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  No classes scheduled for this period. The system will load classes as you navigate the calendar.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Calendar Navigation */}
          <div className="flex flex-wrap gap-3 justify-between items-center">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={goPrev}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <div className="flex items-center gap-2">
                <CalendarIcon className="h-5 w-5 text-muted-foreground" />
                <span className="text-sm font-semibold">
                  {new Date(viewedDate).toLocaleDateString('en-US', {
                    month: 'long',
                    year: 'numeric'
                  })}
                </span>
              </div>

              <Button
                variant="ghost"
                size="icon"
                onClick={goNext}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={goToToday}
              >
                {currentView === "timeGridDay"
                  ? "Today"
                  : currentView === "timeGridWeek"
                  ? "This Week"
                  : "This Month"}
              </Button>

              <Tabs value={currentView} onValueChange={changeView}>
                <TabsList>
                  <TabsTrigger value="timeGridDay" className="gap-1">
                    <Clock className="h-4 w-4" />
                    {currentView === "timeGridDay" && <span className="text-xs">Day</span>}
                  </TabsTrigger>
                  <TabsTrigger value="timeGridWeek" className="gap-1">
                    <GraduationCap className="h-4 w-4" />
                    {currentView === "timeGridWeek" && <span className="text-xs">Week</span>}
                  </TabsTrigger>
                  <TabsTrigger value="dayGridMonth" className="gap-1">
                    <TableIcon className="h-4 w-4" />
                    {currentView === "dayGridMonth" && <span className="text-xs">Month</span>}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>

          {/* FullCalendar with shadcn styling */}
          <Card className="p-3">
            <FullCalendar
              ref={calendarRef}
              timeZone="local"
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView="timeGridWeek"
              headerToolbar={false}
              height="auto"
              contentHeight="auto"
              expandRows={true}
              events={calendarEvents}
              eventClick={handleEventClick}
              datesSet={handleDatesSet}
              slotMinTime="08:00:00"
              slotMaxTime="20:00:00"
              allDaySlot={false}
              firstDay={1}
              slotDuration="00:30:00"
              slotLabelInterval="01:00"
              slotLabelFormat={{
                hour: 'numeric',
                minute: '2-digit',
                hour12: false,
              }}
              eventTimeFormat={{
                hour: 'numeric',
                minute: '2-digit',
                hour12: false,
              }}
              eventBorderColor="black"
              nowIndicator
              displayEventEnd={true}
              windowResizeDelay={0}
            />
          </Card>
        </>
      )}

      {/* Event Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              {selectedEvent?.course_name}
            </DialogTitle>
            <DialogDescription className="flex items-center gap-2">
              <Badge variant="outline">{selectedEvent?.course_code}</Badge>
              Class details and information
            </DialogDescription>
          </DialogHeader>

          {selectedEvent && (
            <div className="space-y-4 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">
                    Section{selectedEvent.section_code.includes(',') ? 's' : ''}
                  </p>
                  {selectedEvent.section_code.includes(',') ? (
                    <div className="flex flex-wrap gap-1">
                      {selectedEvent.section_code.split(', ').map((section, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {section}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <Badge variant="outline">{selectedEvent.section_code}</Badge>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">Type</p>
                  <Badge variant="secondary" className="capitalize">
                    {selectedEvent.schedule_type || 'Lecture'}
                  </Badge>
                </div>
              </div>

              {/* Time and Location */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Time</p>
                    <p className="text-base font-semibold">
                      {formatTime(selectedEvent.start)} - {formatTime(selectedEvent.end)}
                    </p>
                    <p className="text-sm text-gray-600">{selectedEvent.day_name}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Room</p>
                    <p className="text-base font-semibold">{selectedEvent.room_id || 'TBA'}</p>
                  </div>
                </div>
              </div>

              {/* Enrollment Info */}
              <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                <Users className="h-5 w-5 text-purple-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-500">
                    Enrollment{selectedEvent.section_code.includes(',') ? ' (Combined Sections)' : ''}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge
                      className={`${getEnrollmentBadgeColor(
                        selectedEvent.enrolled_count,
                        selectedEvent.max_enrollment
                      )} text-white`}
                    >
                      {selectedEvent.enrolled_count} / {selectedEvent.max_enrollment}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      {selectedEvent.max_enrollment > 0
                        ? `${Math.round((selectedEvent.enrolled_count / selectedEvent.max_enrollment) * 100)}% full`
                        : 'No limit set'}
                    </span>
                  </div>
                  {selectedEvent.section_code.includes(',') && (
                    <p className="text-xs text-gray-500 mt-2">
                      Total enrollment across {selectedEvent.section_code.split(', ').length} sections
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
