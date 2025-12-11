'use client';

import { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useForm, Controller } from 'react-hook-form';
import { 
  CourseInfo, 
  CourseCreate, 
  CourseUpdate,
  TeacherInfo,
  CourseStudentInfo,
  AvailableStudent,
  SubjectInfo,
  createCourse, 
  updateCourse,
  getTeachers,
  getStudents,
  getSubjects,
  getCourseTeachers,
  getCourseStudents,
  assignTeacher,
  enrollStudent,
  removeTeacher,
  removeStudent
} from '@/lib/api/class-schedule';

// Form data interface that matches the actual form fields
interface CourseFormData {
  course_name?: string;
  course_code: string;
  description?: string;
  credits?: number;
  semester_id?: number;
  education_group_id?: number;
  subject_id?: number;
  subject_name?: string;
  education_language_id?: number;
  start_date?: string;
  student_count?: number;
  m_hours?: number;
  s_hours?: number;
  l_hours?: number;
  fm_hours?: number;
  note?: string;
  is_active?: boolean;
}
import { toast } from 'sonner';

interface CourseEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  course?: CourseInfo | null; // null for new course
  onSave: (course: CourseInfo) => void;
}

export function CourseEditModal({ isOpen, onClose, course, onSave }: CourseEditModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<{teachers: TeacherInfo[], students: AvailableStudent[]}>({
    teachers: [],
    students: []
  });
  const [assignedTeachers, setAssignedTeachers] = useState<TeacherInfo[]>([]);
  const [enrolledStudents, setEnrolledStudents] = useState<CourseStudentInfo[]>([]);
  const [availableSubjects, setAvailableSubjects] = useState<SubjectInfo[]>([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>('');
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  
  // Add loading states for search
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Add search states
  const [teacherSearch, setTeacherSearch] = useState('');
  const [studentSearch, setStudentSearch] = useState('');

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<CourseFormData>();

  // Search for teachers with debounce
  const searchTeachers = useCallback(async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setSearchResults(prev => ({ ...prev, teachers: [] }));
      return;
    }
    
    setSearchLoading(true);
    try {
      const allTeachers = await getTeachers();
      const filtered = allTeachers.filter((teacher: TeacherInfo) => 
        (teacher.name && teacher.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (teacher.organization && teacher.organization.toLowerCase().includes(searchTerm.toLowerCase()))
      ).slice(0, 20); // Limit to first 20 results
      
      setSearchResults(prev => ({ ...prev, teachers: filtered }));
    } catch (error) {
      console.error('Failed to search teachers:', error);
      toast.error('Failed to search teachers');
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Search for students with debounce
  const searchStudents = useCallback(async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setSearchResults(prev => ({ ...prev, students: [] }));
      return;
    }
    
    setSearchLoading(true);
    try {
      const allStudents = await getStudents();
      const filtered = allStudents.filter((student: CourseStudentInfo) =>
        (student.name && student.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (student.full_name && student.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (student.student_id_number && student.student_id_number.toString().includes(searchTerm)) ||
        (student.student_number && student.student_number.toString().includes(searchTerm))
      ).slice(0, 20); // Limit to first 20 results
      
      setSearchResults(prev => ({ ...prev, students: filtered }));
    } catch (error) {
      console.error('Failed to search students:', error);
      toast.error('Failed to search students');
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Debounced search effect for teachers
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (teacherSearch) {
        searchTeachers(teacherSearch);
      }
    }, 500);

    return () => clearTimeout(delayedSearch);
  }, [teacherSearch, searchTeachers]);

  // Debounced search effect for students
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (studentSearch) {
        searchStudents(studentSearch);
      }
    }, 500);

    return () => clearTimeout(delayedSearch);
  }, [studentSearch, searchStudents]);

  // Load course assignments
  const loadCourseAssignments = useCallback(async () => {
    if (!course?.id) return;
    
    try {
      const [teachers, students] = await Promise.all([
        getCourseTeachers(course.id),
        getCourseStudents(course.id)
      ]);
      setAssignedTeachers(teachers);
      setEnrolledStudents(students);
    } catch (error) {
      console.error('Failed to load course assignments:', error);
    }
  }, [course?.id]);

  // Load available subjects
  const loadSubjects = useCallback(async () => {
    try {
      const subjects = await getSubjects();
      setAvailableSubjects(subjects);
    } catch (error) {
      console.error('Failed to load subjects:', error);
      toast.error('Failed to load subjects');
    }
  }, []);

  // Load data when modal opens
  useEffect(() => {
    if (isOpen) {
      // Load subjects
      loadSubjects();
      
      if (course) {
        // Editing existing course - map CourseInfo to form fields
        reset({
          course_name: course.course_name,
          course_code: course.course_code || course.code,
          description: course.description,
          credits: course.credits,
          semester_id: course.semester_id,
          education_group_id: course.education_group_id,
          subject_id: course.subject_id,
          education_language_id: course.education_language_id,
          is_active: course.is_active || course.active
        });
        loadCourseAssignments();
      } else {
        // Creating new course - use proper CourseCreate fields
        reset({
          course_name: '',
          course_code: '',
          description: '',
          credits: 0,
          semester_id: 0,
          education_group_id: 0,
          subject_id: 0,
          education_language_id: 0
        });
        setAssignedTeachers([]);
        setEnrolledStudents([]);
      }
    } else {
      // Clean up when modal closes
      setSearchResults({ teachers: [], students: [] });
      setTeacherSearch('');
      setStudentSearch('');
      setSelectedTeacherId('');
      setSelectedStudentId('');
    }
  }, [isOpen, course, reset, loadCourseAssignments, loadSubjects]);

  const onSubmit = async (data: CourseFormData) => {
    setIsLoading(true);
    try {
      let savedCourse: CourseInfo;
      
      // Map form data to API interface
      const apiData: CourseCreate | CourseUpdate = {
        course_name: data.course_name || '',
        course_code: data.course_code,
        description: data.description,
        credits: data.credits || 0,
        semester_id: data.semester_id || 0,
        education_group_id: data.education_group_id || 0,
        subject_id: data.subject_id || 0,
        education_language_id: data.education_language_id || 0,
      };

      if (course) {
        // Update existing course
        if (!course.id) {
          throw new Error('Course ID is required for updates');
        }
        savedCourse = await updateCourse(course.id, apiData as CourseUpdate);
        toast.success('Course updated successfully');
      } else {
        // Create new course
        savedCourse = await createCourse(apiData as CourseCreate);
        toast.success('Course created successfully');
      }
      
      onSave(savedCourse);
      onClose();
    } catch (error) {
      console.error('Failed to save course:', error);
      toast.error(`Failed to ${course ? 'update' : 'create'} course`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssignTeacher = async () => {
    if (!selectedTeacherId || !course?.id) return;
    
    try {
      await assignTeacher(course.id, parseInt(selectedTeacherId));
      setSelectedTeacherId('');
      loadCourseAssignments();
      toast.success('Teacher assigned successfully');
    } catch (error) {
      console.error('Failed to assign teacher:', error);
      toast.error('Failed to assign teacher');
    }
  };

  const handleRemoveTeacher = async (teacherId: string | number) => {
    if (!course?.id) return;
    
    try {
      await removeTeacher(course.id, teacherId);
      loadCourseAssignments();
      toast.success('Teacher removed successfully');
    } catch (error) {
      console.error('Failed to remove teacher:', error);
      toast.error('Failed to remove teacher');
    }
  };

  const handleEnrollStudent = async () => {
    if (!selectedStudentId || !course?.id) return;
    
    try {
      await enrollStudent(course.id, parseInt(selectedStudentId));
      setSelectedStudentId('');
      loadCourseAssignments();
      toast.success('Student enrolled successfully');
    } catch (error) {
      console.error('Failed to enroll student:', error);
      toast.error('Failed to enroll student');
    }
  };

  const handleRemoveStudent = async (studentId: string | number) => {
    if (!course?.id) return;
    
    try {
      await removeStudent(course.id, studentId);
      loadCourseAssignments();
      toast.success('Student removed successfully');
    } catch (error) {
      console.error('Failed to remove student:', error);
      toast.error('Failed to remove student');
    }
  };

  // Get available teachers from search results, excluding already assigned ones
  const availableTeachers = searchResults.teachers.filter(
    teacher => !assignedTeachers.some(assigned => assigned.id === teacher.id)
  );

  // Get available students from search results, excluding already enrolled ones
  const availableStudents = searchResults.students.filter(
    student => !enrolledStudents.some(enrolled => enrolled.id === student.id)
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {course ? 'Edit Course' : 'Create New Course'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Course Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="course_code">Course Code *</Label>
              <Input
                id="course_code"
                {...register('course_code', { required: 'Course code is required' })}
                placeholder="Enter course code"
              />
              {errors.course_code && (
                <p className="text-sm text-red-500 mt-1">{errors.course_code.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="subject_name">Subject</Label>
              <Controller
                name="subject_name"
                control={control}
                render={({ field }) => (
                  <Select value={field.value || ''} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a subject" />
                    </SelectTrigger>
                    <SelectContent className="max-h-64">
                      {availableSubjects.map((subject) => (
                        <SelectItem key={subject.id} value={subject.subject_name}>
                          {subject.subject_name} {subject.subject_code && `(${subject.subject_code})`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="start_date">Start Date</Label>
              <Input
                id="start_date"
                type="date"
                {...register('start_date')}
              />
            </div>
            
            <div>
              <Label htmlFor="student_count">Expected Student Count</Label>
              <Input
                id="student_count"
                type="number"
                min="0"
                {...register('student_count', { valueAsNumber: true })}
                placeholder="Expected number of students"
              />
            </div>
          </div>

          {/* Hours Configuration */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="m_hours">Monthly Hours</Label>
              <Input
                id="m_hours"
                type="number"
                min="0"
                {...register('m_hours', { valueAsNumber: true })}
              />
            </div>

            <div>
              <Label htmlFor="s_hours">Semester Hours</Label>
              <Input
                id="s_hours"
                type="number"
                min="0"
                {...register('s_hours', { valueAsNumber: true })}
              />
            </div>

            <div>
              <Label htmlFor="l_hours">Lecture Hours</Label>
              <Input
                id="l_hours"
                type="number"
                min="0"
                {...register('l_hours', { valueAsNumber: true })}
              />
            </div>

            <div>
              <Label htmlFor="fm_hours">Final Hours</Label>
              <Input
                id="fm_hours"
                type="number"
                min="0"
                {...register('fm_hours', { valueAsNumber: true })}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="note">Notes</Label>
            <Textarea
              id="note"
              {...register('note')}
              placeholder="Additional notes about the course"
              rows={3}
            />
          </div>

          {/* Teacher Assignments (only for existing courses) */}
          {course && (
            <div className="space-y-4">
              <h3 className="font-semibold">Assigned Teachers</h3>
              
              {/* Search and Add Teacher */}
              <div className="space-y-2">
                <Input
                  placeholder="Search teachers by name or organization..."
                  value={teacherSearch}
                  onChange={(e) => setTeacherSearch(e.target.value)}
                />
                {teacherSearch.length >= 2 && (
                  <div className="flex gap-2">
                    <Select value={selectedTeacherId} onValueChange={setSelectedTeacherId}>
                      <SelectTrigger className="flex-1">
                        <SelectValue placeholder="Select teacher to assign" />
                      </SelectTrigger>
                      <SelectContent>
                        {searchLoading ? (
                          <SelectItem value="loading" disabled>Loading...</SelectItem>
                        ) : (
                          availableTeachers.map((teacher) => (
                            <SelectItem key={teacher.id} value={teacher.id.toString()}>
                              {teacher.name} - {teacher.organization}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    <Button 
                      type="button" 
                      onClick={handleAssignTeacher}
                      disabled={!selectedTeacherId}
                    >
                      Assign
                    </Button>
                  </div>
                )}
              </div>

              {/* Assigned Teachers List */}
              <div className="space-y-2">
                {assignedTeachers.map((teacher) => (
                  <div key={teacher.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span>{teacher.name} - {teacher.organization}</span>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRemoveTeacher(teacher.id)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Student Enrollments (only for existing courses) */}
          {course && (
            <div className="space-y-4">
              <h3 className="font-semibold">Enrolled Students</h3>
              
              {/* Search and Add Student */}
              <div className="space-y-2">
                <Input
                  placeholder="Search students by name or ID..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                />
                {studentSearch.length >= 2 && (
                  <div className="flex gap-2">
                    <Select value={selectedStudentId} onValueChange={setSelectedStudentId}>
                      <SelectTrigger className="flex-1">
                        <SelectValue placeholder="Select student to enroll" />
                      </SelectTrigger>
                      <SelectContent>
                        {searchLoading ? (
                          <SelectItem value="loading" disabled>Loading...</SelectItem>
                        ) : (
                          availableStudents.map((student) => (
                            <SelectItem key={student.id} value={student.id.toString()}>
                              {student.name} - ID: {student.student_id_number || 'N/A'}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    <Button 
                      type="button" 
                      onClick={handleEnrollStudent}
                      disabled={!selectedStudentId}
                    >
                      Enroll
                    </Button>
                  </div>
                )}
              </div>

              {/* Enrolled Students List */}
              <div className="space-y-2">
                {enrolledStudents.map((student) => (
                  <div key={student.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span>{student.name || `Student ID: ${student.student_id_number}`}</span>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRemoveStudent(student.id)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : course ? 'Update Course' : 'Create Course'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}