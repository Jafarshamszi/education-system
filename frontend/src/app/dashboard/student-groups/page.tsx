"use client";

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Search,
  Users,
  GraduationCap,
  Building2,
  UserCheck,
  TrendingUp,
  Filter,
  Eye,
  Plus,
  Pencil,
  Trash2
} from 'lucide-react';
import {
  getStudentGroups,
  getStudentGroupsStats,
  getStudentGroupDetail,
  getOrganizations,
  getEducationTypes,
  getEducationLevels,
  createStudentGroup,
  updateStudentGroup,
  deleteStudentGroup,
  getOrganizationsLookup,
  getEducationLevelsLookup,
  getEducationTypesLookup,
  getLanguagesLookup,
  getTutorsLookup,
  type StudentGroupsFilters
} from '@/lib/api/student-groups';
import { toast } from 'sonner';
import {
  StudentGroup,
  StudentGroupDetail,
  StudentGroupStats
} from '@/types/student-groups';
import { useLanguage } from '@/contexts/LanguageContext';

export default function StudentGroupsPage() {
  const { language } = useLanguage();
  
  // Helper function to get localized name
  const getLocalizedName = (name: string | { az: string; en: string; ru: string } | unknown): string => {
    if (!name) return '';
    if (typeof name === 'string') return name;
    if (typeof name === 'object' && name !== null) {
      const nameObj = name as Record<string, string | Record<string, string>>;
      // Handle nested multi-language objects
      if (nameObj[language]) {
        if (typeof nameObj[language] === 'string') return nameObj[language] as string;
        if (typeof nameObj[language] === 'object') {
          const nested = nameObj[language] as Record<string, string>;
          return nested[language] || nested.en || nested.az || '';
        }
      }
      const azValue = nameObj.az || nameObj.en || nameObj.ru;
      return typeof azValue === 'string' ? azValue : '';
    }
    return String(name);
  };
  
  // State for groups data
  const [groups, setGroups] = useState<StudentGroup[]>([]);
  const [stats, setStats] = useState<StudentGroupStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for filters
  const [filters, setFilters] = useState<StudentGroupsFilters>({
    search: '',
    organization: '',
    education_type: '',
    education_level: '',
    limit: 50,
    offset: 0
  });
  
  // Type definitions
  type MultiLangName = { az: string; en: string; ru: string };
  type LookupItem = { id: string; name: string | MultiLangName };
  
  // State for filter options
  const [organizations, setOrganizations] = useState<LookupItem[]>([]);
  const [educationTypes, setEducationTypes] = useState<LookupItem[]>([]);
  const [educationLevels, setEducationLevels] = useState<LookupItem[]>([]);
  
  // State for group detail dialog
  const [selectedGroup, setSelectedGroup] = useState<StudentGroupDetail | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // State for create/edit dialog
  const [isCreateEditOpen, setIsCreateEditOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<StudentGroup | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    organization_id: '',
    education_level_id: '',
    education_type_id: '',
    education_lang_id: '',
    tyutor_id: ''
  });
  const [formLoading, setFormLoading] = useState(false);

  // Lookup data for dropdowns
  const [organizationsLookup, setOrganizationsLookup] = useState<LookupItem[]>([]);
  const [educationLevelsLookup, setEducationLevelsLookup] = useState<LookupItem[]>([]);
  const [educationTypesLookup, setEducationTypesLookup] = useState<LookupItem[]>([]);
  const [languagesLookup, setLanguagesLookup] = useState<LookupItem[]>([]);
  const [tutorsLookup, setTutorsLookup] = useState<LookupItem[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [groupsData, statsData] = await Promise.all([
        getStudentGroups(filters),
        getStudentGroupsStats()
      ]);
      
      setGroups(groupsData.results);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading student groups:', err);
      setError('Failed to load student groups. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const loadGroups = useCallback(async () => {
    try {
      const groupsData = await getStudentGroups(filters);
      setGroups(groupsData.results);
    } catch (err) {
      console.error('Error loading groups:', err);
      setError('Failed to load groups.');
    }
  }, [filters]);

  // Load initial data
  useEffect(() => {
    loadData();
    loadFilterOptions();
  }, [loadData]);

  // Load data when filters change  
  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  const loadFilterOptions = async () => {
    try {
      const [orgs, types, levels] = await Promise.all([
        getOrganizations().catch(err => {
          console.error('Failed to load organizations:', err);
          return [];
        }),
        getEducationTypes().catch(err => {
          console.error('Failed to load education types:', err);
          return [];
        }),
        getEducationLevels().catch(err => {
          console.error('Failed to load education levels:', err);
          return [];
        })
      ]);
      
      setOrganizations(orgs);
      setEducationTypes(types);
      setEducationLevels(levels);
    } catch (err) {
      console.error('Error loading filter options:', err);
      // Don't block the UI, just use empty arrays
    }
  };

  const handleFilterChange = (key: keyof StudentGroupsFilters, value: string | number) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value,
      offset: 0 // Reset pagination when filters change
    }));
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      organization: '',
      education_type: '',
      education_level: '',
      limit: 50,
      offset: 0
    });
  };

  const openGroupDetail = async (groupId: string) => {
    try {
      setDetailLoading(true);
      const groupDetail = await getStudentGroupDetail(groupId);
      setSelectedGroup(groupDetail);
      setDetailDialogOpen(true);
    } catch (err) {
      console.error('Error loading group detail:', err);
      setError('Failed to load group details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'N/A';
    }
  };

  const loadLookupData = async () => {
    try {
      const [orgs, levels, types, langs, tutors] = await Promise.all([
        getOrganizationsLookup(),
        getEducationLevelsLookup(),
        getEducationTypesLookup(),
        getLanguagesLookup(),
        getTutorsLookup()
      ]);

      setOrganizationsLookup(orgs);
      setEducationLevelsLookup(levels);
      setEducationTypesLookup(types);
      setLanguagesLookup(langs);
      setTutorsLookup(tutors);
    } catch (err) {
      console.error('Error loading lookup data:', err);
      toast.error('Failed to load form options');
    }
  };

  const handleCreateNew = async () => {
    setEditingGroup(null);
    setFormData({
      name: '',
      organization_id: '',
      education_level_id: '',
      education_type_id: '',
      education_lang_id: '',
      tyutor_id: ''
    });
    await loadLookupData();
    setIsCreateEditOpen(true);
  };

  const handleEdit = async (group: StudentGroup) => {
    setEditingGroup(group);
    setFormData({
      name: group.group_name || '',
      organization_id: group.organization_id?.toString() || '',
      education_level_id: group.education_level_id?.toString() || '',
      education_type_id: group.education_type_id?.toString() || '',
      education_lang_id: group.education_lang_id?.toString() || '',
      tyutor_id: group.tyutor_id?.toString() || ''
    });
    await loadLookupData();
    setIsCreateEditOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('Group name is required');
      return;
    }

    setFormLoading(true);
    try {
      const payload = {
        name: formData.name,
        organization_id: formData.organization_id ? parseInt(formData.organization_id) : undefined,
        education_level_id: formData.education_level_id ? parseInt(formData.education_level_id) : undefined,
        education_type_id: formData.education_type_id ? parseInt(formData.education_type_id) : undefined,
        education_lang_id: formData.education_lang_id ? parseInt(formData.education_lang_id) : undefined,
        tyutor_id: formData.tyutor_id ? parseInt(formData.tyutor_id) : undefined,
      };

      if (editingGroup) {
        await updateStudentGroup(editingGroup.id, payload);
        toast.success('Student group updated successfully');
      } else {
        await createStudentGroup(payload);
        toast.success('Student group created successfully');
      }

      setIsCreateEditOpen(false);
      loadData();
    } catch (err) {
      console.error('Error saving student group:', err);
      toast.error('Failed to save student group');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (group: StudentGroup) => {
    if (!confirm(`Are you sure you want to delete group "${group.group_name}"?`)) {
      return;
    }

    try {
      await deleteStudentGroup(group.id);
      toast.success('Student group deleted successfully');
      loadData();
    } catch (err) {
      console.error('Error deleting student group:', err);
      toast.error('Failed to delete student group');
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading student groups...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Student Groups</h1>
          <p className="text-muted-foreground">
            Manage and view student groups across all organizations
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Button onClick={handleCreateNew}>
            <Plus className="w-4 h-4 mr-2" />
            Create New Group
          </Button>
          {stats && (
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-sm">
                <Users className="w-4 h-4 mr-1" />
                {stats.total_groups} Groups
              </Badge>
              <Badge variant="secondary" className="text-sm">
                <UserCheck className="w-4 h-4 mr-1" />
                {stats.total_students} Students
              </Badge>
            </div>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Groups</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_groups}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Students</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_students}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Organizations</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.groups_by_organization ? Object.keys(stats.groups_by_organization).length : 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Students/Group</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.total_groups > 0 ? Math.round(stats.average_group_size) : 0}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search groups..."
                  value={filters.search || ''}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Organization</label>
              <Select 
                value={filters.organization || 'all'} 
                onValueChange={(value) => handleFilterChange('organization', value === 'all' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All organizations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All organizations</SelectItem>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {getLocalizedName(org.name)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Education Type</label>
              <Select 
                value={filters.education_type || 'all'} 
                onValueChange={(value) => handleFilterChange('education_type', value === 'all' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  {educationTypes.map((type) => (
                    <SelectItem key={type.id} value={type.id}>
                      {getLocalizedName(type.name)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Education Level</label>
              <Select 
                value={filters.education_level || 'all'} 
                onValueChange={(value) => handleFilterChange('education_level', value === 'all' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All levels</SelectItem>
                  {educationLevels.map((level) => (
                    <SelectItem key={level.id} value={level.id}>
                      {getLocalizedName(level.name)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium invisible">Actions</label>
              <Button variant="outline" onClick={clearFilters} className="w-full">
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Groups Table */}
      <Card>
        <CardHeader>
          <CardTitle>Student Groups ({groups.length})</CardTitle>
          <CardDescription>
            View and manage all student groups in the system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Group Name</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Students</TableHead>
                  <TableHead>Education Level</TableHead>
                  <TableHead>Education Type</TableHead>
                  <TableHead>Language</TableHead>
                  <TableHead>Tutor</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-8">
                      <div className="flex flex-col items-center gap-2">
                        <Users className="w-8 h-8 text-muted-foreground" />
                        <p className="text-muted-foreground">No student groups found</p>
                        <Button variant="outline" onClick={() => clearFilters()}>
                          Clear filters to see all groups
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  groups.map((group) => (
                    <TableRow key={group.id}>
                      <TableCell className="font-medium">
                        {group.group_name || 'N/A'}
                      </TableCell>
                      <TableCell>{group.organization_name || 'N/A'}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {group.student_count}
                        </Badge>
                      </TableCell>
                      <TableCell>{group.education_level || 'N/A'}</TableCell>
                      <TableCell>{group.education_type || 'N/A'}</TableCell>
                      <TableCell>{group.language || 'N/A'}</TableCell>
                      <TableCell>{group.tutor_full_name || 'N/A'}</TableCell>
                      <TableCell>{formatDate(group.create_date)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openGroupDetail(group.id)}
                            disabled={detailLoading}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(group)}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(group)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Group Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Group Details: {selectedGroup?.group_name}</DialogTitle>
            <DialogDescription>
              Detailed information about the student group and its members
            </DialogDescription>
          </DialogHeader>

          {selectedGroup && (
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="info">Group Info</TabsTrigger>
                <TabsTrigger value="students">Students ({selectedGroup.student_count})</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Organization</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.organization_name || 'N/A'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Student Count</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.student_count} students
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Education Level</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.education_level || 'N/A'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Education Type</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.education_type || 'N/A'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Language</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.language || 'N/A'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Tutor</label>
                    <p className="text-sm text-muted-foreground">
                      {selectedGroup.tutor_full_name || 'N/A'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Created</label>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(selectedGroup.create_date)}
                    </p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="students" className="space-y-4">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>PIN Code</TableHead>
                        <TableHead>Joined Group</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedGroup.students.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center py-4">
                            No students in this group
                          </TableCell>
                        </TableRow>
                      ) : (
                        selectedGroup.students.map((student) => (
                          <TableRow key={student.id}>
                            <TableCell>
                              {`${student.firstname || ''} ${student.lastname || ''}`.trim() || 'N/A'}
                            </TableCell>
                            <TableCell>{student.pincode || 'N/A'}</TableCell>
                            <TableCell>{formatDate(student.joined_group_date)}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>

      {/* Create/Edit Dialog */}
      <Dialog open={isCreateEditOpen} onOpenChange={setIsCreateEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingGroup ? 'Edit Student Group' : 'Create New Student Group'}
            </DialogTitle>
            <DialogDescription>
              {editingGroup ? 'Update the group information below' : 'Enter the details for the new student group'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Group Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter group name (e.g., CS-101-2024)"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Organization</label>
                <Select
                  value={formData.organization_id}
                  onValueChange={(value) => setFormData({ ...formData, organization_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {organizationsLookup.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
                        {getLocalizedName(org.name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Education Level</label>
                <Select
                  value={formData.education_level_id}
                  onValueChange={(value) => setFormData({ ...formData, education_level_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {educationLevelsLookup.map((level) => (
                      <SelectItem key={level.id} value={level.id}>
                        {getLocalizedName(level.name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Education Type</label>
                <Select
                  value={formData.education_type_id}
                  onValueChange={(value) => setFormData({ ...formData, education_type_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {educationTypesLookup.map((type) => (
                      <SelectItem key={type.id} value={type.id}>
                        {getLocalizedName(type.name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Language</label>
                <Select
                  value={formData.education_lang_id}
                  onValueChange={(value) => setFormData({ ...formData, education_lang_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {languagesLookup.map((lang) => (
                      <SelectItem key={lang.id} value={lang.id}>
                        {getLocalizedName(lang.name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium">Tutor</label>
                <Select
                  value={formData.tyutor_id}
                  onValueChange={(value) => setFormData({ ...formData, tyutor_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select tutor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {tutorsLookup.map((tutor) => (
                      <SelectItem key={tutor.id} value={tutor.id}>
                        {getLocalizedName(tutor.name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setIsCreateEditOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={formLoading}>
                {formLoading ? 'Saving...' : editingGroup ? 'Update' : 'Create'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}