"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { format } from "date-fns";
import { Calendar as CalendarIcon, Users, Save, CheckCircle2, XCircle, Clock, AlertCircle, ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

// Removed unused Schedule interface - keeping for reference if needed
// interface Schedule {
//   schedule_id: string;
//   offering_id: string;
//   course_code: string;
//   course_name: string;
//   section_code: string;
//   semester: string;
//   academic_year: string;
//   day_of_week: number;
//   start_time: string;
//   end_time: string;
//   schedule_type: string;
// }

interface Course {
  offering_id: string;
  course_code: string;
  course_name: string;
  section_code: string;
  semester: string;
  academic_year: string;
}

interface Student {
  student_id: string;
  student_number: string;
  full_name: string;
  email: string | null;
  attendance_id?: string | null;
  status?: string | null;
  notes?: string | null;
}

interface AttendanceRecord {
  student_id: string;
  status: string;
  notes?: string;
}

function AttendancePageContent() {
  const searchParams = useSearchParams();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [students, setStudents] = useState<Student[]>([]);
  const [attendanceRecords, setAttendanceRecords] = useState<Map<string, AttendanceRecord>>(new Map());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load URL parameters on mount (from grades page navigation)
  useEffect(() => {
    const courseParam = searchParams.get('course');
    const dateParam = searchParams.get('date');
    
    if (courseParam) {
      setSelectedCourse(courseParam);
    }
    if (dateParam) {
      try {
        setSelectedDate(new Date(dateParam));
      } catch (err) {
        console.error("Invalid date parameter", err);
      }
    }
  }, [searchParams]);

  // Load saved attendance from localStorage when course/date changes
  useEffect(() => {
    if (!selectedCourse || !selectedDate) return;
    
    const storageKey = `attendance_${selectedCourse}_${format(selectedDate, "yyyy-MM-dd")}`;
    const savedAttendance = localStorage.getItem(storageKey);
    
    if (savedAttendance) {
      try {
        const parsed = JSON.parse(savedAttendance);
        const newRecords = new Map<string, AttendanceRecord>();
        Object.entries(parsed).forEach(([key, value]) => {
          newRecords.set(key, value as AttendanceRecord);
        });
        setAttendanceRecords(newRecords);
      } catch (err) {
        console.error("Failed to load saved attendance", err);
      }
    }
  }, [selectedCourse, selectedDate]);

  // Save attendance to localStorage whenever it changes
  useEffect(() => {
    if (!selectedCourse || !selectedDate || attendanceRecords.size === 0) return;
    
    const storageKey = `attendance_${selectedCourse}_${format(selectedDate, "yyyy-MM-dd")}`;
    const attendanceObj = Object.fromEntries(attendanceRecords);
    localStorage.setItem(storageKey, JSON.stringify(attendanceObj));
  }, [attendanceRecords, selectedCourse, selectedDate]);

  // Fetch teacher's courses on mount
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("No authentication token found");
          return;
        }

        const response = await fetch("http://localhost:8000/api/v1/teachers/me/students", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch courses");
        }

        const data = await response.json();
        const coursesData = data.courses.map((course: { offering_id: string; course_code: string; course_name: string; section_code: string; semester: string; academic_year: string }) => ({
          offering_id: course.offering_id,  // Keep as string
          course_code: course.course_code,
          course_name: course.course_name,
          section_code: course.section_code,
          semester: course.semester,
          academic_year: course.academic_year,
        }));
        
        setCourses(coursesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    };

    fetchCourses();
  }, []);

  // Fetch students when course or date changes
  useEffect(() => {
    if (!selectedCourse || !selectedDate) return;

    const fetchStudents = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("No authentication token found");
          return;
        }

        // Get students for this course
        const response = await fetch("http://localhost:8000/api/v1/teachers/me/students", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch students");
        }

        const data = await response.json();
        console.log("📊 API Response:", data);
        console.log("📚 Courses:", data.courses);
        console.log("🔍 Selected Course ID:", selectedCourse);
        console.log("🔍 Selected Course ID Type:", typeof selectedCourse);
        
        // offering_id is a string in the backend response
        const course = data.courses.find((c: { offering_id: string; students?: Student[] }) => c.offering_id === selectedCourse);
        console.log("✅ Found Course:", course);
        console.log("👥 Students in course:", course?.students);
        
        if (course && course.students) {
          // Initialize attendance records - only if student has existing status
          const newRecords = new Map<string, AttendanceRecord>();
          course.students.forEach((student: Student) => {
            // Only add to map if student has existing attendance data
            if (student.status) {
              newRecords.set(student.student_id, {
                student_id: student.student_id,
                status: student.status,
                notes: student.notes || "",
              });
            }
          });
          
          setStudents(course.students);
          setAttendanceRecords(newRecords);
        } else {
          setStudents([]);
          setAttendanceRecords(new Map());
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, [selectedCourse, selectedDate]);

  const updateAttendanceStatus = (studentId: string, status: string) => {
    const newRecords = new Map(attendanceRecords);
    const existing = newRecords.get(studentId) || { student_id: studentId, status: "", notes: "" };
    newRecords.set(studentId, { ...existing, status });
    setAttendanceRecords(newRecords);
  };

  const updateAttendanceNotes = (studentId: string, notes: string) => {
    const newRecords = new Map(attendanceRecords);
    const existing = newRecords.get(studentId) || { student_id: studentId, status: "", notes: "" };
    newRecords.set(studentId, { ...existing, notes });
    setAttendanceRecords(newRecords);
  };

  const markAllStudents = (status: string) => {
    const newRecords = new Map<string, AttendanceRecord>();
    students.forEach((student) => {
      const existing = attendanceRecords.get(student.student_id);
      newRecords.set(student.student_id, {
        student_id: student.student_id,
        status: status,
        notes: existing?.notes || "",
      });
    });
    setAttendanceRecords(newRecords);
    setSuccess(`Marked all ${students.length} students as ${status}`);
    setTimeout(() => setSuccess(null), 3000);
  };

  const handleSubmit = async () => {
    if (!selectedCourse || attendanceRecords.size === 0) {
      setError("Please select a course and mark attendance");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setError("No authentication token found");
        return;
      }

      const records = Array.from(attendanceRecords.values());
      
      const response = await fetch("http://localhost:8000/api/v1/teachers/me/attendance", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          course_offering_id: selectedCourse,
          attendance_date: format(selectedDate, "yyyy-MM-dd"),
          records,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save attendance");
      }

      setSuccess(`Attendance saved for ${records.length} students`);
      
      // Clear localStorage after successful save
      const storageKey = `attendance_${selectedCourse}_${format(selectedDate, "yyyy-MM-dd")}`;
      localStorage.removeItem(storageKey);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save attendance");
    } finally {
      setSaving(false);
    }
  };

  const getInitials = (name: string): string => {
    const parts = name.split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "present":
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case "absent":
        return <XCircle className="w-5 h-5 text-red-600" />;
      case "late":
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case "excused":
        return <AlertCircle className="w-5 h-5 text-blue-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "present":
        return "bg-green-50 border-green-200";
      case "absent":
        return "bg-red-50 border-red-200";
      case "late":
        return "bg-yellow-50 border-yellow-200";
      case "excused":
        return "bg-blue-50 border-blue-200";
      default:
        return "";
    }
  };

  const selectedCourseData = courses.find(c => c.offering_id === selectedCourse);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Mark Attendance</h1>
        <p className="text-muted-foreground">
          Select a course and date to mark student attendance
        </p>
      </div>

      {error && (
        <Card className="mb-6 border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="mb-6 border-green-600 bg-green-50">
          <CardContent className="pt-6">
            <p className="text-green-700 font-medium">{success}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2 mb-6">
        {/* Course Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Course</CardTitle>
            <CardDescription>Choose the course for attendance</CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={selectedCourse} onValueChange={setSelectedCourse}>
              <SelectTrigger>
                <SelectValue placeholder="Select a course" />
              </SelectTrigger>
              <SelectContent>
                {courses.map((course) => (
                  <SelectItem key={course.offering_id} value={course.offering_id}>
                    <div className="flex flex-col items-start">
                      <span className="font-medium">{course.course_code}</span>
                      <span className="text-sm text-muted-foreground">
                        {course.section_code} • {course.semester} {course.academic_year}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {selectedCourseData && (
              <div className="mt-4 p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">{selectedCourseData.course_name}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedCourseData.section_code} • {selectedCourseData.semester} {selectedCourseData.academic_year}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Date Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Date</CardTitle>
            <CardDescription>Choose the date for attendance</CardDescription>
          </CardHeader>
          <CardContent>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !selectedDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {selectedDate ? format(selectedDate, "PPP") : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={(date) => date && setSelectedDate(date)}
                  initialFocus
                />
              </PopoverContent>
            </Popover>

            {selectedDate && (
              <div className="mt-4 p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">Selected Date</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {format(selectedDate, "EEEE, MMMM d, yyyy")}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Students Table */}
      {selectedCourse && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                <span>Student Attendance</span>
              </div>
              <Badge variant="outline">
                {students.length} students
              </Badge>
            </CardTitle>
            <CardDescription className="flex items-center justify-between">
              <span>Mark attendance for each student below</span>
              {students.length > 0 && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Users className="w-4 h-4 mr-2" />
                      Mark All As...
                      <ChevronDown className="w-4 h-4 ml-2" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuLabel>Bulk Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => markAllStudents("present")}
                      className="cursor-pointer"
                    >
                      <CheckCircle2 className="w-4 h-4 mr-2 text-green-600" />
                      Mark All Present
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => markAllStudents("absent")}
                      className="cursor-pointer"
                    >
                      <XCircle className="w-4 h-4 mr-2 text-red-600" />
                      Mark All Absent
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => markAllStudents("late")}
                      className="cursor-pointer"
                    >
                      <Clock className="w-4 h-4 mr-2 text-yellow-600" />
                      Mark All Late
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => markAllStudents("excused")}
                      className="cursor-pointer"
                    >
                      <AlertCircle className="w-4 h-4 mr-2 text-blue-600" />
                      Mark All Excused
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : students.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No students enrolled in this course
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student</TableHead>
                      <TableHead>Student Number</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {students.map((student) => {
                      const record = attendanceRecords.get(student.student_id);
                      const status = record?.status || "";  // Empty string = no selection
                      
                      return (
                        <TableRow 
                          key={student.student_id} 
                          className={getStatusColor(status)}
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
                                  {student.email || "No email"}
                                </div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {student.student_number}
                          </TableCell>
                          <TableCell>
                            <RadioGroup
                              key={`${student.student_id}-${status}`}
                              value={status}
                              onValueChange={(value) => updateAttendanceStatus(student.student_id, value)}
                              className="flex gap-4"
                            >
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="present" id={`${student.student_id}-present`} />
                                <Label htmlFor={`${student.student_id}-present`} className="flex items-center gap-1 cursor-pointer">
                                  {getStatusIcon("present")}
                                  <span className="text-sm">Present</span>
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="absent" id={`${student.student_id}-absent`} />
                                <Label htmlFor={`${student.student_id}-absent`} className="flex items-center gap-1 cursor-pointer">
                                  {getStatusIcon("absent")}
                                  <span className="text-sm">Absent</span>
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="late" id={`${student.student_id}-late`} />
                                <Label htmlFor={`${student.student_id}-late`} className="flex items-center gap-1 cursor-pointer">
                                  {getStatusIcon("late")}
                                  <span className="text-sm">Late</span>
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="excused" id={`${student.student_id}-excused`} />
                                <Label htmlFor={`${student.student_id}-excused`} className="flex items-center gap-1 cursor-pointer">
                                  {getStatusIcon("excused")}
                                  <span className="text-sm">Excused</span>
                                </Label>
                              </div>
                            </RadioGroup>
                          </TableCell>
                          <TableCell>
                            <Textarea
                              placeholder="Add notes..."
                              value={record?.notes || ""}
                              onChange={(e) => updateAttendanceNotes(student.student_id, e.target.value)}
                              className="min-h-[60px]"
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>

                <div className="mt-6 flex justify-end gap-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      // Clear all attendance records - reset to empty state
                      setAttendanceRecords(new Map());
                      setSuccess("Cleared all attendance records");
                      setTimeout(() => setSuccess(null), 3000);
                      setError(null);
                    }}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={saving || students.length === 0}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? "Saving..." : "Save Attendance"}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AttendancePage() {
  return (
    <Suspense fallback={
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading...</div>
            </div>
          </CardContent>
        </Card>
      </div>
    }>
      <AttendancePageContent />
    </Suspense>
  );
}
