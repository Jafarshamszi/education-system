"use client";

import { useState, useEffect } from "react";
import { Users, BookOpen, Mail, Calendar, Award, TrendingUp, User } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface StudentInfo {
  student_id: string;
  student_number: string;
  full_name: string;
  email: string | null;
  enrollment_date: string | null;
  enrollment_status: string;
  grade: string | null;
  grade_points: number | null;
  attendance_percentage: number | null;
  status: string;
  study_mode: string | null;
  gpa: number | null;
}

interface CourseStudentsInfo {
  offering_id: string;
  course_code: string;
  course_name: string;
  section_code: string;
  semester: string;
  academic_year: string;
  total_enrolled: number;
  students: StudentInfo[];
}

interface StudentsData {
  total_courses: number;
  total_unique_students: number;
  courses: CourseStudentsInfo[];
}

export default function StudentsPage() {
  const [studentsData, setStudentsData] = useState<StudentsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<StudentInfo | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTab, setSelectedTab] = useState<string>("");

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("No authentication token found");
          setLoading(false);
          return;
        }

        const response = await fetch("http://localhost:8000/api/v1/teachers/me/students", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch students");
        }

        const data = await response.json();
        setStudentsData(data);
        
        // Set first course as selected tab
        if (data.courses.length > 0) {
          setSelectedTab(data.courses[0].offering_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, []);

  const handleStudentClick = (student: StudentInfo) => {
    setSelectedStudent(student);
    setDialogOpen(true);
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status.toLowerCase()) {
      case "active":
        return "default";
      case "inactive":
      case "graduated":
        return "secondary";
      case "suspended":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getEnrollmentStatusBadge = (status: string): "default" | "secondary" | "outline" => {
    switch (status.toLowerCase()) {
      case "enrolled":
        return "default";
      case "completed":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getInitials = (name: string): string => {
    const parts = name.split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-6 w-96" />
        </div>
        <Skeleton className="h-96 w-full" />
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

  if (!studentsData || studentsData.courses.length === 0) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-2">My Students</h1>
          <p className="text-muted-foreground">View and manage students in your courses</p>
        </div>
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg">No courses or students assigned yet</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">My Students</h1>
        <p className="text-muted-foreground">
          View and manage students enrolled in your courses
        </p>
        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-muted-foreground" />
            <span className="text-sm">
              <strong>{studentsData.total_courses}</strong> Courses
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-muted-foreground" />
            <span className="text-sm">
              <strong>{studentsData.total_unique_students}</strong> Total Students
            </span>
          </div>
        </div>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="mb-6 flex-wrap h-auto">
          {studentsData.courses.map((course) => (
            <TabsTrigger key={course.offering_id} value={course.offering_id} className="flex-col items-start text-left p-3">
              <div className="font-semibold text-sm">{course.course_code}</div>
              <div className="text-xs text-muted-foreground">{course.total_enrolled} students</div>
            </TabsTrigger>
          ))}
        </TabsList>

        {studentsData.courses.map((course) => {
          const filteredStudents = course.students.filter(
            (student) =>
              student.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              student.student_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
              student.email?.toLowerCase().includes(searchQuery.toLowerCase())
          );

          return (
            <TabsContent key={course.offering_id} value={course.offering_id}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-start justify-between">
                    <div>
                      <div className="text-xl">{course.course_name}</div>
                      <div className="text-sm font-normal text-muted-foreground mt-1">
                        {course.section_code} • {course.semester} {course.academic_year}
                      </div>
                    </div>
                    <Badge variant="outline" className="text-sm">
                      <Users className="w-4 h-4 mr-1" />
                      {course.total_enrolled} enrolled
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    <div className="mt-4">
                      <Input
                        type="search"
                        placeholder="Search by name, student number, or email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="max-w-md"
                      />
                    </div>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {filteredStudents.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      {searchQuery
                        ? "No students found matching your search"
                        : "No students enrolled in this course yet"}
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Student</TableHead>
                          <TableHead>Student Number</TableHead>
                          <TableHead>Email</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>GPA</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredStudents.map((student) => (
                          <TableRow
                            key={student.student_id}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => handleStudentClick(student)}
                          >
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <Avatar>
                                  <AvatarFallback className="bg-primary/10 text-primary">
                                    {getInitials(student.full_name)}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <div className="font-medium">{student.full_name}</div>
                                  <div className="text-xs text-muted-foreground">
                                    {student.study_mode || "N/A"}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="font-mono text-sm">
                              {student.student_number}
                            </TableCell>
                            <TableCell className="text-sm">{student.email || "N/A"}</TableCell>
                            <TableCell>
                              <Badge variant={getEnrollmentStatusBadge(student.enrollment_status)}>
                                {student.enrollment_status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {student.gpa !== null ? (
                                <div className="flex items-center gap-1">
                                  <Award className="w-4 h-4 text-muted-foreground" />
                                  <span className="font-medium">{student.gpa.toFixed(2)}</span>
                                </div>
                              ) : (
                                <span className="text-muted-foreground">N/A</span>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <button
                                className="text-sm text-primary hover:underline"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStudentClick(student);
                                }}
                              >
                                View Details
                              </button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          );
        })}
      </Tabs>

      {/* Student Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <Avatar className="w-12 h-12">
                <AvatarFallback className="bg-primary/10 text-primary text-lg">
                  {selectedStudent && getInitials(selectedStudent.full_name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <div>{selectedStudent?.full_name}</div>
                <div className="text-sm font-normal text-muted-foreground">
                  {selectedStudent?.student_number}
                </div>
              </div>
            </DialogTitle>
            <DialogDescription>
              Detailed information about this student
            </DialogDescription>
          </DialogHeader>

          {selectedStudent && (
            <div className="space-y-6 mt-4">
              {/* Contact Information */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Contact Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Mail className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Email</p>
                      <p className="text-sm">{selectedStudent.email || "Not provided"}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Student Status</p>
                      <Badge variant={getStatusBadgeVariant(selectedStudent.status)}>
                        {selectedStudent.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Academic Information */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Academic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Enrollment Date</p>
                      <p className="text-sm">
                        {selectedStudent.enrollment_date
                          ? new Date(selectedStudent.enrollment_date).toLocaleDateString()
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Award className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Overall GPA</p>
                      <p className="text-sm font-semibold">
                        {selectedStudent.gpa !== null ? selectedStudent.gpa.toFixed(2) : "N/A"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Study Mode</p>
                      <p className="text-sm capitalize">{selectedStudent.study_mode || "N/A"}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Enrollment Status</p>
                      <Badge variant={getEnrollmentStatusBadge(selectedStudent.enrollment_status)}>
                        {selectedStudent.enrollment_status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Course Performance */}
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-3">Course Performance</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Grade</p>
                    <p className="text-lg font-semibold">
                      {selectedStudent.grade || "Not graded yet"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Grade Points</p>
                    <p className="text-lg font-semibold">
                      {selectedStudent.grade_points !== null
                        ? selectedStudent.grade_points.toFixed(2)
                        : "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Attendance</p>
                    <p className="text-lg font-semibold">
                      {selectedStudent.attendance_percentage !== null
                        ? `${selectedStudent.attendance_percentage.toFixed(1)}%`
                        : "N/A"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
