'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Clock, Users, GraduationCap, BookOpen, Calendar, Loader2 } from 'lucide-react';

import { getCourseTeachers, getCourseStudents, type CourseInfo, type TeacherInfo, type CourseStudentInfo } from '@/lib/api/class-schedule';

interface CourseDetailsModalProps {
  course: CourseInfo;
  children: React.ReactNode;
}

export default function CourseDetailsModal({ course, children }: CourseDetailsModalProps) {
  const [teachers, setTeachers] = useState<TeacherInfo[]>([]);
  const [students, setStudents] = useState<CourseStudentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  // Debug state changes
  useEffect(() => {
    console.log('Teachers state updated:', teachers, 'Length:', teachers.length);
  }, [teachers]);

  useEffect(() => {
    console.log('Students state updated:', students, 'Length:', students.length);
  }, [students]);

  const loadCourseDetails = async (courseId: number | string) => {
    if (!courseId) {
      console.warn('Course ID is missing');
      return;
    }
    
    const id = typeof courseId === 'string' ? parseInt(courseId) : courseId;
    
    try {
      setLoading(true);
      setError(null);
      
      console.log('Loading course details for ID:', id);
      
      const [teacherData, studentData] = await Promise.all([
        getCourseTeachers(id),
        getCourseStudents(id)
      ]);
      
      console.log('Loaded teachers:', teacherData, 'Count:', teacherData.length);
      console.log('Loaded students:', studentData, 'Count:', studentData.length);
      
      // Add state update validation
      console.log('Setting teachers state with', teacherData.length, 'items');
      setTeachers(teacherData);
      
      console.log('Setting students state with', studentData.length, 'items');
      setStudents(studentData);
      
    } catch (err) {
      console.error('Failed to load course details:', err);
      setError('Failed to load course details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('Modal open state changed:', open);
    if (open && course?.id) {
      console.log('Reset state when opening modal');
      // Reset state when opening
      setTeachers([]);
      setStudents([]);
      setError(null);
      console.log('Calling loadCourseDetails with ID:', course.id);
      loadCourseDetails(course.id);
    }
  }, [open, course?.id]);

  const getTotalHours = () => {
    return (course.m_hours || 0) + (course.s_hours || 0) + (course.l_hours || 0) + (course.fm_hours || 0);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Not specified';
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <BookOpen className="h-6 w-6 text-blue-600" />
            <div>
              <div className="font-mono text-lg">{course.course_code}</div>
              {course.subject?.subject_name && (
                <div className="text-sm font-normal text-gray-600 mt-1">
                  {course.subject.subject_name}
                </div>
              )}
            </div>
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading course details...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {/* Course Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-orange-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Hours</p>
                      <p className="text-lg font-bold">{getTotalHours()}h</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Users className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Enrolled Students</p>
                      <p className="text-lg font-bold">{students.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <GraduationCap className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Assigned Teachers</p>
                      <p className="text-lg font-bold">{teachers.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Start Date</p>
                      <p className="text-sm font-bold">{formatDate(course.start_date || null)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Hours Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Hours Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{course.m_hours || 0}</p>
                    <p className="text-sm text-blue-800">Lecture Hours</p>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{course.s_hours || 0}</p>
                    <p className="text-sm text-green-800">Seminar Hours</p>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">{course.l_hours || 0}</p>
                    <p className="text-sm text-purple-800">Lab Hours</p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-600">{course.fm_hours || 0}</p>
                    <p className="text-sm text-orange-800">Final Hours</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Teachers and Students Tabs */}
            <Tabs defaultValue="teachers" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="teachers" className="flex items-center gap-2">
                  <GraduationCap className="h-4 w-4" />
                  Teachers ({teachers.length})
                </TabsTrigger>
                <TabsTrigger value="students" className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Students ({students.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="teachers" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Assigned Teachers</CardTitle>
                    <CardDescription>
                      Teachers responsible for conducting this course
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {teachers.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Teacher Name</TableHead>
                            <TableHead>Organization</TableHead>
                            <TableHead>Lesson Type</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {teachers.map((teacher, index) => (
                            <TableRow key={`teacher-${teacher.id}-${index}`}>
                              <TableCell className="font-medium">
                                {teacher.name || 'N/A'}
                              </TableCell>
                              <TableCell>
                                {teacher.organization || 'N/A'}
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">
                                  {teacher.lesson_type || 'N/A'}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <div>
                        <p className="text-gray-500 text-center py-8">No teachers assigned</p>
                        <p className="text-xs text-gray-400 text-center">Teachers array length: {teachers.length}</p>
                        <p className="text-xs text-gray-400 text-center">Teachers data: {JSON.stringify(teachers)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="students" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Enrolled Students</CardTitle>
                    <CardDescription>
                      Students currently enrolled in this course
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {students.length > 0 ? (
                      <div className="max-h-96 overflow-y-auto">
                        <Table>
                          <TableHeader className="sticky top-0 bg-white">
                            <TableRow>
                              <TableHead>Student Name</TableHead>
                              <TableHead>Student ID</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {students.map((courseStudent, index) => (
                              <TableRow key={`student-${courseStudent.id}-${index}`}>
                                <TableCell className="font-medium">
                                  {courseStudent.name || 'N/A'}
                                </TableCell>
                                <TableCell>
                                  <span className="font-mono text-sm">
                                    {courseStudent.student_id_number || 'N/A'}
                                  </span>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div>
                        <p className="text-gray-500 text-center py-8">No students enrolled</p>
                        <p className="text-xs text-gray-400 text-center">Students array length: {students.length}</p>
                        <p className="text-xs text-gray-400 text-center">Students data: {JSON.stringify(students)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}