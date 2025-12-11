"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { 
  Calendar as CalendarIcon, 
  Save, 
  GraduationCap,
  FileText,
  Calculator,
  Award,
  AlertCircle,
  CheckCircle2
} from "lucide-react";

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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

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
  grade_value: number | null;
  notes: string | null;
}

interface GradeRecord {
  student_id: string;
  grade_value: number | null;
  notes: string;
}

const ASSESSMENT_TYPES = [
  { value: "exam", label: "Exam", icon: FileText },
  { value: "quiz", label: "Quiz", icon: Calculator },
  { value: "assignment", label: "Assignment", icon: FileText },
  { value: "project", label: "Project", icon: Award },
  { value: "presentation", label: "Presentation", icon: GraduationCap },
  { value: "participation", label: "Participation", icon: GraduationCap },
  { value: "lab", label: "Lab Work", icon: Calculator },
  { value: "other", label: "Other", icon: FileText },
];

// Grade options for 1-10 scale (whole numbers only)
const GRADE_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

export default function GradesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [assessmentType, setAssessmentType] = useState<string>("");
  const [assessmentTitle, setAssessmentTitle] = useState<string>("");
  const [totalMarks, setTotalMarks] = useState<string>("10");
  const [assessmentDate, setAssessmentDate] = useState<Date>(new Date());
  const [students, setStudents] = useState<Student[]>([]);
  const [gradeRecords, setGradeRecords] = useState<Map<string, GradeRecord>>(new Map());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [attendanceStatus, setAttendanceStatus] = useState<{
    has_attendance: boolean;
    student_attendance: { [key: string]: { status: string; student_number: string; full_name: string } };
  } | null>(null);
  const [attendanceChecked, setAttendanceChecked] = useState(false);

  // Fetch teacher's courses on mount
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          toast.error("Authentication required", {
            description: "Please log in again"
          });
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
          offering_id: course.offering_id,
          course_code: course.course_code,
          course_name: course.course_name,
          section_code: course.section_code,
          semester: course.semester,
          academic_year: course.academic_year,
        }));
        
        setCourses(coursesData);
      } catch (err) {
        toast.error("Failed to load courses", {
          description: err instanceof Error ? err.message : "An error occurred"
        });
      }
    };

    fetchCourses();
  }, []);

  // Check attendance status when course or date changes
  useEffect(() => {
    if (!selectedCourse || !assessmentDate) {
      setAttendanceChecked(false);
      setAttendanceStatus(null);
      return;
    }

    const checkAttendance = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const dateStr = format(assessmentDate, "yyyy-MM-dd");
        const response = await fetch(
          `http://localhost:8000/api/v1/teachers/me/attendance/check?course_offering_id=${selectedCourse}&attendance_date=${dateStr}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setAttendanceStatus(data);
          setAttendanceChecked(true);
        }
      } catch (err) {
        console.error("Error checking attendance:", err);
      }
    };

    checkAttendance();
  }, [selectedCourse, assessmentDate]);

  // Load saved grades from localStorage when course/date changes
  useEffect(() => {
    if (!selectedCourse || !assessmentDate) return;
    
    const storageKey = `grades_${selectedCourse}_${format(assessmentDate, "yyyy-MM-dd")}`;
    const savedGrades = localStorage.getItem(storageKey);
    
    if (savedGrades) {
      try {
        const parsed = JSON.parse(savedGrades);
        const newRecords = new Map<string, GradeRecord>();
        Object.entries(parsed).forEach(([key, value]) => {
          newRecords.set(key, value as GradeRecord);
        });
        setGradeRecords(newRecords);
      } catch (err) {
        console.error("Failed to load saved grades", err);
      }
    }
  }, [selectedCourse, assessmentDate]);

  // Save grades to localStorage whenever they change
  useEffect(() => {
    if (!selectedCourse || !assessmentDate || gradeRecords.size === 0) return;
    
    const storageKey = `grades_${selectedCourse}_${format(assessmentDate, "yyyy-MM-dd")}`;
    const gradesObj = Object.fromEntries(gradeRecords);
    localStorage.setItem(storageKey, JSON.stringify(gradesObj));
  }, [gradeRecords, selectedCourse, assessmentDate]);

  // Fetch students when course changes
  useEffect(() => {
    if (!selectedCourse) return;

    const fetchStudents = async () => {
      setLoading(true);
      
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          toast.error("Authentication required", {
            description: "Please log in again"
          });
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
        const course = data.courses.find((c: { offering_id: string; students?: Student[] }) => c.offering_id === selectedCourse);
        
        if (course && course.students) {
          setStudents(course.students);
        } else {
          setStudents([]);
        }
      } catch (err) {
        toast.error("Failed to load students", {
          description: err instanceof Error ? err.message : "An error occurred"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, [selectedCourse]);

  const updateGrade = (studentId: string, gradeValue: string) => {
    const newRecords = new Map(gradeRecords);
    const existing = newRecords.get(studentId) || { 
      student_id: studentId, 
      grade_value: null, 
      notes: "" 
    };
    
    const numericGrade = gradeValue === "" ? null : parseFloat(gradeValue);
    newRecords.set(studentId, { ...existing, grade_value: numericGrade });
    setGradeRecords(newRecords);
  };

  const updateNotes = (studentId: string, notes: string) => {
    const newRecords = new Map(gradeRecords);
    const existing = newRecords.get(studentId) || { 
      student_id: studentId, 
      grade_value: null, 
      notes: "" 
    };
    newRecords.set(studentId, { ...existing, notes });
    setGradeRecords(newRecords);
  };

  const handleGoToAttendance = () => {
    const dateStr = format(assessmentDate, "yyyy-MM-dd");
    router.push(`/dashboard/attendance?course=${selectedCourse}&date=${dateStr}`);
  };

  const handleSubmit = async () => {
    if (!selectedCourse || !assessmentType) {
      toast.error("Please fill in all required fields", {
        description: "Course and assessment type are required"
      });
      return;
    }

    if (gradeRecords.size === 0) {
      toast.error("Please enter at least one grade", {
        description: "You need to enter grades for at least one student"
      });
      return;
    }

    // Check if attendance has been submitted
    if (!attendanceStatus?.has_attendance) {
      toast.error("Attendance must be submitted first", {
        description: `You need to submit attendance for ${format(assessmentDate, "PPP")} before entering grades`,
        action: {
          label: "Go to Attendance",
          onClick: handleGoToAttendance
        },
        duration: 10000
      });
      return;
    }

    setSaving(true);

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        toast.error("Authentication required", {
          description: "Please log in again"
        });
        return;
      }

      const grades = Array.from(gradeRecords.values()).filter(
        record => record.grade_value !== null
      );

      const response = await fetch("http://localhost:8000/api/v1/teachers/me/grades", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          course_offering_id: selectedCourse,
          assessment_id: null,
          assessment_title: assessmentTitle,
          assessment_type: assessmentType,
          total_marks: parseFloat(totalMarks),
          assessment_date: format(assessmentDate, "yyyy-MM-dd"),
          grades: grades,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || "Failed to save grades";
        
        // Special handling for attendance-related errors
        if (errorMessage.toLowerCase().includes("attendance")) {
          toast.error("Attendance required", {
            description: errorMessage,
            action: {
              label: "Go to Attendance",
              onClick: handleGoToAttendance
            },
            duration: 10000
          });
        } else {
          toast.error("Failed to save grades", {
            description: errorMessage
          });
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      let successMessage = `Successfully saved grades for ${result.grades_saved} students`;
      if (result.skipped_students && result.skipped_students.length > 0) {
        successMessage = `Saved grades for ${result.grades_saved} students. Skipped ${result.skipped_students.length} students (absent/late)`;
      }
      
      toast.success("Grades saved successfully!", {
        description: successMessage,
        icon: <CheckCircle2 className="h-5 w-5" />
      });
      
      // Clear form and localStorage
      setGradeRecords(new Map());
      setAssessmentTitle("");
      setAssessmentType("");
      localStorage.removeItem(`grades_${selectedCourse}_${format(assessmentDate, "yyyy-MM-dd")}`);
    } catch (err) {
      // Error already handled above
      console.error(err);
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

  const getGradeColor = (grade: number | null, total: number): string => {
    if (grade === null) return "";
    const percentage = (grade / total) * 100;
    
    // For 1-10 scale: 9-10 = A (90%+), 8-8.9 = B (80%+), 7-7.9 = C (70%+), 6-6.9 = D (60%+), <6 = F
    if (percentage >= 90) return "text-green-600 font-semibold";
    if (percentage >= 80) return "text-blue-600 font-semibold";
    if (percentage >= 70) return "text-yellow-600 font-semibold";
    if (percentage >= 60) return "text-orange-600 font-semibold";
    return "text-red-600 font-semibold";
  };

  const selectedCourseData = courses.find(c => c.offering_id === selectedCourse);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Grade Students</h1>
        <p className="text-muted-foreground">
          Enter grades for exams, quizzes, assignments, projects, and other assessments
        </p>
      </div>

      {attendanceChecked && !attendanceStatus?.has_attendance && selectedCourse && (
        <Card className="mb-6 border-yellow-600 bg-yellow-50">
          <CardContent className="pt-6 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-700" />
            <p className="text-yellow-800 font-medium">
              Attendance has not been submitted for {format(assessmentDate, "PPP")}. 
              You must submit attendance before entering grades for this date.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 mb-6">
        {/* Course and Assessment Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Assessment Information</CardTitle>
            <CardDescription>
              Select course and enter assessment details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Course Selection */}
              <div className="space-y-2">
                <Label htmlFor="course">Course</Label>
                <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                  <SelectTrigger id="course">
                    <SelectValue placeholder="Select a course" />
                  </SelectTrigger>
                  <SelectContent>
                    {courses.map((course) => (
                      <SelectItem key={course.offering_id} value={course.offering_id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{course.course_code}</span>
                          <span className="text-xs text-muted-foreground">
                            {course.course_name} • {course.section_code}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Assessment Type */}
              <div className="space-y-2">
                <Label htmlFor="type">Assessment Type *</Label>
                <Select value={assessmentType} onValueChange={setAssessmentType}>
                  <SelectTrigger id="type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {ASSESSMENT_TYPES.map((type) => {
                      const Icon = type.icon;
                      return (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4" />
                            <span>{type.label}</span>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {/* Assessment Title */}
              <div className="space-y-2 md:col-span-1">
                <Label htmlFor="title">Assessment Title</Label>
                <Input
                  id="title"
                  placeholder="e.g., Midterm Exam 1 (optional)"
                  value={assessmentTitle}
                  onChange={(e) => setAssessmentTitle(e.target.value)}
                />
              </div>

              {/* Total Marks */}
              <div className="space-y-2">
                <Label htmlFor="total">Total Marks (out of 10) *</Label>
                <Input
                  id="total"
                  type="number"
                  min="1"
                  max="10"
                  step="0.5"
                  value={totalMarks}
                  onChange={(e) => setTotalMarks(e.target.value)}
                  placeholder="10"
                />
              </div>

              {/* Date */}
              <div className="space-y-2">
                <Label>Assessment Date *</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !assessmentDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {assessmentDate ? (
                        format(assessmentDate, "PPP")
                      ) : (
                        <span>Pick a date</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={assessmentDate}
                      onSelect={(date) => date && setAssessmentDate(date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Students and Grades */}
        {selectedCourse && selectedCourseData && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Student Grades</CardTitle>
                  <CardDescription>
                    Enter grades for {students.length} students
                    {assessmentType && ` • ${ASSESSMENT_TYPES.find(t => t.value === assessmentType)?.label}`}
                    {assessmentTitle && ` • ${assessmentTitle}`}
                  </CardDescription>
                </div>
                <Badge variant="secondary" className="text-base">
                  {gradeRecords.size} / {students.length} graded
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : students.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No students found for this course
                </div>
              ) : (
                <>
                  {/* Bulk Grade Assignment */}
                  <div className="mb-6 p-4 border rounded-lg bg-muted/50">
                    <div className="flex items-center gap-4">
                      <Label className="text-sm font-medium">Set Grade for All Students:</Label>
                      <Select
                        onValueChange={(value) => {
                          // Set the same grade for all students who are not absent/late
                          const newRecords = new Map(gradeRecords);
                          students.forEach((student) => {
                            const studentAttendance = attendanceStatus?.student_attendance[student.student_id];
                            const isAbsentOrLate = studentAttendance && ['absent', 'late'].includes(studentAttendance.status);
                            
                            if (!isAbsentOrLate) {
                              const existing = newRecords.get(student.student_id) || {
                                student_id: student.student_id,
                                grade_value: null,
                                notes: ""
                              };
                              newRecords.set(student.student_id, {
                                ...existing,
                                grade_value: parseFloat(value)
                              });
                            }
                          });
                          setGradeRecords(newRecords);
                          toast.success("Grade applied to all students", {
                            description: `Set grade ${value}/10 for all present students`
                          });
                        }}
                      >
                        <SelectTrigger className="w-[180px]">
                          <SelectValue placeholder="Select grade" />
                        </SelectTrigger>
                        <SelectContent>
                          {GRADE_OPTIONS.map((grade) => (
                            <SelectItem key={grade} value={grade}>
                              {grade} / 10
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <span className="text-xs text-muted-foreground">
                        (You can adjust individual grades below)
                      </span>
                    </div>
                  </div>

                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Student</TableHead>
                        <TableHead>Student Number</TableHead>
                        <TableHead>Attendance</TableHead>
                        <TableHead className="w-[150px]">Grade (/{totalMarks})</TableHead>
                        <TableHead>Notes</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {students.map((student) => {
                        const record = gradeRecords.get(student.student_id);
                        const gradeValue = record?.grade_value;
                        const studentAttendance = attendanceStatus?.student_attendance[student.student_id];
                        const isAbsentOrLate = studentAttendance && ['absent', 'late'].includes(studentAttendance.status);
                        
                        return (
                          <TableRow key={student.student_id} className={isAbsentOrLate ? "bg-muted/50" : ""}>
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
                              {studentAttendance ? (
                                <Badge 
                                  variant={
                                    studentAttendance.status === 'present' ? 'default' :
                                    studentAttendance.status === 'late' ? 'secondary' :
                                    'destructive'
                                  }
                                  className="capitalize"
                                >
                                  {studentAttendance.status}
                                </Badge>
                              ) : (
                                <span className="text-xs text-muted-foreground">No record</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <Select
                                  disabled={isAbsentOrLate}
                                  value={gradeValue?.toString() || ""}
                                  onValueChange={(value) => updateGrade(student.student_id, value)}
                                >
                                  <SelectTrigger 
                                    className={cn(
                                      "w-full",
                                      gradeValue !== null && gradeValue !== undefined && getGradeColor(gradeValue, parseFloat(totalMarks))
                                    )}
                                  >
                                    <SelectValue placeholder={isAbsentOrLate ? "Cannot grade" : "Select grade"} />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {GRADE_OPTIONS.map((grade) => (
                                      <SelectItem key={grade} value={grade}>
                                        {grade} / 10
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                                {isAbsentOrLate && (
                                  <p className="text-xs text-muted-foreground italic">
                                    {studentAttendance?.status === 'absent' ? 'Student was absent' : 'Student was late'}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Textarea
                                placeholder={isAbsentOrLate ? "Cannot grade" : "Add feedback..."}
                                value={record?.notes || ""}
                                onChange={(e) => updateNotes(student.student_id, e.target.value)}
                                disabled={isAbsentOrLate}
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
                        setGradeRecords(new Map());
                        const storageKey = `grades_${selectedCourse}_${format(assessmentDate, "yyyy-MM-dd")}`;
                        localStorage.removeItem(storageKey);
                        toast.success("Cleared all grades");
                      }}
                    >
                      Clear All
                    </Button>
                    <Button
                      onClick={handleSubmit}
                      disabled={
                        saving || 
                        students.length === 0 || 
                        gradeRecords.size === 0
                      }
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {saving ? "Saving..." : "Save Grades"}
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
