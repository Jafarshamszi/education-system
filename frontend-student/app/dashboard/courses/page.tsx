"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BookOpen, Calendar, User, GraduationCap, TrendingUp, CalendarDays } from "lucide-react";

interface CourseSchedule {
  day_of_week: number;
  day_name: string;
  start_time: string;
  end_time: string;
  room: string | null;
  schedule_type: string | null;
  instructor_name: string | null;
}

interface CourseDetail {
  enrollment_id: string;
  course_id: string;
  course_code: string;
  course_name: string;
  credits: number;
  enrollment_status: string;
  grade: string | null;
  grade_points: number | null;
  attendance_percentage: number | null;
  instructor_name: string | null;
  schedules: CourseSchedule[];
  semester: string | null;
  academic_year: string | null;
}

interface CoursesData {
  student_id: string;
  student_number: string;
  full_name: string;
  enrolled_courses: CourseDetail[];
  completed_courses: CourseDetail[];
}

export default function CoursesPage() {
  const [coursesData, setCoursesData] = useState<CoursesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCoursesData();
  }, []);

  const fetchCoursesData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('No authentication token found. Please log in.');
        setLoading(false);
        return;
      }

      console.log('Fetching courses data from API...');

      const response = await fetch('http://localhost:8000/api/v1/students/me/courses', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Courses data received:', data);
      setCoursesData(data);
    } catch (err) {
      console.error('Error fetching courses:', err);
      setError(err instanceof Error ? err.message : 'Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: string | null): "default" | "secondary" | "outline" | "destructive" => {
    if (!grade) return 'secondary';
    const upperGrade = grade.toUpperCase();
    if (upperGrade.startsWith('A')) return 'default';
    if (upperGrade.startsWith('B')) return 'secondary';
    if (upperGrade.startsWith('C')) return 'outline';
    return 'destructive';
  };

  const getAttendanceColor = (percentage: number | null): "default" | "secondary" | "destructive" => {
    if (percentage === null) return 'secondary';
    if (percentage >= 80) return 'default';
    if (percentage >= 60) return 'secondary';
    return 'destructive';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading courses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Courses</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <button
              onClick={fetchCoursesData}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Retry
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!coursesData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">No course data available</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Courses</h1>
        <p className="text-muted-foreground">
          View and manage your enrolled and completed courses
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enrolled Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{coursesData.enrolled_courses.length}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Courses</CardTitle>
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{coursesData.completed_courses.length}</div>
            <p className="text-xs text-muted-foreground">Successfully finished</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {coursesData.enrolled_courses.reduce((sum, course) => sum + course.credits, 0)}
            </div>
            <p className="text-xs text-muted-foreground">This semester</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="enrolled" className="space-y-4">
        <TabsList>
          <TabsTrigger value="enrolled">
            Enrolled ({coursesData.enrolled_courses.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed ({coursesData.completed_courses.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="enrolled" className="space-y-4">
          {coursesData.enrolled_courses.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">No enrolled courses found</p>
              </CardContent>
            </Card>
          ) : (
            coursesData.enrolled_courses.map((course) => (
              <Card key={course.enrollment_id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="flex items-center gap-2">
                        {course.course_code}
                        <Badge variant={course.enrollment_status === 'enrolled' ? 'default' : 'secondary'}>
                          {course.enrollment_status}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-base">
                        {course.course_name}
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{course.credits} Credits</div>
                      {course.semester && (
                        <div className="text-xs text-muted-foreground">
                          {course.semester} {course.academic_year}
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {course.instructor_name && (
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">Instructor</p>
                          <p className="text-xs text-muted-foreground">{course.instructor_name}</p>
                        </div>
                      </div>
                    )}
                    {course.grade && (
                      <div className="flex items-center gap-2">
                        <GraduationCap className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">Current Grade</p>
                          <Badge variant={getGradeColor(course.grade)}>
                            {course.grade}
                            {course.grade_points && ` (${course.grade_points.toFixed(2)})`}
                          </Badge>
                        </div>
                      </div>
                    )}
                    {course.attendance_percentage !== null && (
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">Attendance</p>
                          <Badge variant={getAttendanceColor(course.attendance_percentage)}>
                            {course.attendance_percentage.toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* View Schedule Button */}
                  <div className="pt-4 border-t">
                    <Link href="/dashboard/schedule">
                      <Button variant="outline" className="w-full">
                        <CalendarDays className="mr-2 h-4 w-4" />
                        View Class Schedule
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          {coursesData.completed_courses.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">No completed courses found</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Completed Courses</CardTitle>
                <CardDescription>
                  Your academic history and grades
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Course Code</TableHead>
                      <TableHead>Course Name</TableHead>
                      <TableHead>Credits</TableHead>
                      <TableHead>Grade</TableHead>
                      <TableHead>Grade Points</TableHead>
                      <TableHead>Semester</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {coursesData.completed_courses.map((course) => (
                      <TableRow key={course.enrollment_id}>
                        <TableCell className="font-medium">
                          {course.course_code}
                        </TableCell>
                        <TableCell>{course.course_name}</TableCell>
                        <TableCell>{course.credits}</TableCell>
                        <TableCell>
                          {course.grade ? (
                            <Badge variant={getGradeColor(course.grade)}>
                              {course.grade}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {course.grade_points !== null ? (
                            course.grade_points.toFixed(2)
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {course.semester} {course.academic_year}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
