'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Search, Users, Building, Eye, ChevronLeft, ChevronRight, UserCheck } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { api } from '@/lib/api';

import { Teacher, TeacherListResponse } from '@/types/teachers';

export default function TeachersPage() {
  const { language } = useLanguage();
  
  // Helper function to get localized name
  const getLocalizedName = (name: string | { az: string; en: string; ru: string } | null | undefined): string => {
    if (!name) return 'N/A';
    if (typeof name === 'string') return name;
    return name[language] || name.en || name.az || 'N/A';
  };
  
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);

  // Fetch teachers from API
  const fetchTeachers = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '10',
      });

      if (searchTerm) params.append('search', searchTerm);

      const response = await api.get<TeacherListResponse>(`/teachers/?${params}`);
      const data = response.data;
      
      setTeachers(data.results);
      setCurrentPage(data.current_page);
      setTotalPages(data.total_pages);
      setTotalCount(data.count);

    } catch (error) {
      console.error('Error fetching teachers:', error);
      toast.error('Failed to fetch teachers. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    fetchTeachers(1);
  }, [fetchTeachers]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      fetchTeachers(page);
    }
  };

  const getStatusBadge = (teacher: Teacher) => {
    if (!teacher.is_active) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    return <Badge variant="default">Active</Badge>;
  };

  const handleViewTeacher = (teacher: Teacher) => {
    setSelectedTeacher(teacher);
    setIsViewDialogOpen(true);
  };

  // Calculate statistics
  const activeTeachers = teachers.filter(t => t.is_active).length;
  const organizationsCount = new Set(
    teachers.filter(t => t.organization).map(t => t.organization!.id)
  ).size;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Teachers</h1>
        <p className="text-muted-foreground">Manage teacher information and assignments</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Teachers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Teachers</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeTeachers}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Organizations</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{organizationsCount}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Teachers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, employee number..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Teachers List</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading teachers...</div>
            </div>
          ) : teachers.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">No teachers found.</div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Employee Number</TableHead>
                    <TableHead>Position</TableHead>
                    <TableHead>Organization</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {teachers.map((teacher, index) => (
                    <TableRow key={`${teacher.id}-${index}`}>
                      <TableCell>
                        <div>
                          <div className="font-medium">
                            {teacher.person?.full_name || 'N/A'}
                          </div>
                          {teacher.person?.middle_name && (
                            <div className="text-sm text-muted-foreground">
                              {teacher.person.middle_name}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {teacher.employee_number}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{getLocalizedName(teacher.position_title)}</div>
                          {teacher.employment_type && (
                            <div className="text-sm text-muted-foreground capitalize">
                              {teacher.employment_type.replace('_', ' ')}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {getLocalizedName(teacher.organization?.name)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(teacher)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewTeacher(teacher)}
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
                    Showing {((currentPage - 1) * 10) + 1} to{' '}
                    {Math.min(currentPage * 10, totalCount)} of{' '}
                    {totalCount} teachers
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

      {/* View Teacher Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Teacher Details</DialogTitle>
          </DialogHeader>
          {selectedTeacher && (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold mb-2">Personal Information</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Full Name:</strong> {selectedTeacher.person?.full_name || 'N/A'}
                    </div>
                    <div>
                      <strong>First Name:</strong> {selectedTeacher.person?.first_name || 'N/A'}
                    </div>
                    <div>
                      <strong>Last Name:</strong> {selectedTeacher.person?.last_name || 'N/A'}
                    </div>
                    {selectedTeacher.person?.middle_name && (
                      <div>
                        <strong>Middle Name:</strong> {selectedTeacher.person.middle_name}
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Professional Information</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Employee Number:</strong> {selectedTeacher.employee_number}
                    </div>
                    <div>
                      <strong>Position:</strong> {getLocalizedName(selectedTeacher.position_title)}
                    </div>
                    <div>
                      <strong>Employment Type:</strong>{' '}
                      {selectedTeacher.employment_type ? 
                        selectedTeacher.employment_type.replace('_', ' ').toUpperCase() : 
                        'N/A'}
                    </div>
                    {selectedTeacher.academic_rank && (
                      <div>
                        <strong>Academic Rank:</strong> {getLocalizedName(selectedTeacher.academic_rank)}
                      </div>
                    )}
                    <div>
                      <strong>Organization:</strong> {getLocalizedName(selectedTeacher.organization?.name)}
                    </div>
                    {selectedTeacher.hire_date && (
                      <div>
                        <strong>Hire Date:</strong>{' '}
                        {new Date(selectedTeacher.hire_date).toLocaleDateString()}
                      </div>
                    )}
                    <div>
                      <strong>Status:</strong>{' '}
                      {selectedTeacher.is_active ? (
                        <Badge variant="default">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </div>
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
