/**
 * Student-related TypeScript types for the Education System
 * Updated to match the new LMS API schema
 */

export interface PersonInfo {
  id: string;
  first_name: string;
  last_name: string;
  middle_name?: string | null;
}

export interface AcademicProgramInfo {
  id: string;
  code: string;
  name: {
    az?: string;
    en?: string;
    ru?: string;
  };
}

export interface Student {
  id: string;
  student_number: string;
  person: PersonInfo | null;
  academic_program: AcademicProgramInfo | null;
  status: string;
  study_mode?: string | null;
  funding_type?: string | null;
  enrollment_date: string;
  expected_graduation_date?: string | null;
  gpa?: number | null;
  total_credits_earned: number;
}

export interface StudentsListResponse {
  count: number;
  total_pages: number;
  current_page: number;
  per_page: number;
  results: Student[];
}

export interface StudentStatsResponse {
  total_students: number;
  active_students: number;
  graduated_students: number;
  average_gpa?: number | null;
}

// For backward compatibility - same as Student
export type StudentDetailResponse = Student;

export interface StudentFilters {
  search?: string;
  status?: string;
  study_mode?: string;
  academic_program_id?: string;
  page: number;
  per_page: number;
}

export interface FilterOptions {
  statuses: string[];
  study_modes: string[];
  academic_programs: AcademicProgramInfo[];
}

// Legacy interface for backward compatibility - will be removed
export interface FormData {
  [key: string]: string | number | boolean | null | undefined;
}

// Dashboard-specific types
export interface CourseGrade {
  id: string;
  course_code: string;
  course_name: {
    az?: string;
    en?: string;
    ru?: string;
  };
  credit_hours: number;
  grade: string;
  grade_points: number;
  semester: string;
  academic_year: string;
}

export interface AttendanceRecord {
  id: string;
  course_code: string;
  course_name: string;
  date: string;
  status: 'present' | 'absent' | 'late' | 'excused';
}

export interface Event {
  id: string;
  title: string;
  description?: string;
  event_type: 'exam' | 'assignment' | 'lecture' | 'holiday' | 'other';
  start_date: string;
  end_date?: string;
  location?: string;
  course_code?: string;
}

export interface StudentDashboardData {
  student: Student;
  grades: CourseGrade[];
  upcoming_events: Event[];
  attendance_summary: {
    total_classes: number;
    attended: number;
    absent: number;
    late: number;
    attendance_percentage: number;
  };
  current_semester_stats: {
    enrolled_courses: number;
    completed_credits: number;
    gpa: number;
  };
}
