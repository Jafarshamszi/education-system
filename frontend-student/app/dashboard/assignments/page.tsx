"use client";

import { useState, useEffect } from "react";
import { FileText, Upload, CheckCircle, Clock, AlertCircle, Calendar, Award, BookOpen, X } from "lucide-react";
import { format, formatDistanceToNow, isPast } from "date-fns";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AssignmentSubmission {
  submission_id: string | null;
  submitted_at: string | null;
  file_name: string | null;
  file_size: number | null;
  score: number | null;
  feedback: string | null;
  graded_at: string | null;
  graded_by_name: string | null;
}

interface Assignment {
  assignment_id: string;
  course_code: string;
  course_name: string;
  title: string;
  description: string;
  instructions: string | null;
  due_date: string;
  total_marks: number;
  weight_percentage: number | null;
  status: string;
  submission: AssignmentSubmission | null;
}

interface AssignmentsData {
  student_id: string;
  student_number: string;
  full_name: string;
  total_assignments: number;
  pending_count: number;
  submitted_count: number;
  graded_count: number;
  overdue_count: number;
  assignments: Assignment[];
}

export default function AssignmentsPage() {
  const [assignmentsData, setAssignmentsData] = useState<AssignmentsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [currentTab, setCurrentTab] = useState("all");

  useEffect(() => {
    fetchAssignmentsData();
  }, []);

  const fetchAssignmentsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("No authentication token found. Please log in.");
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:8000/api/v1/students/me/assignments", {
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
      console.log("Assignments data received:", data);
      setAssignmentsData(data);
    } catch (err) {
      console.error("Error fetching assignments:", err);
      setError(err instanceof Error ? err.message : "Failed to load assignments");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "text/plain",
        "image/jpeg",
        "image/png",
      ];
      
      if (!allowedTypes.includes(file.type)) {
        alert("Invalid file type. Allowed: PDF, Word, ZIP, TXT, JPG, PNG");
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        alert("File size must be less than 10MB");
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleSubmitAssignment = async () => {
    if (!selectedFile || !selectedAssignment) return;

    try {
      setUploading(true);
      const token = localStorage.getItem("access_token");

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        `http://localhost:8000/api/v1/students/me/assignments/${selectedAssignment.assignment_id}/submit`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Upload failed! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Upload result:", result);
      
      setUploadSuccess(true);
      setSelectedFile(null);
      
      setTimeout(() => {
        setUploadDialogOpen(false);
        setUploadSuccess(false);
        fetchAssignmentsData();
      }, 2000);
    } catch (err) {
      console.error("Error uploading file:", err);
      alert(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = (assignment: Assignment) => {
    switch (assignment.status) {
      case "graded":
        return <Badge className="bg-green-500 hover:bg-green-600"><CheckCircle className="w-3 h-3 mr-1" />Graded</Badge>;
      case "submitted":
        return <Badge className="bg-blue-500 hover:bg-blue-600"><Upload className="w-3 h-3 mr-1" />Submitted</Badge>;
      case "overdue":
        return <Badge className="bg-red-500 hover:bg-red-600"><AlertCircle className="w-3 h-3 mr-1" />Overdue</Badge>;
      case "pending":
        return <Badge className="bg-yellow-500 hover:bg-yellow-600"><Clock className="w-3 h-3 mr-1" />Pending</Badge>;
      default:
        return <Badge variant="outline">{assignment.status}</Badge>;
    }
  };

  const getDueDateText = (dueDate: string) => {
    const due = new Date(dueDate);
    
    if (isPast(due)) {
      return (
        <span className="text-red-500 font-semibold">
          Overdue by {formatDistanceToNow(due)}
        </span>
      );
    }
    
    return (
      <span className="text-muted-foreground">
        Due {formatDistanceToNow(due, { addSuffix: true })}
      </span>
    );
  };

  const filterAssignments = (assignments: Assignment[], filter: string) => {
    if (filter === "all") return assignments;
    return assignments.filter(a => a.status === filter);
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "N/A";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading assignments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-md border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={fetchAssignmentsData} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!assignmentsData) {
    return null;
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assignments</h1>
        <p className="text-muted-foreground mt-2">
          Track and submit your course assignments
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assignments</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignmentsData.total_assignments}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all courses
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignmentsData.pending_count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Need submission
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
            <Upload className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignmentsData.submitted_count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Awaiting grading
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Graded</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignmentsData.graded_count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assignmentsData.overdue_count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Missed deadline
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">All ({assignmentsData.total_assignments})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({assignmentsData.pending_count})</TabsTrigger>
          <TabsTrigger value="submitted">Submitted ({assignmentsData.submitted_count})</TabsTrigger>
          <TabsTrigger value="graded">Graded ({assignmentsData.graded_count})</TabsTrigger>
          <TabsTrigger value="overdue">Overdue ({assignmentsData.overdue_count})</TabsTrigger>
        </TabsList>

        {["all", "pending", "submitted", "graded", "overdue"].map((filter) => (
          <TabsContent key={filter} value={filter} className="space-y-4 mt-4">
            {filterAssignments(assignmentsData.assignments, filter).length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground text-center">
                    No {filter === "all" ? "" : filter} assignments found
                  </p>
                </CardContent>
              </Card>
            ) : (
              filterAssignments(assignmentsData.assignments, filter).map((assignment) => (
                <Card key={assignment.assignment_id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant="outline" className="font-mono text-xs">
                            {assignment.course_code}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {assignment.course_name}
                          </span>
                        </div>
                        <CardTitle className="text-xl">{assignment.title}</CardTitle>
                      </div>
                      {getStatusBadge(assignment)}
                    </div>
                    <CardDescription className="mt-2">
                      {assignment.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex flex-wrap gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">Due:</span>
                          <span>{format(new Date(assignment.due_date), "PPP")}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Award className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">Marks:</span>
                          <span>{assignment.total_marks}</span>
                          {assignment.weight_percentage && (
                            <span className="text-muted-foreground">
                              ({assignment.weight_percentage}% of grade)
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {getDueDateText(assignment.due_date)}
                      </div>

                      {assignment.submission && assignment.status === "graded" && (
                        <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold">Your Score</span>
                            <div className="flex items-center gap-2">
                              <span className="text-2xl font-bold">
                                {assignment.submission.score}
                              </span>
                              <span className="text-muted-foreground">
                                / {assignment.total_marks}
                              </span>
                              <Badge className="ml-2 bg-green-500">
                                {((assignment.submission.score! / assignment.total_marks) * 100).toFixed(1)}%
                              </Badge>
                            </div>
                          </div>
                          <Progress 
                            value={(assignment.submission.score! / assignment.total_marks) * 100} 
                            className="h-2"
                          />
                        </div>
                      )}

                      {assignment.submission && assignment.status === "submitted" && (
                        <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg space-y-2">
                          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
                            <CheckCircle className="h-4 w-4" />
                            <span className="font-semibold">Submitted</span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            File: {assignment.submission.file_name}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Submitted: {assignment.submission.submitted_at && format(new Date(assignment.submission.submitted_at), "PPP 'at' p")}
                          </p>
                        </div>
                      )}

                      <Separator />

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setSelectedAssignment(assignment);
                            setDialogOpen(true);
                          }}
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                        
                        {(assignment.status === "pending" || assignment.status === "overdue") && (
                          <Button
                            onClick={() => {
                              setSelectedAssignment(assignment);
                              setUploadDialogOpen(true);
                            }}
                            className={assignment.status === "overdue" ? "bg-red-500 hover:bg-red-600" : ""}
                          >
                            <Upload className="h-4 w-4 mr-2" />
                            Submit Assignment
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        ))}
      </Tabs>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedAssignment && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline" className="font-mono">
                    {selectedAssignment.course_code}
                  </Badge>
                  {getStatusBadge(selectedAssignment)}
                </div>
                <DialogTitle className="text-2xl">{selectedAssignment.title}</DialogTitle>
                <DialogDescription>
                  {selectedAssignment.course_name}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 mt-4">
                <div>
                  <h4 className="font-semibold mb-2">Description</h4>
                  <p className="text-sm text-muted-foreground">
                    {selectedAssignment.description}
                  </p>
                </div>

                {selectedAssignment.instructions && (
                  <div>
                    <h4 className="font-semibold mb-2">Instructions</h4>
                    <pre className="text-sm text-muted-foreground whitespace-pre-wrap bg-muted p-3 rounded-md">
                      {selectedAssignment.instructions}
                    </pre>
                  </div>
                )}

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Due Date</p>
                    <p className="text-base font-semibold">
                      {format(new Date(selectedAssignment.due_date), "PPP 'at' p")}
                    </p>
                    <p className="text-sm mt-1">{getDueDateText(selectedAssignment.due_date)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Total Marks</p>
                    <p className="text-base font-semibold">{selectedAssignment.total_marks}</p>
                    {selectedAssignment.weight_percentage && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {selectedAssignment.weight_percentage}% of final grade
                      </p>
                    )}
                  </div>
                </div>

                {selectedAssignment.submission && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-semibold mb-3">Submission Details</h4>
                      <div className="space-y-2 bg-muted/50 p-4 rounded-lg">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">File Name:</span>
                          <span className="text-sm font-medium">{selectedAssignment.submission.file_name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">File Size:</span>
                          <span className="text-sm font-medium">
                            {formatFileSize(selectedAssignment.submission.file_size)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Submitted At:</span>
                          <span className="text-sm font-medium">
                            {selectedAssignment.submission.submitted_at && 
                              format(new Date(selectedAssignment.submission.submitted_at), "PPP 'at' p")}
                          </span>
                        </div>
                      </div>
                    </div>

                    {selectedAssignment.submission.score !== null && (
                      <>
                        <Separator />
                        <div>
                          <h4 className="font-semibold mb-3">Grade & Feedback</h4>
                          <div className="space-y-3">
                            <div className="bg-muted/50 p-4 rounded-lg">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-semibold">Score</span>
                                <div className="flex items-center gap-2">
                                  <span className="text-2xl font-bold">
                                    {selectedAssignment.submission.score}
                                  </span>
                                  <span className="text-muted-foreground">
                                    / {selectedAssignment.total_marks}
                                  </span>
                                  <Badge className="ml-2 bg-green-500">
                                    {((selectedAssignment.submission.score / selectedAssignment.total_marks) * 100).toFixed(1)}%
                                  </Badge>
                                </div>
                              </div>
                              <Progress 
                                value={(selectedAssignment.submission.score / selectedAssignment.total_marks) * 100} 
                                className="h-2"
                              />
                            </div>

                            {selectedAssignment.submission.feedback && (
                              <div>
                                <p className="text-sm font-medium mb-2">Feedback from {selectedAssignment.submission.graded_by_name}</p>
                                <div className="bg-muted/50 p-3 rounded-lg">
                                  <p className="text-sm text-muted-foreground">
                                    {selectedAssignment.submission.feedback}
                                  </p>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                  Graded: {selectedAssignment.submission.graded_at && 
                                    format(new Date(selectedAssignment.submission.graded_at), "PPP 'at' p")}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>

              <DialogFooter className="mt-4">
                {(selectedAssignment.status === "pending" || selectedAssignment.status === "overdue") && (
                  <Button
                    onClick={() => {
                      setDialogOpen(false);
                      setUploadDialogOpen(true);
                    }}
                    className={selectedAssignment.status === "overdue" ? "bg-red-500 hover:bg-red-600" : ""}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Submit Assignment
                  </Button>
                )}
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          {selectedAssignment && (
            <>
              <DialogHeader>
                <DialogTitle>Submit Assignment</DialogTitle>
                <DialogDescription>
                  {selectedAssignment.title} - {selectedAssignment.course_name}
                </DialogDescription>
              </DialogHeader>

              {uploadSuccess ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Upload Successful!</h3>
                  <p className="text-sm text-muted-foreground text-center">
                    Your assignment has been submitted successfully.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 mt-4">
                  <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200 font-medium mb-2">
                      Submission Guidelines:
                    </p>
                    <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1 list-disc list-inside">
                      <li>Allowed formats: PDF, Word (.docx, .doc), ZIP, TXT, JPG, PNG</li>
                      <li>Maximum file size: 10 MB</li>
                      <li>Ensure your file is named appropriately</li>
                    </ul>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="file-upload">Choose File</Label>
                    <Input
                      id="file-upload"
                      type="file"
                      onChange={handleFileChange}
                      accept=".pdf,.doc,.docx,.zip,.txt,.jpg,.jpeg,.png"
                      disabled={uploading}
                    />
                    {selectedFile && (
                      <div className="flex items-center justify-between bg-muted p-3 rounded-lg mt-2">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">{selectedFile.name}</span>
                          <span className="text-xs text-muted-foreground">
                            ({formatFileSize(selectedFile.size)})
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedFile(null)}
                          disabled={uploading}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {selectedAssignment.status === "overdue" && (
                    <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 p-4 rounded-lg">
                      <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                        <AlertCircle className="h-4 w-4" />
                        <p className="text-sm font-semibold">
                          This assignment is overdue
                        </p>
                      </div>
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                        Submitting after the deadline may result in late penalties.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {!uploadSuccess && (
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setUploadDialogOpen(false);
                      setSelectedFile(null);
                    }}
                    disabled={uploading}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmitAssignment}
                    disabled={!selectedFile || uploading}
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Submit
                      </>
                    )}
                  </Button>
                </DialogFooter>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
