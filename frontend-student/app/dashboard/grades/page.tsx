"use client";

import { useState, useEffect } from "react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  SortingState,
  ColumnFiltersState,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown, MoreHorizontal, Award, TrendingUp, BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Types matching backend API
interface AssessmentGrade {
  assessment_id: string;
  assessment_title: string;
  assessment_type: string;
  course_code: string;
  course_name: string;
  total_marks: number;
  marks_obtained: number | null;
  percentage: number | null;
  letter_grade: string | null;
  weight_percentage: number | null;
  feedback: string | null;
  graded_at: string | null;
  graded_by_name: string | null;
  is_final: boolean;
}

interface CourseGradeSummary {
  course_code: string;
  course_name: string;
  credit_hours: number;
  total_assessments: number;
  graded_assessments: number;
  average_percentage: number | null;
  final_grade: string | null;
  grade_points: number | null;
}

interface GradesData {
  student_id: string;
  student_number: string;
  full_name: string;
  current_gpa: number | null;
  total_credits_earned: number;
  course_summaries: CourseGradeSummary[];
  detailed_grades: AssessmentGrade[];
}

export default function GradesPage() {
  const [gradesData, setGradesData] = useState<GradesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [selectedGrade, setSelectedGrade] = useState<AssessmentGrade | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchGradesData();
  }, []);

  const fetchGradesData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("No authentication token found. Please log in.");
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:8000/api/v1/students/me/grades", {
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
            window.location.href = "/";
          }, 1500);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Grades data received:", data);
      setGradesData(data);
    } catch (err) {
      console.error("Error fetching grades:", err);
      setError(err instanceof Error ? err.message : "Failed to load grades");
    } finally {
      setLoading(false);
    }
  };

  // Define columns for the detailed grades table
  const columns: ColumnDef<AssessmentGrade>[] = [
    {
      accessorKey: "course_code",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Course
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      cell: ({ row }) => {
        const grade = row.original;
        return (
          <div>
            <div className="font-medium">{grade.course_name}</div>
            <div className="text-xs text-muted-foreground">{grade.course_code}</div>
          </div>
        );
      },
    },
    {
      accessorKey: "assessment_title",
      header: "Assessment",
      cell: ({ row }) => {
        const grade = row.original;
        return (
          <div>
            <div className="font-medium">{grade.assessment_title}</div>
            <div className="text-sm text-muted-foreground">
              {grade.assessment_type}
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: "marks_obtained",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Score
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      cell: ({ row }) => {
        const grade = row.original;
        const marksObtained = grade.marks_obtained;
        const totalMarks = grade.total_marks;

        if (marksObtained === null) {
          return <span className="text-muted-foreground">Not graded</span>;
        }

        return (
          <div>
            <span className="font-medium">
              {marksObtained.toFixed(1)} / {totalMarks.toFixed(0)}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: "percentage",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Percentage
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      cell: ({ row }) => {
        const percentage = row.getValue("percentage") as number | null;
        if (percentage === null) return "-";

        const getPercentageColor = (pct: number) => {
          if (pct >= 90) return "text-green-600 dark:text-green-400";
          if (pct >= 80) return "text-blue-600 dark:text-blue-400";
          if (pct >= 70) return "text-yellow-600 dark:text-yellow-400";
          if (pct >= 60) return "text-orange-600 dark:text-orange-400";
          return "text-red-600 dark:text-red-400";
        };

        return (
          <span className={`font-medium ${getPercentageColor(percentage)}`}>
            {percentage.toFixed(1)}%
          </span>
        );
      },
    },
    {
      accessorKey: "letter_grade",
      header: "Grade",
      cell: ({ row }) => {
        const letterGrade = row.getValue("letter_grade") as string | null;
        if (!letterGrade) return "-";

        const getGradeBadgeVariant = (grade: string) => {
          if (["A", "A+", "A-"].includes(grade)) return "default";
          if (["B", "B+", "B-"].includes(grade)) return "secondary";
          if (["C", "C+", "C-"].includes(grade)) return "outline";
          return "destructive";
        };

        return (
          <Badge variant={getGradeBadgeVariant(letterGrade)}>
            {letterGrade}
          </Badge>
        );
      },
    },
    {
      accessorKey: "graded_at",
      header: "Graded Date",
      cell: ({ row }) => {
        const gradedAt = row.getValue("graded_at") as string | null;
        if (!gradedAt) return "-";

        const date = new Date(gradedAt);
        return (
          <span className="text-sm">
            {date.toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        );
      },
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const grade = row.original;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGrade(grade);
                  setDialogOpen(true);
                }}
              >
                View Details
              </DropdownMenuItem>
              {grade.feedback && (
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGrade(grade);
                    setDialogOpen(true);
                  }}
                >
                  View Feedback
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  console.log("Grade details:", grade);
                }}
              >
                Copy Grade ID
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data: gradesData?.detailed_grades || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading grades...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Grades</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => fetchGradesData()} className="w-full">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!gradesData) {
    return null;
  }

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Grades</h1>
        <p className="text-muted-foreground">
          View all your grades and academic performance
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current GPA</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {gradesData.current_gpa ? gradesData.current_gpa.toFixed(2) : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              Out of 4.00 scale
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Credits Earned</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {gradesData.total_credits_earned}
            </div>
            <p className="text-xs text-muted-foreground">
              Total credit hours completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assessments</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {gradesData.detailed_grades.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Graded assignments and exams
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Course Summaries */}
      <Card>
        <CardHeader>
          <CardTitle>Course Performance</CardTitle>
          <CardDescription>
            Summary of your grades by course
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {gradesData.course_summaries.map((course) => (
              <div
                key={course.course_code}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-base">{course.course_name}</span>
                    <Badge variant="outline">{course.credit_hours} credits</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {course.course_code}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {course.graded_assessments} of {course.total_assessments} assessments graded
                  </p>
                </div>
                <div className="text-right space-y-1">
                  {course.final_grade && (
                    <Badge variant="default" className="text-lg px-3 py-1">
                      {course.final_grade}
                    </Badge>
                  )}
                  {course.average_percentage !== null && (
                    <p className="text-sm text-muted-foreground">
                      Avg: {course.average_percentage.toFixed(1)}%
                    </p>
                  )}
                  {course.grade_points !== null && (
                    <p className="text-xs text-muted-foreground">
                      {course.grade_points.toFixed(2)} pts
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Grades Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Grades</CardTitle>
          <CardDescription>
            Detailed breakdown of all your assessment grades
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Filter Input */}
            <div className="flex items-center gap-2">
              <Input
                placeholder="Filter by course code..."
                value={(table.getColumn("course_code")?.getFilterValue() as string) ?? ""}
                onChange={(event) =>
                  table.getColumn("course_code")?.setFilterValue(event.target.value)
                }
                className="max-w-sm"
              />
              <Input
                placeholder="Filter by assessment..."
                value={(table.getColumn("assessment_title")?.getFilterValue() as string) ?? ""}
                onChange={(event) =>
                  table.getColumn("assessment_title")?.setFilterValue(event.target.value)
                }
                className="max-w-sm"
              />
            </div>

            {/* Table */}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => {
                        return (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => (
                      <TableRow
                        key={row.id}
                        data-state={row.getIsSelected() && "selected"}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={columns.length}
                        className="h-24 text-center"
                      >
                        No grades found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {table.getState().pagination.pageIndex * 10 + 1} to{" "}
                {Math.min(
                  (table.getState().pagination.pageIndex + 1) * 10,
                  table.getFilteredRowModel().rows.length
                )}{" "}
                of {table.getFilteredRowModel().rows.length} grades
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Grade Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Badge variant="default">{selectedGrade?.course_code}</Badge>
              {selectedGrade?.assessment_title}
            </DialogTitle>
            <DialogDescription>
              {selectedGrade?.course_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Assessment Type</p>
                <p className="text-lg font-medium">{selectedGrade?.assessment_type}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Weight</p>
                <p className="text-lg font-medium">
                  {selectedGrade?.weight_percentage
                    ? `${selectedGrade.weight_percentage}%`
                    : "N/A"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Score</p>
                <p className="text-2xl font-bold">
                  {selectedGrade?.marks_obtained !== null
                    ? `${selectedGrade?.marks_obtained?.toFixed(1)} / ${selectedGrade?.total_marks?.toFixed(0)}`
                    : "Not graded"}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Grade</p>
                {selectedGrade?.letter_grade && (
                  <Badge variant="default" className="text-xl px-4 py-2">
                    {selectedGrade?.letter_grade}
                  </Badge>
                )}
                {selectedGrade?.percentage !== null && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedGrade?.percentage?.toFixed(1)}%
                  </p>
                )}
              </div>
            </div>

            {selectedGrade?.graded_by_name && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Graded By</p>
                <p className="text-lg">{selectedGrade.graded_by_name}</p>
              </div>
            )}

            {selectedGrade?.graded_at && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Graded Date</p>
                <p className="text-lg">
                  {new Date(selectedGrade.graded_at).toLocaleString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            )}

            {selectedGrade?.feedback && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Feedback</p>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{selectedGrade.feedback}</p>
                </div>
              </div>
            )}

            {selectedGrade?.is_final && (
              <Badge variant="secondary">Final Grade</Badge>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
