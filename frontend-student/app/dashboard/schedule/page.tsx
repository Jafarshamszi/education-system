"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  User,
  GraduationCap,
  Table as TableIcon,
} from "lucide-react";
import "@/styles/calendar.css";
import type { EventClickArg, DatesSetArg } from "@fullcalendar/core";

interface ScheduleEvent {
  id: string;
  title: string;
  course_code: string;
  course_name: string;
  start: string;
  end: string;
  day_of_week: number;
  day_name: string;
  room: string | null;
  schedule_type: string | null;
  instructor_name: string | null;
  background_color: string;
}

interface ScheduleData {
  student_id: string;
  student_number: string;
  full_name: string;
  schedule_events: ScheduleEvent[];
}

export default function SchedulePage() {
  const [scheduleData, setScheduleData] = useState<ScheduleData | null>(null);
  const [loading, setLoading] = useState(false); // Start false to let calendar mount
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ScheduleEvent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentView, setCurrentView] = useState("timeGridWeek");
  const [viewedDate, setViewedDate] = useState(new Date());
  const [visibleDateRange, setVisibleDateRange] = useState<{ start: Date; end: Date } | null>(null);
  const calendarRef = useRef<FullCalendar>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Fetch schedule data from API
  const fetchScheduleData = async (startDate: string, endDate: string) => {
    try {
      // Only show loading spinner if it's not the initial load
      if (!isInitialLoad) {
        setLoading(true);
      }
      setError(null);

      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('No authentication token found. Please log in.');
        setLoading(false);
        setIsInitialLoad(false);
        return;
      }

      console.log(`Fetching schedule from ${startDate} to ${endDate}`);

      const response = await fetch(
        `http://localhost:8000/api/v1/students/me/schedule?start_date=${startDate}&end_date=${endDate}`,
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
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_id');
          localStorage.removeItem('username');
          localStorage.removeItem('user_type');
          setError('Session expired. Please log in again.');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Schedule data received:', data);
      console.log('Number of events:', data.schedule_events?.length || 0);

      setScheduleData(data);
      setIsInitialLoad(false);
    } catch (err) {
      console.error('Error fetching schedule:', err);
      setError(err instanceof Error ? err.message : 'Failed to load schedule');
      setIsInitialLoad(false);
    } finally {
      setLoading(false);
    }
  };

  // Backend already sends events for the requested date range
  // We just use them directly without additional filtering
  const visibleEvents = useMemo(() => {
    if (!scheduleData) return [];

    // Backend has already filtered events to the requested range
    // No need for additional filtering
    console.log(`Showing ${scheduleData.schedule_events.length} events from backend`);
    return scheduleData.schedule_events;
  }, [scheduleData]);

  // Handle calendar date range changes (lazy loading trigger)
  const handleDatesSet = (dateInfo: DatesSetArg) => {
    setViewedDate(dateInfo.view.currentStart);

    // Use the actual visible range from FullCalendar (no buffer)
    const startDate = new Date(dateInfo.start);
    const endDate = new Date(dateInfo.end);

    // Update visible range (triggers useMemo recalculation)
    setVisibleDateRange({ start: startDate, end: endDate });

    // Fetch data for this range from API
    const startStr = startDate.toISOString().split('T')[0];
    const endStr = endDate.toISOString().split('T')[0];

    console.log(`Requesting schedule from ${startStr} to ${endStr}`);
    fetchScheduleData(startStr, endStr);
  };

  const handleEventClick = (info: EventClickArg) => {
    // Find the event from visible events
    const event = visibleEvents.find(e => e.id === info.event.id);

    if (event) {
      setSelectedEvent(event);
      setDialogOpen(true);
    }
  };

  const goToToday = () => {
    const calendarApi = calendarRef.current?.getApi();
    const today = new Date();
    const academicYearStart = new Date('2024-09-15');
    const academicYearEnd = new Date('2025-06-14');

    // If today is outside academic year, go to start of academic year
    if (today < academicYearStart || today > academicYearEnd) {
      calendarApi?.gotoDate(academicYearStart);
    } else {
      calendarApi?.today();
    }
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

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Schedule</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => {
                const today = new Date();
                const startDate = new Date(today);
                startDate.setDate(startDate.getDate() - 7);
                const endDate = new Date(today);
                endDate.setDate(endDate.getDate() + 7);
                fetchScheduleData(
                  startDate.toISOString().split('T')[0],
                  endDate.toISOString().split('T')[0]
                );
              }}
              className="w-full"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Convert schedule events to FullCalendar format
  const calendarEvents = visibleEvents.map(event => ({
    id: event.id,
    title: event.course_name,
    start: event.start,
    end: event.end,
    backgroundColor: event.background_color,
    borderColor: event.background_color,
    extendedProps: {
      course_code: event.course_code,
      course_name: event.course_name,
      room: event.room,
      schedule_type: event.schedule_type,
      instructor_name: event.instructor_name,
      day_name: event.day_name,
    }
  }));

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8 relative">
      {/* Loading Overlay */}
      {isInitialLoad && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading your schedule...</p>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-bold tracking-tight">Class Schedule</h1>
        <p className="text-muted-foreground">
          View your weekly class schedule (Academic Year: Sep 2024 - Jun 2025)
        </p>
      </div>

      {/* Info message if no events */}
      {calendarEvents.length === 0 && !isInitialLoad && scheduleData && (
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
          initialDate="2024-09-16"
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

      {/* Event Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
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
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <CalendarIcon className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Day & Time</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedEvent.day_name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(selectedEvent.start).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false,
                    })}{' '}
                    -{' '}
                    {new Date(selectedEvent.end).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false,
                    })}
                  </p>
                </div>
              </div>

              {selectedEvent.room && (
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Room</p>
                    <p className="text-sm text-muted-foreground">{selectedEvent.room}</p>
                  </div>
                </div>
              )}

              {selectedEvent.schedule_type && (
                <div className="flex items-start gap-3">
                  <GraduationCap className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Type</p>
                    <Badge variant="outline">{selectedEvent.schedule_type}</Badge>
                  </div>
                </div>
              )}

              {selectedEvent.instructor_name && (
                <div className="flex items-start gap-3">
                  <User className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Instructor</p>
                    <p className="text-sm text-muted-foreground">
                      {selectedEvent.instructor_name}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
