/**
 * TypeScript interfaces for Education Plan data
 */

export interface EducationPlanSubject {
  id: string;
  code: string;
  subject_name_az?: string;
  credit: string;
  all_hours: string;
  out_hours: string;
  in_hours: string;
  m_hours?: string;
  s_hours?: string;
  l_hours?: string;
  fm_hours?: string;
  m_week_charge?: string;
  s_week_charge?: string;
  l_week_charge?: string;
  week_charge?: number;
  fm_week_charge?: string;
  semester_name_az?: string;
  course_work: string;
  department_name_az?: string;
  chosen_status: string;
  create_date: string;
}

export interface EducationPlanStats {
  total_subjects: number;
  total_credits: number;
  total_hours: number;
  subjects_by_semester: Record<string, number>;
  subjects_by_department: Record<string, number>;
}

export interface EducationPlan {
  id: string;
  code?: string;
  name?: string | {
    az?: string;
    en?: string;
    ru?: string;
  };
  degree_type?: string;
  duration_years?: number;
  total_credits?: number;
  organization_unit_id?: string;
  language_of_instruction?: string[];
  is_active?: boolean;
  created_at?: string;
  // Legacy fields for backward compatibility
  organization_id?: string;
  education_type_id?: string;
  education_level_id?: string;
  total_subjects?: number;
}

export interface EducationPlanDetail {
  id: string;
  name?: string;
  organization_id?: string;
  education_type_id?: string;
  education_level_id?: string;
  status?: string;
  active: boolean;
  create_date?: string;
  total_subjects?: number;
}

export interface EducationPlanUpdate {
  name?: string;
  active?: boolean;
}

export interface EducationPlanOverallStats {
  total_education_plans: number;
  total_subjects: number;
  plans_by_year: Record<string, number>;
}

// Form interfaces for editing
export interface EducationPlanSubjectFormData {
  code: string;
  subject_name_az: string;
  credit: string;
  out_hours: string;
  in_hours: string;
  m_hours: string;
  s_hours: string;
  l_hours: string;
  fm_hours: string;
  course_work: string;
  chosen_status: string;
}

// API response types
export interface EducationPlansResponse {
  plans: EducationPlan[];
  total: number;
  page: number;
  limit: number;
}

export interface EducationPlanSubjectsResponse {
  subjects: EducationPlanSubject[];
  total: number;
  page: number;
  limit: number;
}

// Filter and search types
export interface EducationPlanFilters {
  semester_id?: string;
  search?: string;
  department?: string;
  credit_range?: [number, number];
  hours_range?: [number, number];
}

export interface SemesterOption {
  id: string;
  name_az: string;
  name_en?: string;
}

export interface DepartmentOption {
  id: string;
  name_az: string;
  name_en?: string;
}

// Table column definitions for data display
export interface SubjectTableColumn {
  key: keyof EducationPlanSubject;
  label: string;
  sortable?: boolean;
  searchable?: boolean;
  type?: 'text' | 'number' | 'date';
  format?: (value: unknown) => string;
}

// Subject hour breakdown for detailed view
export interface SubjectHourBreakdown {
  total_hours: number;
  in_hours: number;
  out_hours: number;
  lecture_hours?: number; // m_hours
  seminar_hours?: number; // s_hours
  lab_hours?: number; // l_hours
  final_hours?: number; // fm_hours
}

export interface SubjectWeeklyCharge {
  total_weekly: number;
  lecture_weekly?: number; // m_week_charge
  seminar_weekly?: number; // s_week_charge
  lab_weekly?: number; // l_week_charge
  final_weekly?: number; // fm_week_charge
}

export interface DetailedSubjectView extends EducationPlanSubject {
  hours_breakdown: SubjectHourBreakdown;
  weekly_charge: SubjectWeeklyCharge;
  has_course_work: boolean;
  is_chosen: boolean;
}