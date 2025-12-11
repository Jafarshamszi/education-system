"use client";

import { useState, useEffect } from "react";
import {
  BookOpen,
  Users,
  Clock,
  GraduationCap,
  Globe,
  CalendarDays,
  CheckCircle2,
  XCircle,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface DetailedCourse {
  offering_id: string;
  course_code: string;
  course_name: string;
  course_description: string | null;
  credit_hours: number;
  lecture_hours: number;
  lab_hours: number;
  tutorial_hours: number;
  course_level: string | null;
  section_code: string;
  semester: string;
  academic_year: string;
  term_type: string;
  max_enrollment: number;
  current_enrollment: number;
  delivery_mode: string | null;
  enrollment_status: string;
  language_of_instruction: string;
  is_published: boolean;
}

interface CoursesData {
  total_courses: number;
  courses: DetailedCourse[];
}

export default function MyCoursesPage() {
  const [coursesData, setCoursesData] = useState<CoursesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourse, setSelectedCourse] = useState<DetailedCourse | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("No authentication token found");
          setLoading(false);
          return;
        }

        const response = await fetch("http://localhost:8000/api/v1/teachers/me/courses", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch courses");
        }

        const data = await response.json();
        setCoursesData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  // Filter courses based on search query
  const filteredCourses = coursesData?.courses.filter(
    (course) =>
      course.course_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.course_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.section_code.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Get badge variant for enrollment status
  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status.toLowerCase()) {
      case "open":
        return "default";
      case "closed":
        return "secondary";
      case "cancelled":
        return "destructive";
      default:
        return "outline";
    }
  };

  // Get badge variant for delivery mode
  const getDeliveryBadgeVariant = (mode: string | null): "default" | "secondary" | "outline" => {
    if (!mode) return "outline";
    switch (mode.toLowerCase()) {
      case "in_person":
        return "default";
      case "online":
        return "secondary";
      default:
        return "outline";
    }
  };

  // Format delivery mode text
  const formatDeliveryMode = (mode: string | null): string => {
    if (!mode) return "Not specified";
    return mode.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  // Format enrollment status
  const formatEnrollmentStatus = (status: string): string => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  // Handle course card click
  const handleCourseClick = (course: DetailedCourse) => {
    setSelectedCourse(course);
    setDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-6 w-96" />
        </div>
        <div className="mb-6">
          <Skeleton className="h-10 w-full max-w-md" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-80" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">My Courses</h1>
        <p className="text-muted-foreground">
          Manage and view details of all courses you are teaching
        </p>
      </div>

      {/* Search and Stats */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="w-full sm:w-96">
          <Input
            type="search"
            placeholder="Search courses..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
        </div>
        <div className="flex gap-2 items-center">
          <Badge variant="outline" className="text-sm px-3 py-1">
            <BookOpen className="w-4 h-4 mr-1" />
            {filteredCourses.length} {filteredCourses.length === 1 ? "Course" : "Courses"}
          </Badge>
        </div>
      </div>

      {/* Courses Grid */}
      {filteredCourses.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg">
              {searchQuery
                ? "No courses found matching your search"
                : "No courses assigned yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredCourses.map((course) => (
            <Card
              key={course.offering_id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleCourseClick(course)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between mb-2">
                  <Badge variant="outline" className="font-mono text-xs">
                    {course.course_code}
                  </Badge>
                  {course.is_published ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <XCircle className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                <CardTitle className="text-lg line-clamp-2">
                  {course.course_name}
                </CardTitle>
                <CardDescription className="line-clamp-1">
                  {course.section_code}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3">
                {/* Academic Info */}
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <CalendarDays className="w-4 h-4 text-muted-foreground" />
                    <span>{course.semester} {course.academic_year}</span>
                  </div>
                </div>

                {/* Credit Hours */}
                <div className="flex items-center gap-2 text-sm">
                  <GraduationCap className="w-4 h-4 text-muted-foreground" />
                  <span className="font-semibold">{course.credit_hours} Credits</span>
                  {course.lecture_hours > 0 && (
                    <span className="text-muted-foreground">
                      • {course.lecture_hours}h Lecture
                    </span>
                  )}
                </div>

                {/* Lab/Tutorial Hours */}
                {(course.lab_hours > 0 || course.tutorial_hours > 0) && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    {course.lab_hours > 0 && <span>{course.lab_hours}h Lab</span>}
                    {course.lab_hours > 0 && course.tutorial_hours > 0 && <span>•</span>}
                    {course.tutorial_hours > 0 && <span>{course.tutorial_hours}h Tutorial</span>}
                  </div>
                )}

                {/* Enrollment */}
                <div className="flex items-center gap-2 text-sm">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {course.current_enrollment}/{course.max_enrollment}
                      </span>
                      <span className="text-muted-foreground">enrolled</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5 mt-1">
                      <div
                        className="bg-primary h-1.5 rounded-full"
                        style={{
                          width: `${Math.min(
                            (course.current_enrollment / course.max_enrollment) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Delivery Mode & Language */}
                <div className="flex flex-wrap gap-2 pt-2">
                  <Badge variant={getDeliveryBadgeVariant(course.delivery_mode)}>
                    {formatDeliveryMode(course.delivery_mode)}
                  </Badge>
                  <Badge variant={getStatusBadgeVariant(course.enrollment_status)}>
                    {formatEnrollmentStatus(course.enrollment_status)}
                  </Badge>
                  {course.language_of_instruction && (
                    <Badge variant="outline" className="gap-1">
                      <Globe className="w-3 h-3" />
                      {course.language_of_instruction.toUpperCase()}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Course Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-start justify-between mb-2">
              <Badge variant="outline" className="font-mono text-sm">
                {selectedCourse?.course_code}
              </Badge>
              {selectedCourse?.is_published ? (
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="text-xs font-medium">Published</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-gray-400">
                  <XCircle className="w-4 h-4" />
                  <span className="text-xs font-medium">Not Published</span>
                </div>
              )}
            </div>
            <DialogTitle className="text-2xl">{selectedCourse?.course_name}</DialogTitle>
            <DialogDescription className="text-base">
              Section: {selectedCourse?.section_code}
            </DialogDescription>
          </DialogHeader>

          {selectedCourse && (
            <div className="space-y-6 mt-4">
              {/* Course Description */}
              {selectedCourse.course_description && (
                <div>
                  <h3 className="font-semibold text-sm text-muted-foreground mb-2">Description</h3>
                  <p className="text-sm leading-relaxed">{selectedCourse.course_description}</p>
                </div>
              )}

              {/* Academic Information */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Academic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <CalendarDays className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Academic Term</p>
                      <p className="font-medium">{selectedCourse.semester} {selectedCourse.academic_year}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <GraduationCap className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Credit Hours</p>
                      <p className="font-medium">{selectedCourse.credit_hours} Credits</p>
                    </div>
                  </div>
                  {selectedCourse.course_level && (
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Course Level</p>
                        <p className="font-medium">{selectedCourse.course_level}</p>
                      </div>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Language</p>
                      <p className="font-medium">{selectedCourse.language_of_instruction.toUpperCase()}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Contact Hours */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Contact Hours</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Lecture</p>
                      <p className="font-medium">{selectedCourse.lecture_hours} hours</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Lab</p>
                      <p className="font-medium">{selectedCourse.lab_hours} hours</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Tutorial</p>
                      <p className="font-medium">{selectedCourse.tutorial_hours} hours</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Enrollment Information */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Enrollment Information</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-muted-foreground" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs text-muted-foreground">Current Enrollment</p>
                        <p className="font-medium text-sm">
                          {selectedCourse.current_enrollment} / {selectedCourse.max_enrollment} students
                        </p>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(
                              (selectedCourse.current_enrollment / selectedCourse.max_enrollment) * 100,
                              100
                            )}%`,
                          }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {Math.round((selectedCourse.current_enrollment / selectedCourse.max_enrollment) * 100)}% filled
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={getDeliveryBadgeVariant(selectedCourse.delivery_mode)}>
                      {formatDeliveryMode(selectedCourse.delivery_mode)}
                    </Badge>
                    <Badge variant={getStatusBadgeVariant(selectedCourse.enrollment_status)}>
                      {formatEnrollmentStatus(selectedCourse.enrollment_status)}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="border-t pt-4">
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Quick Actions</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
                    <Users className="w-4 h-4" />
                    <span className="text-sm">View Students</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
                    <BookOpen className="w-4 h-4" />
                    <span className="text-sm">Course Materials</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-sm">Mark Attendance</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
                    <GraduationCap className="w-4 h-4" />
                    <span className="text-sm">Enter Grades</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
