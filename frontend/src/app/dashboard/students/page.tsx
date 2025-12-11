'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Search, Users, GraduationCap, TrendingUp, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api';

import { Student, StudentsListResponse, StudentStatsResponse } from '@/types/students';

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [stats, setStats] = useState<StudentStatsResponse | null>(null);

  // Fetch students from API
  const fetchStudents = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '25',
      });

      if (searchTerm) params.append('search', searchTerm);

      const response = await api.get<StudentsListResponse>(`/students/?${params}`);
      const data = response.data;
      
      setStudents(data.results);
      setCurrentPage(data.current_page);
      setTotalPages(data.total_pages);
      setTotalCount(data.count);

    } catch (error) {
      console.error('Error fetching students:', error);
      toast.error('Failed to fetch students. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await api.get<StudentStatsResponse>('/students/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching student stats:', error);
    }
  }, []);

  useEffect(() => {
    fetchStudents(1);
    fetchStats();
  }, [fetchStudents, fetchStats]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      fetchStudents(page);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: "default" | "secondary" | "destructive" | "outline", label: string }> = {
      active: { variant: "default", label: "Active" },
      inactive: { variant: "secondary", label: "Inactive" },
      graduated: { variant: "outline", label: "Graduated" },
      suspended: { variant: "destructive", label: "Suspended" },
      withdrawn: { variant: "secondary", label: "Withdrawn" },
    };
    
    const config = statusConfig[status] || { variant: "outline" as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handleViewStudent = (student: Student) => {
    setSelectedStudent(student);
    setIsViewDialogOpen(true);
  };

  return (
    <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN', 'SYSADMIN']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Students</h1>
          <p className="text-muted-foreground">Manage student information and academic records</p>
        </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Students</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_students.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Students</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_students.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Graduated</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.graduated_students.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average GPA</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.average_gpa?.toFixed(2) || 'N/A'}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Search Students</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name or student number..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Students List</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading students...</div>
            </div>
          ) : students.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">No students found.</div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student Number</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Program</TableHead>
                    <TableHead>Study Mode</TableHead>
                    <TableHead>GPA</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {students.map((student, index) => (
                    <TableRow key={`${student.id}-${index}`}>
                      <TableCell>
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {student.student_number}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">
                            {student.person ? 
                              `${student.person.first_name} ${student.person.last_name}` : 
                              'N/A'
                            }
                          </div>
                          {student.person?.middle_name && (
                            <div className="text-sm text-muted-foreground">
                              {student.person.middle_name}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {student.academic_program ? (
                          <div>
                            <div className="font-medium text-sm">
                              {student.academic_program.name.en || student.academic_program.code}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {student.academic_program.code}
                            </div>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="capitalize">
                          {student.study_mode?.replace('_', ' ') || 'N/A'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono">
                          {student.gpa !== null && student.gpa !== undefined ? 
                            student.gpa.toFixed(2) : 
                            'N/A'
                          }
                        </span>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(student.status)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewStudent(student)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4">
                  <div className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * 25) + 1} to{' '}
                    {Math.min(currentPage * 25, totalCount)} of{' '}
                    {totalCount} students
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <span className="text-sm">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* View Student Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Student Details</DialogTitle>
          </DialogHeader>
          {selectedStudent && (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold mb-2">Personal Information</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Student Number:</strong> {selectedStudent.student_number}
                    </div>
                    {selectedStudent.person && (
                      <>
                        <div>
                          <strong>First Name:</strong> {selectedStudent.person.first_name}
                        </div>
                        <div>
                          <strong>Last Name:</strong> {selectedStudent.person.last_name}
                        </div>
                        {selectedStudent.person.middle_name && (
                          <div>
                            <strong>Middle Name:</strong> {selectedStudent.person.middle_name}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Academic Information</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Status:</strong> {getStatusBadge(selectedStudent.status)}
                    </div>
                    {selectedStudent.academic_program && (
                      <div>
                        <strong>Program:</strong> {selectedStudent.academic_program.name.en || selectedStudent.academic_program.code}
                      </div>
                    )}
                    <div>
                      <strong>Study Mode:</strong>{' '}
                      <span className="capitalize">
                        {selectedStudent.study_mode?.replace('_', ' ') || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <strong>Funding Type:</strong>{' '}
                      <span className="capitalize">
                        {selectedStudent.funding_type?.replace('_', ' ') || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <strong>Enrollment Date:</strong>{' '}
                      {new Date(selectedStudent.enrollment_date).toLocaleDateString()}
                    </div>
                    {selectedStudent.expected_graduation_date && (
                      <div>
                        <strong>Expected Graduation:</strong>{' '}
                        {new Date(selectedStudent.expected_graduation_date).toLocaleDateString()}
                      </div>
                    )}
                    <div>
                      <strong>GPA:</strong>{' '}
                      {selectedStudent.gpa !== null && selectedStudent.gpa !== undefined ? 
                        selectedStudent.gpa.toFixed(2) : 
                        'N/A'
                      }
                    </div>
                    <div>
                      <strong>Credits Earned:</strong> {selectedStudent.total_credits_earned}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
    </ProtectedRoute>
  );
}
