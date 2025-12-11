// Curriculum system TypeScript interfaces based on our database analysis

// JSONB multilingual field type
export type MultilingualText = string | { az?: string; en?: string; ru?: string };

export interface CurriculumStats {
  active_curricula: number;
  unique_subjects: number;
  total_subject_dictionary: number;
  active_courses: number;
  student_enrollments: number;
  teaching_assignments: number;
  organizations_with_curricula: number;
  total_teaching_hours: number;
  avg_course_hours: number;
  avg_students_per_course: number;
}

export interface CurriculumOverview {
  id: string; // UUID
  code: string;
  name: MultilingualText; // Can be string (from backend extraction) or JSONB object
  degree_type: string;
  total_credits: number;
  is_active: boolean;
  organization_name?: MultilingualText;
  subjects_count?: number;
  courses_count?: number;
  students_enrolled?: number;
  create_date?: string;
}

export interface CurriculumDetail {
  id: string; // UUID
  name: MultilingualText; // Can be string (from backend extraction) or JSONB object
  code?: string;
  degree_type?: string;
  total_credits?: number;
  total_hours?: number;
  is_active?: boolean;
  organization_name: MultilingualText;
  subjects_count: number;
  courses_count: number;
  create_date?: string;
}

export interface SubjectInfo {
  code: string;
  name_az: string;
  used_in_curricula: number;
}

export interface CurriculumSubject {
  subject_code: string;
  subject_name: MultilingualText; // Can be string or JSONB object
  create_date?: string;
}

export interface CurriculumFilters {
  limit?: number;
  offset?: number;
  search?: string;
  organization_id?: number;
}

export interface ApiResponse<T> {
  data: T;
  success?: boolean;
  message?: string;
}

// API Response types
export type CurriculumListResponse = CurriculumOverview[];
export type CurriculumDetailResponse = CurriculumDetail;
export type CurriculumStatsResponse = CurriculumStats;
export type TopSubjectsResponse = SubjectInfo[];
export type CurriculumSubjectsResponse = CurriculumSubject[];