'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useForm, Controller } from 'react-hook-form';
import { 
  CourseInfo, 
  CourseCreate, 
  CourseUpdate,
  TeacherInfo,
  SubjectInfo,
  EducationGroup,
  EducationLanguage,
  SemesterInfo,
  CourseStudentInfo,
  AvailableStudent,
  createCourse, 
  updateCourse,
  getTeachers,
  getTeachersByOrganization,
  getEducationGroupOrganization,
  getSubjects,
  getEducationGroups,
  getEducationLanguages,
  getSemesters,
  getCourseTeachers,
  assignTeacher,
  removeTeacher,
  assignMultipleTeachers,
  getCourseStudentsDetailed,
  manageCourseStudents,
  getAvailableStudents,
  getEducationGroupStudents
} from '@/lib/api/class-schedule';
import { toast } from 'sonner';
import { BookOpen, Users, Calendar, Globe, Clock, User, GraduationCap, X, Plus, Search } from 'lucide-react';

interface CourseEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  course?: CourseInfo | null;
  onSave: (course: CourseInfo) => void;
}

interface CourseFormData {
  code: string;
  subject_id?: number;
  teacher_id?: number;
  education_group_id?: number;
  education_language_id?: number;
  semester_id?: number;
  start_date?: string;
  m_hours?: number;
  s_hours?: number;
  l_hours?: number;
  fm_hours?: number;
  note?: string;
}

export function EnhancedCourseEditModal({ isOpen, onClose, course, onSave }: CourseEditModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState('basic');
  
  // Dropdown data states
  const [teachers, setTeachers] = useState<TeacherInfo[]>([]);
  const [subjects, setSubjects] = useState<SubjectInfo[]>([]);
  const [educationGroups, setEducationGroups] = useState<EducationGroup[]>([]);
  const [educationLanguages, setEducationLanguages] = useState<EducationLanguage[]>([]);
  const [semesters, setSemesters] = useState<SemesterInfo[]>([]);
  
  // Assigned teachers for existing courses
  const [assignedTeachers, setAssignedTeachers] = useState<TeacherInfo[]>([]);
  
  // Enhanced student management states
  const [courseStudents, setCourseStudents] = useState<CourseStudentInfo[]>([]);
  const [availableStudents, setAvailableStudents] = useState<AvailableStudent[]>([]);
  const [groupStudents, setGroupStudents] = useState<AvailableStudent[]>([]);
  const [studentSearchTerm, setStudentSearchTerm] = useState('');
  const [selectedEducationGroupForStudents, setSelectedEducationGroupForStudents] = useState<number | null>(null);
  
  // Teacher search states
  const [searchedTeachers, setSearchedTeachers] = useState<TeacherInfo[]>([]);
  const [teacherSearchTerm, setTeacherSearchTerm] = useState('');
  
  const { register, handleSubmit, control, setValue, watch, formState: { errors } } = useForm<CourseFormData>();
  
  // Watch education_group_id to filter teachers by organization
  const selectedEducationGroupId = watch('education_group_id');
  
  const isEditMode = !!course;

  // Load dropdown data on modal open
  useEffect(() => {
    if (isOpen) {
      loadDropdownData();
      if (course) {
        loadCourseData();
        loadCourseStudents();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, course]);

  // Debounced search for students
  useEffect(() => {
    if (studentSearchTerm.length >= 2) {
      const timeoutId = setTimeout(() => {
        searchAvailableStudents(studentSearchTerm);
      }, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setAvailableStudents([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentSearchTerm, selectedEducationGroupForStudents, course?.id]);

  // Debounced search for teachers
  useEffect(() => {
    if (teacherSearchTerm.length >= 2) {
      const timeoutId = setTimeout(() => {
        searchTeachers(teacherSearchTerm);
      }, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setSearchedTeachers([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teacherSearchTerm, teachers]);

  // Filter teachers by education group organization
  useEffect(() => {
    if (selectedEducationGroupId) {
      loadTeachersByEducationGroup(selectedEducationGroupId);
    } else {
      // Load all teachers if no education group is selected
      loadAllTeachers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEducationGroupId]);

  const loadAllTeachers = async () => {
    try {
      const teachersData = await getTeachers();
      setTeachers(teachersData);
    } catch (error) {
      console.error('Failed to load teachers:', error);
      toast.error('Failed to load teachers');
    }
  };

  const loadTeachersByEducationGroup = async (educationGroupId: number) => {
    try {
      // First get the organization_id for this education group
      const orgData = await getEducationGroupOrganization(educationGroupId);
      
      // Then get teachers filtered by that organization
      const filteredTeachers = await getTeachersByOrganization(orgData.organization_id);
      setTeachers(filteredTeachers);
      
      // Show toast to inform user
      if (filteredTeachers.length > 0) {
        toast.success(`Showing ${filteredTeachers.length} teachers from ${orgData.organization_name}`);
      } else {
        toast.info(`No teachers found for ${orgData.organization_name}. Showing all teachers.`);
        // Fallback to all teachers if none found in organization
        loadAllTeachers();
      }
    } catch (error) {
      console.error('Failed to load filtered teachers:', error);
      // Fallback to all teachers on error
      loadAllTeachers();
    }
  };

  const loadDropdownData = async () => {
    try {
      setIsLoading(true);
      
      const [teachersData, subjectsData, groupsData, languagesData, semestersData] = await Promise.all([
        getTeachers(),
        getSubjects(),
        getEducationGroups(),
        getEducationLanguages(),
        getSemesters()
      ]);
      
      setTeachers(teachersData);
      setSubjects(subjectsData);
      setEducationGroups(groupsData);
      setEducationLanguages(languagesData);
      setSemesters(semestersData);
      
    } catch (error) {
      console.error('Failed to load dropdown data:', error);
      toast.error('Failed to load form data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCourseData = async () => {
    if (!course) return;
    if (!course.id) {
      console.error('Course ID is missing');
      return;
    }
    
    try {
      // Load assigned teachers for existing course
      const assignedTeachersData = await getCourseTeachers(course.id);
      setAssignedTeachers(assignedTeachersData);
      
      // Populate form with course data
      setValue('code', course.code || course.course_code || '');
      setValue('start_date', course.start_date || '');
      setValue('m_hours', course.m_hours || 0);
      setValue('s_hours', course.s_hours || 0);
      setValue('l_hours', course.l_hours || 0);
      setValue('fm_hours', course.fm_hours || 0);
      
    } catch (error) {
      console.error('Failed to load course data:', error);
      toast.error('Failed to load course details');
    }
  };

  // Load course students for editing
  const loadCourseStudents = async () => {
    if (!course?.id) return;
    
    try {
      const students = await getCourseStudentsDetailed(course.id);
      setCourseStudents(students);
    } catch (error) {
      console.error('Failed to load course students:', error);
      toast.error('Failed to load course students');
    }
  };

  // Load students from a specific education group
  const loadEducationGroupStudents = async (groupId: number) => {
    try {
      const students = await getEducationGroupStudents(groupId);
      setGroupStudents(students);
    } catch (error) {
      console.error('Failed to load group students:', error);
      toast.error('Failed to load group students');
    }
  };

  // Search for teachers
  const searchTeachers = async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setSearchedTeachers([]);
      return;
    }
    
    // Filter from existing teachers list
    const filtered = teachers.filter(teacher => 
      (teacher.name && teacher.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (teacher.full_name && teacher.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (teacher.username && teacher.username.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    setSearchedTeachers(filtered);
  };

  // Search for available students
  const searchAvailableStudents = async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setAvailableStudents([]);
      return;
    }
    
    try {
      const students = await getAvailableStudents(selectedEducationGroupForStudents || undefined);
      // Filter by search term client-side
      const filtered = students.filter((student: AvailableStudent) =>
        (student.name && student.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (student.full_name && student.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (student.student_number && student.student_number.toString().includes(searchTerm)) ||
        (student.student_id_number && student.student_id_number.toString().includes(searchTerm))
      );
      setAvailableStudents(filtered);
    } catch (error) {
      console.error('Failed to search students:', error);
    }
  };

  // Handle multiple teacher assignment
  const handleAssignTeachers = async (selectedTeacherIds: (string | number)[]) => {
    if (!course?.id) return;
    
    try {
      await assignMultipleTeachers(course.id, selectedTeacherIds);
      const updatedTeachers = await getCourseTeachers(course.id);
      setAssignedTeachers(updatedTeachers);
      toast.success(`${selectedTeacherIds.length} teachers assigned successfully`);
    } catch (error) {
      console.error('Failed to assign teachers:', error);
      toast.error('Failed to assign teachers');
    }
  };

  // Handle student management
  const handleAddStudent = async (studentId: string | number) => {
    if (!course?.id) return;
    
    try {
      await manageCourseStudents(course.id, [studentId], 'add');
      await loadCourseStudents();
      setAvailableStudents(prev => prev.filter(s => s.id !== studentId));
      toast.success('Student added successfully');
    } catch (error) {
      console.error('Failed to add student:', error);
      toast.error('Failed to add student');
    }
  };

  const handleRemoveStudent = async (studentId: string | number | undefined) => {
    if (!course?.id || !studentId) return;
    
    try {
      await manageCourseStudents(course.id, [studentId], 'remove');
      await loadCourseStudents();
      toast.success('Student removed successfully');
    } catch (error) {
      console.error('Failed to remove student:', error);
      toast.error('Failed to remove student');
    }
  };

  const handleRemoveTeacher = async (teacherId: string | number) => {
    if (!course?.id) return;
    
    try {
      await removeTeacher(course.id, teacherId);
      const updatedTeachers = await getCourseTeachers(course.id);
      setAssignedTeachers(updatedTeachers);
      toast.success('Teacher removed successfully');
    } catch (error) {
      console.error('Failed to remove teacher:', error);
      toast.error('Failed to remove teacher');
    }
  };

  const onSubmit = async (data: CourseFormData) => {
    try {
      setIsLoading(true);
      
      let result: CourseInfo;
      
      if (isEditMode && course) {
        // Update existing course
        if (!course.id) throw new Error('Course ID is required for update');
        
        const updateData: CourseUpdate = {
          course_code: data.code,
          description: data.note || undefined,
          is_active: true,
        };
        
        result = await updateCourse(course.id, updateData);
        
        // Handle teacher assignment if selected
        if (data.teacher_id) {
          try {
            await assignTeacher(course.id, data.teacher_id);
          } catch (error) {
            console.warn('Teacher assignment failed:', error);
          }
        }
        
      } else {
        // Create new course
        const createData: CourseCreate = {
          course_name: data.code, // Using code as course name for now
          course_code: data.code,
          description: data.note || undefined,
          credits: 0, // Default value
          semester_id: data.semester_id || 1, // Default to semester 1
          education_group_id: data.education_group_id || 1, // Default value
          subject_id: data.subject_id || 1, // Default value
          education_language_id: data.education_language_id || 1, // Default value
        };
        
        result = await createCourse(createData);
        
        // Assign teacher if selected
        if (data.teacher_id && result.id) {
          try {
            await assignTeacher(result.id, data.teacher_id);
          } catch (error) {
            console.warn('Teacher assignment failed:', error);
          }
        }
      }
      
      toast.success(isEditMode ? 'Course updated successfully' : 'Course created successfully');
      onSave(result);
      onClose();
      
    } catch (error) {
      console.error('Failed to save course:', error);
      toast.error('Failed to save course');
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            {isEditMode ? 'Edit Course' : 'Create New Course'}
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit(onSubmit)}>
          <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic" className="flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                Basic Info
              </TabsTrigger>
              <TabsTrigger value="assignment" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Assignment
              </TabsTrigger>
              <TabsTrigger value="schedule" className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Schedule
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2">
                <GraduationCap className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>
            
            {/* Basic Information Tab */}
            <TabsContent value="basic" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    Course Details
                  </CardTitle>
                  <CardDescription>
                    Basic information about the course
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="code">Course Code *</Label>
                      <Input
                        id="code"
                        {...register('code', { required: 'Course code is required' })}
                        placeholder="e.g., CS101"
                      />
                      {errors.code && (
                        <p className="text-sm text-red-500">{errors.code.message}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="start_date">Start Date</Label>
                      <Input
                        id="start_date"
                        type="date"
                        {...register('start_date')}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="subject_id">Subject</Label>
                    <Controller
                      name="subject_id"
                      control={control}
                      render={({ field }) => (
                        <Select
                          value={field.value?.toString()}
                          onValueChange={(value) => field.onChange(parseInt(value))}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select subject" />
                          </SelectTrigger>
                          <SelectContent>
                            {subjects.map((subject) => (
                              <SelectItem key={subject.id} value={subject.id.toString()}>
                                <div className="flex items-center gap-2">
                                  {subject.subject_code && <Badge variant="outline">{subject.subject_code}</Badge>}
                                  {subject.subject_name}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="note">Notes</Label>
                    <Textarea
                      id="note"
                      {...register('note')}
                      placeholder="Additional notes or description"
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Enhanced Assignment Tab */}
            <TabsContent value="assignment" className="space-y-6">
              {/* Multiple Teacher Assignment */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Teacher Assignment
                  </CardTitle>
                  <CardDescription>
                    Assign multiple teachers to this course
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Currently Assigned Teachers */}
                  {assignedTeachers.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">Currently Assigned Teachers ({assignedTeachers.length})</Label>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {assignedTeachers.map((teacher) => (
                          <div key={teacher.id} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                            <div>
                              <p className="font-medium text-green-800">{teacher.name}</p>
                              {teacher.organization && (
                                <p className="text-xs text-green-600">{teacher.organization}</p>
                              )}
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => handleRemoveTeacher(teacher.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Teacher Search and Add */}
                  <div className="space-y-2">
                    <Label htmlFor="teacher-search">Add Teachers</Label>
                    <div className="relative">
                      <Input
                        id="teacher-search"
                        placeholder="Search teachers..."
                        value={teacherSearchTerm}
                        onChange={(e) => setTeacherSearchTerm(e.target.value)}
                      />
                      <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    </div>
                    {searchedTeachers.length > 0 && (
                      <Card className="absolute z-10 w-full max-h-60 overflow-y-auto">
                        <CardContent className="p-0">
                          {searchedTeachers
                            .filter(teacher => !assignedTeachers.some(at => at.id === teacher.id))
                            .map((teacher) => (
                            <div
                              key={teacher.id}
                              className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                              onClick={() => {
                                if (course?.id) {
                                  const newTeacherIds = [...assignedTeachers.map(t => t.id), teacher.id];
                                  handleAssignTeachers(newTeacherIds);
                                }
                                setTeacherSearchTerm('');
                                setSearchedTeachers([]);
                              }}
                            >
                              <div className="font-medium">{teacher.name}</div>
                              {teacher.organization && (
                                <div className="text-sm text-gray-500">{teacher.organization}</div>
                              )}
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Advanced Student Management */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Student Management
                  </CardTitle>
                  <CardDescription>
                    Manage individual students for this course
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Education Group Selection for bulk add */}
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Label htmlFor="education-group">Add from Education Group</Label>
                      <Select
                        value={selectedEducationGroupForStudents?.toString() || ''}
                        onValueChange={(value) => {
                          const groupId = parseInt(value);
                          setSelectedEducationGroupForStudents(groupId);
                          loadEducationGroupStudents(groupId);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select education group" />
                        </SelectTrigger>
                        <SelectContent>
                          {educationGroups.map((group) => (
                            <SelectItem key={group.id} value={group.id.toString()}>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{group.group_name}</span>
                                <Badge variant="secondary">
                                  {group.group_code}
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {selectedEducationGroupForStudents && groupStudents.length > 0 && (
                      <Button
                        type="button"
                        onClick={() => {
                          if (course?.id) {
                            const studentIds = groupStudents
                              .filter(student => !courseStudents.some(cs => cs.student_id === student.id))
                              .map(student => student.id);
                            if (studentIds.length > 0) {
                              manageCourseStudents(course.id, studentIds, 'add').then(() => {
                                loadCourseStudents();
                                toast.success(`${studentIds.length} students added from ${educationGroups.find(g => g.id === selectedEducationGroupForStudents)?.group_name}`);
                              }).catch(() => {
                                toast.error('Failed to add students from group');
                              });
                            }
                          }
                        }}
                        disabled={!groupStudents.some(student => !courseStudents.some(cs => cs.student_id === student.id))}
                      >
                        Add All Available ({groupStudents.filter(student => !courseStudents.some(cs => cs.student_id === student.id)).length})
                      </Button>
                    )}
                  </div>
                  
                  {/* Currently Enrolled Students */}
                  {courseStudents.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">Currently Enrolled Students ({courseStudents.length})</Label>
                      <div className="space-y-2 max-h-48 overflow-y-auto border rounded p-2">
                        {courseStudents.map((student) => (
                          <div key={student.id} className="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded">
                            <div>
                              <p className="font-medium text-blue-800">{student.name || student.student?.name || student.student?.full_name || `Student ${student.student_id}`}</p>
                              <div className="flex gap-2 text-xs text-blue-600">
                                <span>ID: {student.student_id_number || student.student?.student_id_number || student.student_id}</span>
                                {student.enrollment_date && (
                                  <span>Enrolled: {new Date(student.enrollment_date).toLocaleDateString()}</span>
                                )}
                              </div>
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => handleRemoveStudent(student.student_id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Add Individual Students from Other Classes */}
                  <div className="space-y-2">
                    <Label htmlFor="student-search">Add Individual Students</Label>
                    <div className="flex gap-2">
                      <div className="flex-1 relative">
                        <Input
                          id="student-search"
                          placeholder="Search students from all classes..."
                          value={studentSearchTerm}
                          onChange={(e) => setStudentSearchTerm(e.target.value)}
                        />
                        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      </div>
                      <Select
                        value={selectedEducationGroupForStudents?.toString() || 'all'}
                        onValueChange={(value) => {
                          setSelectedEducationGroupForStudents(value === 'all' ? null : parseInt(value));
                          if (studentSearchTerm.length >= 2) {
                            searchAvailableStudents(studentSearchTerm);
                          }
                        }}
                      >
                        <SelectTrigger className="w-48">
                          <SelectValue placeholder="Filter by group" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Groups</SelectItem>
                          {educationGroups.map((group) => (
                            <SelectItem key={group.id} value={group.id.toString()}>
                              {group.group_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {availableStudents.length > 0 && (
                      <Card className="max-h-60 overflow-y-auto">
                        <CardContent className="p-0">
                          {availableStudents.map((student) => (
                            <div
                              key={student.id}
                              className="flex items-center justify-between p-3 hover:bg-gray-50 border-b last:border-b-0"
                            >
                              <div>
                                <p className="font-medium">{student.name || student.full_name}</p>
                                <div className="flex gap-2 text-sm text-gray-500">
                                  <span>ID: {student.student_id_number || student.student_number}</span>
                                  {student.education_group_name && (
                                    <span>Group: {student.education_group_name}</span>
                                  )}
                                </div>
                              </div>
                              <Button
                                type="button"
                                size="sm"
                                onClick={() => handleAddStudent(student.id)}
                              >
                                <Plus className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Schedule Tab */}
            <TabsContent value="schedule" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Course Hours
                  </CardTitle>
                  <CardDescription>
                    Define the time allocation for different types of classes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="m_hours">Lecture Hours</Label>
                      <Input
                        id="m_hours"
                        type="number"
                        min="0"
                        {...register('m_hours', { valueAsNumber: true })}
                        placeholder="0"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="s_hours">Seminar Hours</Label>
                      <Input
                        id="s_hours"
                        type="number"
                        min="0"
                        {...register('s_hours', { valueAsNumber: true })}
                        placeholder="0"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="l_hours">Lab Hours</Label>
                      <Input
                        id="l_hours"
                        type="number"
                        min="0"
                        {...register('l_hours', { valueAsNumber: true })}
                        placeholder="0"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="fm_hours">Practical Hours</Label>
                      <Input
                        id="fm_hours"
                        type="number"
                        min="0"
                        {...register('fm_hours', { valueAsNumber: true })}
                        placeholder="0"
                      />
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-muted rounded-lg">
                    <p className="text-sm font-medium">Total Hours: {
                      (watch('m_hours') || 0) + 
                      (watch('s_hours') || 0) + 
                      (watch('l_hours') || 0) + 
                      (watch('fm_hours') || 0)
                    }</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Settings Tab */}
            <TabsContent value="settings" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="h-5 w-5" />
                      Language & Semester
                    </CardTitle>
                    <CardDescription>
                      Course language and semester settings
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="education_language_id">Education Language</Label>
                      <Controller
                        name="education_language_id"
                        control={control}
                        render={({ field }) => (
                          <Select
                            value={field.value?.toString() || ''}
                            onValueChange={(value) => field.onChange(value ? parseInt(value) : undefined)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select language" />
                            </SelectTrigger>
                            <SelectContent>
                              {educationLanguages.map((language) => (
                                <SelectItem key={language.id} value={language.id.toString()}>
                                  <div className="flex items-center gap-2">
                                    {language.language_code && <Badge variant="outline">{language.language_code}</Badge>}
                                    {language.language_name}
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="semester_id">Semester</Label>
                      <Controller
                        name="semester_id"
                        control={control}
                        render={({ field }) => (
                          <Select
                            value={field.value?.toString() || ''}
                            onValueChange={(value) => field.onChange(value ? parseInt(value) : undefined)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select semester" />
                            </SelectTrigger>
                            <SelectContent>
                              {semesters.map((semester) => (
                                <SelectItem key={semester.id} value={semester.id.toString()}>
                                  <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4" />
                                    {semester.semester_name}
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle>Preview</CardTitle>
                    <CardDescription>
                      Course information preview
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Course Code:</span>
                        <span className="text-sm">{watch('code') || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Total Hours:</span>
                        <span className="text-sm">
                          {(watch('m_hours') || 0) + (watch('s_hours') || 0) + 
                           (watch('l_hours') || 0) + (watch('fm_hours') || 0)}
                        </span>
                      </div>
                      {watch('start_date') && (
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Start Date:</span>
                          <span className="text-sm">{watch('start_date')}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
          
          {/* Action Buttons */}
          <div className="flex justify-between pt-6 border-t">
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCurrentTab('basic')}
                disabled={currentTab === 'basic'}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  const tabs = ['basic', 'assignment', 'schedule', 'settings'];
                  const currentIndex = tabs.indexOf(currentTab);
                  if (currentIndex < tabs.length - 1) {
                    setCurrentTab(tabs[currentIndex + 1]);
                  }
                }}
                disabled={currentTab === 'settings'}
              >
                Next
              </Button>
            </div>
            
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : (isEditMode ? 'Update Course' : 'Create Course')}
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}