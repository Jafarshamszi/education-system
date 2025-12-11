'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Calendar } from '@/components/ui/calendar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  BookOpen,
  Calendar as CalendarIcon,
  TrendingUp,
  Award,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  GraduationCap,
  User,
  MapPin,
  FileText,
  Target,
} from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import {
  StudentDashboardData
} from '@/types/students';

export default function StudentDashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<StudentDashboardData | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());

  // Mock data for demonstration - Replace with actual API calls
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        // TODO: Replace with actual API endpoints
        // const response = await fetch(`${API_BASE_URL}/students/me/dashboard`);
        // const data = await response.json();

        // Mock data for now
        const mockData: StudentDashboardData = {
          student: {
            id: '1',
            student_number: 'ST2024001',
            person: {
              id: '1',
              first_name: 'John',
              last_name: 'Doe',
              middle_name: 'Michael',
            },
            academic_program: {
              id: '1',
              code: 'CS-BS',
              name: {
                en: 'Computer Science',
                az: 'Kompüter Elmləri',
                ru: 'Компьютерные науки',
              },
            },
            status: 'active',
            study_mode: 'full_time',
            funding_type: 'government',
            enrollment_date: '2020-09-01',
            expected_graduation_date: '2024-06-30',
            gpa: 3.75,
            total_credits_earned: 90,
          },
          grades: [
            {
              id: '1',
              course_code: 'CS-301',
              course_name: { en: 'Database Systems', az: 'Verilənlər Bazası Sistemləri' },
              credit_hours: 4,
              grade: 'A',
              grade_points: 4.0,
              semester: 'Fall',
              academic_year: '2024-2025',
            },
            {
              id: '2',
              course_code: 'CS-302',
              course_name: { en: 'Software Engineering', az: 'Proqram Mühəndisliyi' },
              credit_hours: 4,
              grade: 'A-',
              grade_points: 3.7,
              semester: 'Fall',
              academic_year: '2024-2025',
            },
            {
              id: '3',
              course_code: 'CS-303',
              course_name: { en: 'Computer Networks', az: 'Kompüter Şəbəkələri' },
              credit_hours: 3,
              grade: 'B+',
              grade_points: 3.3,
              semester: 'Fall',
              academic_year: '2024-2025',
            },
            {
              id: '4',
              course_code: 'MATH-301',
              course_name: { en: 'Advanced Mathematics', az: 'Qabaqcıl Riyaziyyat' },
              credit_hours: 3,
              grade: 'B',
              grade_points: 3.0,
              semester: 'Fall',
              academic_year: '2024-2025',
            },
          ],
          upcoming_events: [
            {
              id: '1',
              title: 'Database Systems Midterm',
              description: 'Midterm exam covering chapters 1-5',
              event_type: 'exam',
              start_date: '2025-10-15T10:00:00',
              location: 'Room 301',
              course_code: 'CS-301',
            },
            {
              id: '2',
              title: 'Software Engineering Project Deadline',
              description: 'Final project submission',
              event_type: 'assignment',
              start_date: '2025-10-18T23:59:00',
              course_code: 'CS-302',
            },
            {
              id: '3',
              title: 'Computer Networks Lab',
              event_type: 'lecture',
              start_date: '2025-10-13T14:00:00',
              end_date: '2025-10-13T16:00:00',
              location: 'Lab 204',
              course_code: 'CS-303',
            },
            {
              id: '4',
              title: 'University Sports Day',
              event_type: 'other',
              start_date: '2025-10-20T09:00:00',
              location: 'Sports Complex',
            },
          ],
          attendance_summary: {
            total_classes: 48,
            attended: 44,
            absent: 2,
            late: 2,
            attendance_percentage: 91.7,
          },
          current_semester_stats: {
            enrolled_courses: 4,
            completed_credits: 14,
            gpa: 3.55,
          },
        };

        setDashboardData(mockData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getInitials = (firstName?: string, lastName?: string) => {
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'exam':
        return <FileText className="h-4 w-4" />;
      case 'assignment':
        return <Target className="h-4 w-4" />;
      case 'lecture':
        return <BookOpen className="h-4 w-4" />;
      default:
        return <CalendarIcon className="h-4 w-4" />;
    }
  };

  const getEventBadgeVariant = (eventType: string) => {
    switch (eventType) {
      case 'exam':
        return 'destructive' as const;
      case 'assignment':
        return 'default' as const;
      case 'lecture':
        return 'secondary' as const;
      default:
        return 'outline' as const;
    }
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-blue-600';
    if (grade.startsWith('C')) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <ProtectedRoute allowedRoles={['STUDENT']}>
        <div className="flex items-center justify-center h-[80vh]">
          <div className="text-muted-foreground">Loading dashboard...</div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!dashboardData) {
    return (
      <ProtectedRoute allowedRoles={['STUDENT']}>
        <div className="flex items-center justify-center h-[80vh]">
          <div className="text-muted-foreground">No data available</div>
        </div>
      </ProtectedRoute>
    );
  }

  const { student, grades, upcoming_events, attendance_summary, current_semester_stats } = dashboardData;

  return (
    <ProtectedRoute allowedRoles={['STUDENT']}>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">
              Welcome back, {student.person?.first_name}!
            </h1>
            <p className="text-muted-foreground">
              Here&apos;s your academic overview and upcoming events
            </p>
          </div>
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg">
              {getInitials(student.person?.first_name, student.person?.last_name)}
            </AvatarFallback>
          </Avatar>
        </div>

        {/* Student Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Student Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Student Number</p>
                <p className="font-mono font-semibold">{student.student_number}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Program</p>
                <p className="font-semibold">{student.academic_program?.name.en}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Study Mode</p>
                <Badge variant="outline" className="capitalize">
                  {student.study_mode?.replace('_', ' ')}
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant="default">{student.status}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overall GPA</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{student.gpa?.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Out of 4.00</p>
              <Progress value={(student.gpa || 0) * 25} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Credits Earned</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{student.total_credits_earned}</div>
              <p className="text-xs text-muted-foreground">Total credits completed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Courses</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{current_semester_stats.enrolled_courses}</div>
              <p className="text-xs text-muted-foreground">This semester</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Attendance</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {attendance_summary.attendance_percentage.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                {attendance_summary.attended}/{attendance_summary.total_classes} classes
              </p>
              <Progress value={attendance_summary.attendance_percentage} className="mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="grades" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="grades">Grades</TabsTrigger>
            <TabsTrigger value="schedule">Schedule & Events</TabsTrigger>
            <TabsTrigger value="attendance">Attendance</TabsTrigger>
          </TabsList>

          {/* Grades Tab */}
          <TabsContent value="grades" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GraduationCap className="h-5 w-5" />
                  Course Grades
                </CardTitle>
                <CardDescription>
                  Current semester: Fall 2024-2025
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {grades.map((grade) => (
                    <div
                      key={grade.id}
                      className="flex items-center justify-between p-4 rounded-lg border"
                    >
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <code className="text-sm font-mono bg-muted px-2 py-1 rounded">
                            {grade.course_code}
                          </code>
                          <h4 className="font-semibold">{grade.course_name.en}</h4>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {grade.credit_hours} credits • {grade.semester} {grade.academic_year}
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${getGradeColor(grade.grade)}`}>
                            {grade.grade}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {grade.grade_points.toFixed(1)} GPA
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <Separator className="my-6" />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Semester GPA</p>
                    <p className="text-2xl font-bold">{current_semester_stats.gpa.toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Credits This Semester</p>
                    <p className="text-2xl font-bold">{current_semester_stats.completed_credits}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Schedule & Events Tab */}
          <TabsContent value="schedule" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Calendar */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CalendarIcon className="h-5 w-5" />
                    Academic Calendar
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    className="rounded-md border"
                  />
                </CardContent>
              </Card>

              {/* Upcoming Events */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Upcoming Events
                  </CardTitle>
                  <CardDescription>Your schedule for the next week</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[350px] pr-4">
                    <div className="space-y-4">
                      {upcoming_events.map((event) => (
                        <div
                          key={event.id}
                          className="flex gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
                        >
                          <div className="flex items-start mt-1">
                            {getEventIcon(event.event_type)}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-semibold text-sm leading-tight">
                                {event.title}
                              </h4>
                              <Badge variant={getEventBadgeVariant(event.event_type)} className="text-xs">
                                {event.event_type}
                              </Badge>
                            </div>
                            {event.description && (
                              <p className="text-xs text-muted-foreground">
                                {event.description}
                              </p>
                            )}
                            <div className="flex flex-col gap-1 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(event.start_date).toLocaleString()}
                              </div>
                              {event.location && (
                                <div className="flex items-center gap-1">
                                  <MapPin className="h-3 w-3" />
                                  {event.location}
                                </div>
                              )}
                              {event.course_code && (
                                <code className="text-xs bg-muted px-1.5 py-0.5 rounded w-fit">
                                  {event.course_code}
                                </code>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Attendance Tab */}
          <TabsContent value="attendance" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Attendance Summary</CardTitle>
                  <CardDescription>Overall attendance statistics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Attendance Rate</span>
                      <span className="font-semibold">
                        {attendance_summary.attendance_percentage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={attendance_summary.attendance_percentage} />
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span className="text-sm">Present</span>
                      </div>
                      <span className="font-semibold">{attendance_summary.attended}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-600" />
                        <span className="text-sm">Absent</span>
                      </div>
                      <span className="font-semibold">{attendance_summary.absent}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                        <span className="text-sm">Late</span>
                      </div>
                      <span className="font-semibold">{attendance_summary.late}</span>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-sm font-medium">Total Classes</span>
                    <span className="text-2xl font-bold">{attendance_summary.total_classes}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Attendance Tips</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3 text-sm">
                    <div className="flex gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                      <div>
                        <p className="font-medium">Great attendance!</p>
                        <p className="text-muted-foreground">
                          You&apos;re maintaining excellent attendance. Keep it up!
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <AlertCircle className="h-5 w-5 text-yellow-600 shrink-0" />
                      <div>
                        <p className="font-medium">Attendance Policy</p>
                        <p className="text-muted-foreground">
                          Minimum 75% attendance required for exam eligibility.
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <BookOpen className="h-5 w-5 text-blue-600 shrink-0" />
                      <div>
                        <p className="font-medium">Pro Tip</p>
                        <p className="text-muted-foreground">
                          Regular attendance correlates with better academic performance.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </ProtectedRoute>
  );
}
