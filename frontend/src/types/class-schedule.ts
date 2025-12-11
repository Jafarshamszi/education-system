// Class Schedule TypeScript interfaces matching the backend FastAPI models

export interface Course {
  id: number;
  code: string;
  start_date: string | null;
  m_hours: number; // Main/Lecture hours
  s_hours: number; // Seminar hours
  l_hours: number; // Lab hours
  fm_hours: number; // Final/Exam hours
  student_count: number;
  subject_name: string | null;
  subject_code: string | null;
  enrolled_students: number;
  assigned_teachers: number;
  active: boolean;
}

export interface Teacher {
  course_code: string;
  teacher_name: string;
  organization_name: string | null;
  position_name: string | null;
  lesson_type_name: string | null;
}

export interface Student {
  course_code: string;
  student_name: string;
  student_id_number: number | null;
}

export interface ScheduleStats {
  total_courses: number;
  total_students: number;
  total_teachers: number;
  active_periods: number;
}

// Extended types for UI components
export interface CourseWithDetails extends Course {
  teachers: Teacher[];
  students: Student[];
  total_hours: number;
}

export interface CourseFilterOptions {
  search: string;
  organization: string;
  lesson_type: string;
  hours_range: {
    min: number;
    max: number;
  };
}

// Utility types for schedule grid display
export interface ScheduleGridItem {
  course: Course;
  teachers: Teacher[];
  student_count: number;
  status: 'active' | 'inactive';
}

export interface TeacherAssignment {
  teacher_name: string;
  course_code: string;
  organization_name: string;
  lesson_type: string;
  total_courses: number;
}

// Response types for API calls
export interface CoursesResponse {
  courses: Course[];
  total: number;
  page: number;
  limit: number;
}

export interface TeachersResponse {
  teachers: Teacher[];
  total: number;
}

export interface StudentsResponse {
  students: Student[];
  total: number;
}

// Form types for filtering and search
export interface ScheduleFilters {
  searchTerm: string;
  startDate: string;
  endDate: string;
  minHours: number;
  maxHours: number;
  organizationFilter: string;
  lessonTypeFilter: string;
}

export interface SortOptions {
  field: keyof Course;
  direction: 'asc' | 'desc';
}

// Calendar view types
export interface ScheduleCalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  course_code: string;
  teacher_name: string;
  type: 'lecture' | 'seminar' | 'lab' | 'exam';
}