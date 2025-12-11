"use client";

import { useState, useEffect } from "react";
import { BookOpen, Users, TrendingUp, Award, Clock, BarChart3 } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface CourseInfo {
  offering_id: string;
  course_code: string;
  course_name: string;
  student_count: number;
  semester: string | null;
  academic_year: string | null;
  section_code?: string;
}

interface DashboardData {
  teacher_id: string;
  employee_number: string;
  full_name: string;
  position_title: string | null;
  academic_rank: string | null;
  department: string | null;
  total_courses: number;
  total_students: number;
  courses: CourseInfo[];
}

export default function TeacherDashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("No authentication token found. Please log in.");
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:8000/api/v1/teachers/me/dashboard", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_id");
          localStorage.removeItem("username");
          localStorage.removeItem("user_type");
          setError("Session expired. Please log in again.");
          setTimeout(() => {
            window.location.href = "/login";
          }, 1500);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Dashboard data received:", data);
      setDashboardData(data);
    } catch (err) {
      console.error("Error fetching dashboard:", err);
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-4 rounded-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <Card className="w-full max-w-md border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <button
              onClick={fetchDashboardData}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Try Again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Welcome back, {dashboardData.full_name}!</h2>
        <p className="text-muted-foreground mt-2">
          Here&apos;s an overview of your teaching activities
        </p>
      </div>

      {dashboardData.position_title && (
        <div className="flex gap-2 items-center flex-wrap">
          <Badge variant="outline" className="text-sm">
            <Award className="mr-1 h-3 w-3" />
            {dashboardData.position_title}
          </Badge>
          {dashboardData.academic_rank && (
            <Badge variant="outline" className="text-sm">
              {dashboardData.academic_rank}
            </Badge>
          )}
          {dashboardData.department && (
            <Badge variant="outline" className="text-sm">
              {dashboardData.department}
            </Badge>
          )}
          <Badge variant="outline" className="text-sm font-mono">
            ID: {dashboardData.employee_number}
          </Badge>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_courses}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active this semester
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_students}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all courses
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Class Size</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.total_courses > 0
                ? Math.round(dashboardData.total_students / dashboardData.total_courses)
                : 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Students per course
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Largest Class</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.courses.length > 0
                ? Math.max(...dashboardData.courses.map(c => c.student_count))
                : 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Students in largest course
            </p>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className="text-2xl font-bold tracking-tight mb-4">My Courses</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dashboardData.courses.map((course, index) => (
            <Card key={course.offering_id || `course-${index}`} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <Badge variant="outline" className="font-mono text-xs mb-2">
                      {course.course_code}
                    </Badge>
                    <CardTitle className="text-lg">{course.course_name}</CardTitle>
                  </div>
                  <BookOpen className="h-5 w-5 text-muted-foreground" />
                </div>
                {(course.semester || course.academic_year) && (
                  <CardDescription className="flex items-center gap-2 mt-2">
                    <Clock className="h-3 w-3" />
                    {course.semester} {course.academic_year}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Enrolled Students</span>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="font-semibold">{course.student_count}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t flex gap-2">
                    <button className="flex-1 px-3 py-2 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                      View Course
                    </button>
                    <button className="flex-1 px-3 py-2 text-xs border rounded-md hover:bg-accent transition-colors">
                      Attendance
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Course Distribution</CardTitle>
            <CardDescription>Enrollment across your courses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.courses.slice(0, 5).map((course, idx) => {
                const percentage = dashboardData.total_students > 0
                  ? Math.round((course.student_count / dashboardData.total_students) * 100)
                  : 0;
                
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium truncate max-w-[200px]">
                        {course.course_code}
                      </span>
                      <span className="text-muted-foreground">
                        {course.student_count} students ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Teaching Summary</CardTitle>
            <CardDescription>Your course statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-blue-500" />
                  <span className="text-sm">Total Courses</span>
                </div>
                <span className="text-sm font-semibold">
                  {dashboardData.total_courses}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Total Students</span>
                </div>
                <span className="text-sm font-semibold">
                  {dashboardData.total_students}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-purple-500" />
                  <span className="text-sm">Avg. Class Size</span>
                </div>
                <span className="text-sm font-semibold">
                  {dashboardData.total_courses > 0
                    ? Math.round(dashboardData.total_students / dashboardData.total_courses)
                    : 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-orange-500" />
                  <span className="text-sm">Largest Class</span>
                </div>
                <span className="text-sm font-semibold">
                  {Math.max(...dashboardData.courses.map(c => c.student_count), 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
