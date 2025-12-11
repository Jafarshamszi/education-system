"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Search, 
  BookOpen, 
  Clock, 
  Users, 
  GraduationCap, 
  Eye, 
  ChevronLeft, 
  ChevronRight
} from "lucide-react";
import { educationPlansApi, type EducationPlanApiDetail, type PlanSubject, type EducationPlanUpdate } from '@/lib/api/education-plans';
import { teachersApi, type TeacherStats } from '@/lib/api/teachers';
import { toast } from "sonner";

import type {
  EducationPlan,
  EducationPlanStats,
  EducationPlanOverallStats,
} from "@/types/education-plan";



export default function EducationPlanPage() {
  // State management
  const [educationPlans, setEducationPlans] = useState<EducationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<EducationPlan | null>(null);
  const [selectedPlanDetail, setSelectedPlanDetail] = useState<EducationPlanApiDetail | null>(null);
  const [subjects, setSubjects] = useState<PlanSubject[]>([]);
  const [planStats, setPlanStats] = useState<EducationPlanStats | null>(null);
  const [overallStats, setOverallStats] = useState<EducationPlanOverallStats | null>(null);
  const [teacherStats, setTeacherStats] = useState<TeacherStats | null>(null);
  
  // Filters and search
  const [selectedSemester, setSelectedSemester] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [subjectSearchTerm, setSubjectSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const itemsPerPage = 10;
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Dialog states
  const [selectedSubject, setSelectedSubject] = useState<PlanSubject | null>(null);
  const [isSubjectDialogOpen, setIsSubjectDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  
  // Edit form state
  const [editForm, setEditForm] = useState<EducationPlanUpdate>({});

  // Load education plans
  const loadEducationPlans = useCallback(async (page: number = 1) => {
    try {
      setIsLoading(true);

      const params = {
        limit: itemsPerPage,
        offset: (page - 1) * itemsPerPage,
        ...(searchTerm.trim() && { search: searchTerm.trim() }),
      };

      const plans = await educationPlansApi.getEducationPlans(params);

      // Ensure results is always an array
      setEducationPlans(Array.isArray(plans?.results) ? plans.results : []);

      // Use the backend pagination data
      setTotalCount(plans?.count || 0);
      setTotalPages(Math.ceil((plans?.count || 0) / itemsPerPage));
      setCurrentPage(page);

    } catch (error) {
      console.error("Error fetching education plans:", error);
      toast.error("Failed to load education plans");
      // Ensure state is always an array even on error
      setEducationPlans([]);
      setTotalCount(0);
      setTotalPages(1);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, itemsPerPage]);

  const loadOverallStats = useCallback(async () => {
    try {
      const stats = await educationPlansApi.getEducationPlansStats();
      setOverallStats(stats);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  const loadTeacherStats = useCallback(async () => {
    try {
      const stats = await teachersApi.getTeacherStats();
      setTeacherStats(stats);
    } catch (error) {
      console.error("Error fetching teacher stats:", error);
    }
  }, []);

  const loadPlanDetail = async (planId: string) => {
    try {
      const planDetail = await educationPlansApi.getEducationPlan(parseInt(planId));
      setSelectedPlanDetail(planDetail);
      return planDetail;
    } catch (error) {
      console.error("Error fetching plan details:", error);
      toast.error("Failed to load plan details");
      return null;
    }
  };

  const loadPlanSubjects = async (planId: string) => {
    try {
      setIsLoadingSubjects(true);
      
      const params = {
        ...(selectedSemester && selectedSemester !== "all" && { semester: selectedSemester }),
        ...(subjectSearchTerm.trim() && { search: subjectSearchTerm.trim() }),
      };
      
      const subjectsData = await educationPlansApi.getEducationPlanSubjects(parseInt(planId), params);
      setSubjects(subjectsData);
    } catch (error) {
      console.error("Error fetching subjects:", error);
      toast.error("Failed to load subjects");
    } finally {
      setIsLoadingSubjects(false);
    }
  };

  const loadPlanStats = async (planId: string) => {
    try {
      const stats = await educationPlansApi.getEducationPlanSubjectStats(planId);
      setPlanStats(stats);
    } catch (error) {
      console.error("Error fetching plan stats:", error);
    }
  };

  // Effects
  useEffect(() => {
    const loadInitialData = async () => {
      await loadEducationPlans(1);
      await loadOverallStats();
      await loadTeacherStats();
    };
    
    loadInitialData();
  }, [loadEducationPlans, loadOverallStats, loadTeacherStats]);

  // Event handlers
  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handleSubjectSearch = (value: string) => {
    setSubjectSearchTerm(value);
    if (selectedPlan) {
      loadPlanSubjects(selectedPlan.id);
    }
  };

  const handlePageChange = (page: number) => {
    loadEducationPlans(page);
  };

  const handleViewPlan = async (plan: EducationPlan) => {
    setSelectedPlan(plan);
    setIsViewDialogOpen(true);
    loadPlanSubjects(plan.id);
    loadPlanStats(plan.id);
  };

  const handleEditPlan = async (plan: EducationPlan) => {
    const planDetail = await loadPlanDetail(plan.id);
    if (planDetail) {
      setSelectedPlanDetail(planDetail);
      const planName = typeof planDetail.name === 'object' && planDetail.name !== null
        ? (planDetail.name.en || planDetail.name.az || planDetail.name.ru || "")
        : (planDetail.name || "");
      setEditForm({
        name: planName,
        active: planDetail.is_active
      });
      setIsEditDialogOpen(true);
    }
  };

  const handleSavePlan = async () => {
    if (!selectedPlanDetail) return;
    
    try {
      setIsSaving(true);
      
      const updatedPlan = await educationPlansApi.updateEducationPlan(Number(selectedPlanDetail.id), editForm);
      
      // Update the plans list
      setEducationPlans(plans => 
        plans.map(plan => 
          plan.id === updatedPlan.id 
            ? { ...plan, ...updatedPlan }
            : plan
        )
      );
      
      setIsEditDialogOpen(false);
      toast.success("Education plan updated successfully");
      
    } catch (error) {
      console.error("Error updating plan:", error);
      toast.error("Failed to update education plan");
    } finally {
      setIsSaving(false);
    }
  };

  const handleViewSubject = (subject: PlanSubject) => {
    setSelectedSubject(subject);
    setIsSubjectDialogOpen(true);
  };

  const formatHours = (hours: string) => {
    const num = parseInt(hours);
    return num > 0 ? `${num}h` : "-";
  };

  const formatCredit = (credit: string) => {
    const num = parseInt(credit);
    return num > 0 ? `${num} AKTS` : "-";
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-7xl mx-auto py-6 px-4">
        <div className="space-y-6">
          <div className="flex items-center space-x-2">
            <BookOpen className="h-6 w-6" />
            <h1 className="text-3xl font-bold">Education Plans</h1>
          </div>
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading education plans...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto py-6 px-4">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BookOpen className="h-6 w-6" />
            <h1 className="text-3xl font-bold">Education Plans</h1>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Plans</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overallStats?.total_education_plans || 0}
              </div>
              <p className="text-xs text-muted-foreground">Active education plans</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Subjects</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overallStats?.total_subjects || 0}
              </div>
              <p className="text-xs text-muted-foreground">Across all plans</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Teachers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {teacherStats?.active_teachers || 0}
              </div>
              <p className="text-xs text-muted-foreground">Available for teaching</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Academic Years</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overallStats?.plans_by_year ? Object.keys(overallStats.plans_by_year).length : 0}
              </div>
              <p className="text-xs text-muted-foreground">Different years covered</p>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Education Plans</CardTitle>
            <CardDescription>
              Manage and view education plans, subjects, and curriculum details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search education plans..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Education Plans Table */}
        <Card>
          <CardHeader>
            <CardTitle>Plans ({totalCount})</CardTitle>
            <CardDescription>
              {totalCount} education plan{totalCount !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading education plans...</p>
              </div>
            ) : !educationPlans || educationPlans.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No education plans found</h3>
                <p className="text-muted-foreground">
                  {searchTerm 
                    ? "Try adjusting your search terms" 
                    : "No education plans are available"}
                </p>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Program Name</TableHead>
                      <TableHead>Degree Type</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Credits</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(educationPlans || []).map((plan) => (
                      <TableRow key={plan.id}>
                        <TableCell className="font-mono text-xs">{plan.code || plan.id}</TableCell>
                        <TableCell className="font-medium">
                          {typeof plan.name === 'object' && plan.name !== null 
                            ? (plan.name.en || plan.name.az || plan.name.ru || '-')
                            : (plan.name || '-')}
                        </TableCell>
                        <TableCell className="max-w-sm">
                          <div className="text-sm">
                            <span className="capitalize">{plan.degree_type || '-'}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {plan.duration_years ? `${plan.duration_years} years` : '-'}
                        </TableCell>
                        <TableCell>
                          {plan.total_credits || '-'} credits
                        </TableCell>
                        <TableCell>
                          <Badge variant="default">
                            Active
                          </Badge>
                        </TableCell>
                        <TableCell>
                          -
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewPlan(plan)}
                            >
                              <Eye className="h-4 w-4" />
                              View
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditPlan(plan)}
                            >
                              Edit
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Plan View Dialog */}
        <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
          <DialogContent className="max-w-7xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Education Plan Details</DialogTitle>
              <DialogDescription>
                Detailed view of {
                  selectedPlan?.name 
                    ? (typeof selectedPlan.name === 'object' 
                        ? (selectedPlan.name.en || selectedPlan.name.az || selectedPlan.name.ru)
                        : selectedPlan.name)
                    : `Plan ${selectedPlan?.id}`
                }
              </DialogDescription>
            </DialogHeader>
            
            {selectedPlan && (
              <div className="space-y-6">
                {/* Plan Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Plan Code</label>
                    <p className="text-lg font-mono">{selectedPlan.code || selectedPlan.id}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Degree Type</label>
                    <p className="text-lg capitalize">{selectedPlan.degree_type || 'Unknown'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Plan Name</label>
                    <p>
                      {selectedPlan.name 
                        ? (typeof selectedPlan.name === 'object' 
                            ? (selectedPlan.name.en || selectedPlan.name.az || selectedPlan.name.ru)
                            : selectedPlan.name)
                        : 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Duration</label>
                    <p>{selectedPlan.duration_years ? `${selectedPlan.duration_years} years` : 'Not provided'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Total Credits</label>
                    <p>{selectedPlan.total_credits || 'Not provided'}</p>
                  </div>
                </div>

                {/* Plan Stats */}
                {planStats && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{planStats.total_subjects}</div>
                      <div className="text-sm text-muted-foreground">Total Subjects</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{planStats.total_credits}</div>
                      <div className="text-sm text-muted-foreground">Total Credits</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{planStats.total_hours}</div>
                      <div className="text-sm text-muted-foreground">Total Hours</div>
                    </div>
                  </div>
                )}

                {/* Subjects Search */}
                <div className="flex items-center space-x-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search subjects..."
                      value={subjectSearchTerm}
                      onChange={(e) => handleSubjectSearch(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                  
                  {planStats?.subjects_by_semester && (
                    <Select
                      value={selectedSemester}
                      onValueChange={setSelectedSemester}
                    >
                      <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="All semesters" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All semesters</SelectItem>
                        {Object.keys(planStats.subjects_by_semester).map((semester) => (
                          <SelectItem key={semester} value={semester}>
                            {semester}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                {/* Subjects Table */}
                {isLoadingSubjects ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-2 text-sm text-muted-foreground">Loading subjects...</p>
                  </div>
                ) : !subjects || subjects.length === 0 ? (
                  <div className="text-center py-8">
                    <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">No subjects found</p>
                  </div>
                ) : (
                  <div className="rounded-md border max-h-96 overflow-y-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Code</TableHead>
                          <TableHead>Subject</TableHead>
                          <TableHead>Semester</TableHead>
                          <TableHead>Department</TableHead>
                          <TableHead>Credit</TableHead>
                          <TableHead>Hours</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(subjects || []).map((subject, index) => (
                          <TableRow key={`${subject.id}-${subject.subject_code}-${subject.semester_name_az || 'no-sem'}-${index}`}>
                            <TableCell className="font-mono text-xs">{subject.subject_code}</TableCell>
                            <TableCell className="font-medium text-sm">
                              {subject.subject_name_az}
                            </TableCell>
                            <TableCell className="text-sm">{subject.semester_name_az}</TableCell>
                            <TableCell className="text-sm">{subject.department_name_az}</TableCell>
                            <TableCell>{formatCredit(String(subject.credit || 0))}</TableCell>
                            <TableCell>{formatHours(String(subject.all_hours || 0))}</TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewSubject(subject)}
                              >
                                <Eye className="h-3 w-3" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Subject Detail Dialog */}
        <Dialog open={isSubjectDialogOpen} onOpenChange={setIsSubjectDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Subject Details</DialogTitle>
              <DialogDescription>
                Detailed information about the selected subject
              </DialogDescription>
            </DialogHeader>
            
            {selectedSubject && (
              <div className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Subject Code</label>
                    <p className="text-lg font-mono">{selectedSubject.subject_code}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Subject Name</label>
                    <p className="text-lg">{selectedSubject.subject_name_az}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Department</label>
                    <p>{selectedSubject.department_name_az}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Semester</label>
                    <p>{selectedSubject.semester_name_az}</p>
                  </div>
                </div>

                {/* Hours Breakdown */}
                <div>
                  <h4 className="font-medium mb-3">Hour Distribution</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{selectedSubject.all_hours}h</div>
                      <div className="text-xs text-muted-foreground">Total Hours</div>
                    </div>
                    <div className="text-center p-3 bg-muted rounded-lg">
                      <div className="text-xl font-semibold">{formatHours(String(selectedSubject.out_hours || 0))}</div>
                      <div className="text-xs text-muted-foreground">Outside Hours</div>
                    </div>
                    <div className="text-center p-3 bg-muted rounded-lg">
                      <div className="text-xl font-semibold">{formatHours(String(selectedSubject.in_hours || 0))}</div>
                      <div className="text-xs text-muted-foreground">In-Class Hours</div>
                    </div>
                    <div className="text-center p-3 bg-muted rounded-lg">
                      <div className="text-xl font-semibold">{formatCredit(String(selectedSubject.credit || 0))}</div>
                      <div className="text-xs text-muted-foreground">Credits</div>
                    </div>
                  </div>
                </div>

                {/* Detailed Hours */}
                {(selectedSubject.m_hours || selectedSubject.s_hours || selectedSubject.l_hours || selectedSubject.fm_hours) && (
                  <div>
                    <h4 className="font-medium mb-3">Class Type Breakdown</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {selectedSubject.m_hours && (
                        <div className="p-2 border rounded">
                          <div className="font-semibold">{formatHours(String(selectedSubject.m_hours || 0))}</div>
                          <div className="text-xs text-muted-foreground">Lectures</div>
                        </div>
                      )}
                      {selectedSubject.s_hours && (
                        <div className="p-2 border rounded">
                          <div className="font-semibold">{formatHours(String(selectedSubject.s_hours || 0))}</div>
                          <div className="text-xs text-muted-foreground">Seminars</div>
                        </div>
                      )}
                      {selectedSubject.l_hours && (
                        <div className="p-2 border rounded">
                          <div className="font-semibold">{formatHours(String(selectedSubject.l_hours || 0))}</div>
                          <div className="text-xs text-muted-foreground">Labs</div>
                        </div>
                      )}
                      {selectedSubject.fm_hours && (
                        <div className="p-2 border rounded">
                          <div className="font-semibold">{formatHours(String(selectedSubject.fm_hours || 0))}</div>
                          <div className="text-xs text-muted-foreground">Final/Exam</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Status */}
                <div className="flex gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Course Work</label>
                    <div className="mt-1">
                      <Badge variant={selectedSubject.course_work === "1" ? "default" : "secondary"}>
                        {selectedSubject.course_work === "1" ? "Required" : "Not Required"}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Status</label>
                    <div className="mt-1">
                      <Badge variant={selectedSubject.chosen_status === "1" ? "default" : "outline"}>
                        {selectedSubject.chosen_status === "1" ? "Chosen" : "Not Chosen"}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Edit Plan Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Edit Education Plan</DialogTitle>
              <DialogDescription>
                Update the education plan information
              </DialogDescription>
            </DialogHeader>
            
            {selectedPlanDetail && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Plan ID</label>
                  <Input value={selectedPlanDetail.id} disabled className="bg-muted" />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">Plan Name</label>
                  <Input
                    value={editForm.name || ""}
                    onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter plan name"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="active"
                    checked={editForm.active || false}
                    onChange={(e) => setEditForm(prev => ({ ...prev, active: e.target.checked }))}
                    className="rounded"
                  />
                  <label htmlFor="active" className="text-sm font-medium">Active</label>
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => setIsEditDialogOpen(false)}
                    disabled={isSaving}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSavePlan}
                    disabled={isSaving}
                  >
                    {isSaving ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}