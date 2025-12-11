"use client"

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  BookOpen, 
  Calendar as CalendarIcon, 
  TrendingUp, 
  Award,
  FileText,
  Clock
} from "lucide-react";
import ProtectedRoute from '@/components/auth/ProtectedRoute';

interface CourseGrade {
  course_code: string;
  course_name: string;
  grade: string;
  credits: number;
}

interface Event {
  id: number;
  title: string;
  date: string;
  time: string;
  type: 'exam' | 'assignment' | 'lecture' | 'other';
}

interface StudentDashboardData {
  full_name: string;
  current_gpa: number;
  total_credits: number;
  courses: CourseGrade[];
  upcoming_events: Event[];
}

export default function StudentDashboard() {
  return (
    <ProtectedRoute allowedRoles={["STUDENT"]}>
      <DashboardContent />
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const [dashboardData, setDashboardData] = useState<StudentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.warn('No access token found, using mock data');
        // Fallback to mock data if no token
        const mockData: StudentDashboardData = {
          full_name: localStorage.getItem('full_name') || 'Student Name',
          current_gpa: 3.75,
          total_credits: 90,
          courses: [
            { course_code: 'CS301', course_name: 'Data Structures', grade: 'A', credits: 3 },
            { course_code: 'CS302', course_name: 'Algorithms', grade: 'A-', credits: 3 },
            { course_code: 'MATH201', course_name: 'Discrete Mathematics', grade: 'B+', credits: 4 },
            { course_code: 'ENG101', course_name: 'Technical Writing', grade: 'A', credits: 3 },
          ],
          upcoming_events: [],
        };
        setDashboardData(mockData);
        setLoading(false);
        return;
      }

      console.log('Fetching dashboard data from API...');
      
      // Fetch real data from API
      const response = await fetch('http://localhost:8000/api/v1/students/me/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Dashboard data received:', data);

      // Transform API response to match our interface
      const transformedData: StudentDashboardData = {
        full_name: data.full_name,
        current_gpa: data.current_gpa || 0,
        total_credits: data.total_credits || 0,
        courses: data.courses || [],
        upcoming_events: data.upcoming_events || [],
      };

      setDashboardData(transformedData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // Fallback to mock data on error
      const mockData: StudentDashboardData = {
        full_name: localStorage.getItem('full_name') || 'Student Name',
        current_gpa: 3.75,
        total_credits: 90,
        courses: [
          { course_code: 'CS301', course_name: 'Data Structures', grade: 'A', credits: 3 },
          { course_code: 'CS302', course_name: 'Algorithms', grade: 'A-', credits: 3 },
        ],
        upcoming_events: [],
      };
      setDashboardData(mockData);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium">Unable to load dashboard</div>
        </div>
      </div>
    );
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'exam':
        return <FileText className="h-4 w-4" />;
      case 'assignment':
        return <BookOpen className="h-4 w-4" />;
      default:
        return <CalendarIcon className="h-4 w-4" />;
    }
  };

  const getEventColor = (type: string): "default" | "destructive" | "secondary" | "outline" => {
    switch (type) {
      case 'exam':
        return 'destructive';
      case 'assignment':
        return 'default';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current GPA</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.current_gpa.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Out of 4.0</p>
            <Progress value={(dashboardData.current_gpa / 4.0) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_credits}</div>
            <p className="text-xs text-muted-foreground">Credits earned</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.courses.length}</div>
            <p className="text-xs text-muted-foreground">This semester</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Events</CardTitle>
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.upcoming_events.length}</div>
            <p className="text-xs text-muted-foreground">Next 7 days</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Current Courses</CardTitle>
            <CardDescription>Your enrolled courses and current grades</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.courses.map((course, index) => (
                <div key={index} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{course.course_code}</Badge>
                      <p className="font-medium">{course.course_name}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">{course.credits} credits</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="text-lg font-bold">{course.grade}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Upcoming Events</CardTitle>
            <CardDescription>Your schedule for the next week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.upcoming_events.map((event) => (
                <div key={event.id} className="flex items-start gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                    {getEventIcon(event.type)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="font-medium leading-none">{event.title}</p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CalendarIcon className="h-3 w-3" />
                      <span>{event.date}</span>
                      <Clock className="h-3 w-3 ml-2" />
                      <span>{event.time}</span>
                    </div>
                    <Badge variant={getEventColor(event.type)} className="text-xs">
                      {event.type}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Academic Progress</CardTitle>
            <CardDescription>Track your degree completion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Credits Completed</span>
                <span className="text-sm text-muted-foreground">{dashboardData.total_credits}/120</span>
              </div>
              <Progress value={(dashboardData.total_credits / 120) * 100} />
            </div>
            <Separator />
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Current Semester Credits</span>
                <span className="text-sm text-muted-foreground">
                  {dashboardData.courses.reduce((sum, course) => sum + course.credits, 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and links</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <a href="/dashboard/grades" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-accent">
              <Award className="h-4 w-4" />
              <span className="text-sm font-medium">View All Grades</span>
            </a>
            <a href="/dashboard/schedule" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-accent">
              <CalendarIcon className="h-4 w-4" />
              <span className="text-sm font-medium">View Schedule</span>
            </a>
            <a href="/dashboard/assignments" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-accent">
              <FileText className="h-4 w-4" />
              <span className="text-sm font-medium">View Assignments</span>
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
