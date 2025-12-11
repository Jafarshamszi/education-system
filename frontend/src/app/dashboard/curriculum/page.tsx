'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Search, 
  GraduationCap, 
  BookOpen, 
  Users, 
  Clock, 
  Building, 
  Eye,
  Award,
  BarChart3
} from 'lucide-react';
import { curriculumAPI } from '@/lib/api/curriculum';
import { 
  CurriculumStats,
  CurriculumOverview, 
  CurriculumDetail,
  SubjectInfo,
  CurriculumSubject
} from '@/types/curriculum';

export default function CurriculumPage() {
  // State management
  const [stats, setStats] = useState<CurriculumStats | null>(null);
  const [curricula, setCurricula] = useState<CurriculumOverview[]>([]);
  const [topSubjects, setTopSubjects] = useState<SubjectInfo[]>([]);
  const [selectedCurriculum, setSelectedCurriculum] = useState<CurriculumDetail | null>(null);
  const [curriculumSubjects, setCurriculumSubjects] = useState<CurriculumSubject[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const pageSize = 20;

  // Helper function to safely extract text from JSONB or string fields
  const getText = (value: string | Record<string, string> | null | undefined): string => {
    if (!value) return 'N/A';
    if (typeof value === 'string') return value;
    if (typeof value === 'object') {
      return value.en || value.az || value.ru || 'N/A';
    }
    return String(value);
  };

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load curricula when search term or page changes
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const offset = (currentPage - 1) * pageSize;
        const filters: { limit: number; offset: number; search?: string } = { 
          limit: pageSize, 
          offset 
        };
        
        // Add search filter if search term exists
        if (searchTerm.trim()) {
          filters.search = searchTerm.trim();
        }
        
        const data = await curriculumAPI.getCurricula(filters);
        setCurricula(data);
        setError(null);
      } catch (err) {
        setError('Failed to load curricula');
        console.error('Error loading curricula:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [currentPage, searchTerm]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [statsData, curriculaData, subjectsData] = await Promise.all([
        curriculumAPI.getStats(),
        curriculumAPI.getCurricula({ limit: pageSize }),
        curriculumAPI.getTopSubjects(10)
      ]);

      setStats(statsData);
      setCurricula(curriculaData);
      setTopSubjects(subjectsData);
      setError(null);
    } catch (err) {
      setError('Failed to load curriculum data');
      console.error('Error loading initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCurricula = async () => {
    setLoading(true);
    try {
      const offset = (currentPage - 1) * pageSize;
      const data = await curriculumAPI.getCurricula({ limit: pageSize, offset });
      setCurricula(data);
      setError(null);
    } catch (err) {
      setError('Failed to load curricula');
      console.error('Error loading curricula:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm) {
      // If search term is empty, reload all curricula
      setCurrentPage(1);
      return;
    }
    
    setCurrentPage(1); // Reset to first page for new search
  };

  const handleCurriculumDetail = async (curriculumId: string) => {
    try {
      const [detailData, subjectsData] = await Promise.all([
        curriculumAPI.getCurriculumDetail(curriculumId),
        curriculumAPI.getCurriculumSubjects(curriculumId)
      ]);

      setSelectedCurriculum(detailData);
      setCurriculumSubjects(subjectsData);
      setIsDetailModalOpen(true);
    } catch (err) {
      setError('Failed to load curriculum details');
      console.error('Error loading curriculum details:', err);
    }
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatNumber = (num: number | undefined) => {
    if (num === undefined || num === null) return '0';
    return new Intl.NumberFormat().format(num);
  };

  const handleModalClose = (open: boolean) => {
    setIsDetailModalOpen(open);
    if (!open) {
      // Clear selected curriculum data when closing
      setSelectedCurriculum(null);
      setCurriculumSubjects([]);
    }
  };

  if (loading && !curricula.length) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex justify-center items-center min-h-96">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-lg text-muted-foreground">Loading curriculum data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Curriculum Management System</h1>
        <p className="text-muted-foreground">
          Comprehensive curriculum analysis and management dashboard
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Curricula</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats.active_curricula)}</div>
              <p className="text-xs text-muted-foreground">Education programs</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unique Subjects</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats.unique_subjects)}</div>
              <p className="text-xs text-muted-foreground">Different subjects</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Courses</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats.active_courses)}</div>
              <p className="text-xs text-muted-foreground">Running courses</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Student Enrollments</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats.student_enrollments)}</div>
              <p className="text-xs text-muted-foreground">Total enrollments</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Teaching Hours</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats.total_teaching_hours)}</div>
              <p className="text-xs text-muted-foreground">Total hours</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="curricula" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="curricula">Curricula Overview</TabsTrigger>
          <TabsTrigger value="subjects">Top Subjects</TabsTrigger>
        </TabsList>

        {/* Curricula Tab */}
        <TabsContent value="curricula" className="space-y-4">
          {/* Search and Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Search Curricula</CardTitle>
              <CardDescription>Find and explore education programs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search curricula..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                <Button onClick={handleSearch} disabled={!searchTerm}>
                  Search
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setSearchTerm('');
                    setCurrentPage(1);
                    loadCurricula();
                  }}
                >
                  Clear
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Curricula List */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {curricula.map((curriculum) => (
              <Card key={curriculum.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg truncate" title={getText(curriculum.name)}>
                        {getText(curriculum.name)}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <span className="font-mono bg-muted px-1 rounded text-xs">{curriculum.code}</span>
                        {curriculum.organization_name && (
                          <>
                            <Building className="h-3 w-3 ml-2" />
                            {getText(curriculum.organization_name)}
                          </>
                        )}
                      </CardDescription>
                    </div>
                    <Badge variant={curriculum.is_active ? "default" : "secondary"}>
                      {curriculum.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium text-muted-foreground">Degree</div>
                      <div className="text-lg font-semibold capitalize">{curriculum.degree_type}</div>
                    </div>
                    <div>
                      <div className="font-medium text-muted-foreground">Credits</div>
                      <div className="text-lg font-semibold">{curriculum.total_credits}</div>
                    </div>
                    {curriculum.subjects_count !== undefined && (
                      <div>
                        <div className="font-medium text-muted-foreground">Subjects</div>
                        <div className="text-lg font-semibold">{curriculum.subjects_count}</div>
                      </div>
                    )}
                    {curriculum.courses_count !== undefined && (
                      <div>
                        <div className="font-medium text-muted-foreground">Courses</div>
                        <div className="text-lg font-semibold">{curriculum.courses_count}</div>
                      </div>
                    )}
                    {curriculum.students_enrolled !== undefined && (
                      <div>
                        <div className="font-medium text-muted-foreground">Students</div>
                        <div className="text-lg font-semibold">{formatNumber(curriculum.students_enrolled)}</div>
                      </div>
                    )}
                    {curriculum.create_date && (
                      <div>
                        <div className="font-medium text-muted-foreground">Created</div>
                        <div className="text-sm">{formatDate(curriculum.create_date)}</div>
                      </div>
                    )}
                  </div>
                  
                  <Button 
                    onClick={() => handleCurriculumDetail(curriculum.id)}
                    className="w-full"
                    size="sm"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {curricula.length === pageSize && (
            <div className="flex justify-center gap-2">
              <Button 
                variant="outline" 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setCurrentPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Top Subjects Tab */}
        <TabsContent value="subjects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Most Used Subjects in Curricula</CardTitle>
              <CardDescription>Subjects with highest usage across education programs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topSubjects.map((subject, index) => (
                  <div key={subject.code} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <Badge variant="secondary" className="text-lg font-bold w-10 h-10 flex items-center justify-center">
                        {index + 1}
                      </Badge>
                      <div>
                        <div className="font-semibold">{subject.code}</div>
                        <div className="text-sm text-muted-foreground">{subject.name_az}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{subject.used_in_curricula}</div>
                      <div className="text-sm text-muted-foreground">curricula</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Curriculum Detail Modal */}
      <Dialog open={isDetailModalOpen} onOpenChange={handleModalClose}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              {getText(selectedCurriculum?.name)}
            </DialogTitle>
            <DialogDescription>
              Detailed curriculum information and subject breakdown
            </DialogDescription>
          </DialogHeader>

          {selectedCurriculum && (
            <div className="space-y-6">
              {/* Curriculum Overview */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{selectedCurriculum.subjects_count}</div>
                    <div className="text-sm text-muted-foreground">Subjects</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{selectedCurriculum.courses_count}</div>
                    <div className="text-sm text-muted-foreground">Courses</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{formatNumber(selectedCurriculum.total_hours)}</div>
                    <div className="text-sm text-muted-foreground">Total Hours</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-sm font-medium">Created</div>
                    <div className="text-sm text-muted-foreground">{formatDate(selectedCurriculum.create_date)}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Name</div>
                      <div>{getText(selectedCurriculum.name)}</div>
                    </div>
                    {selectedCurriculum.code && (
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Code</div>
                        <div>{selectedCurriculum.code}</div>
                      </div>
                    )}
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Organization</div>
                      <div>{getText(selectedCurriculum.organization_name)}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Subjects Table */}
              {curriculumSubjects.length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Curriculum Subjects ({curriculumSubjects.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Subject Code</TableHead>
                          <TableHead>Subject Name</TableHead>
                          <TableHead>Created Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {curriculumSubjects.map((subject, index) => (
                          <TableRow key={`${subject.subject_code}-${getText(subject.subject_name)}-${index}`}>
                            <TableCell className="font-medium">{subject.subject_code}</TableCell>
                            <TableCell>{getText(subject.subject_name)}</TableCell>
                            <TableCell>
                              {subject.create_date ? formatDate(subject.create_date) : 'N/A'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle>Curriculum Subjects</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8">
                      <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-medium text-muted-foreground mb-2">No Subjects Found</h3>
                      <p className="text-sm text-muted-foreground">
                        This curriculum doesn&apos;t have any subjects assigned yet.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}