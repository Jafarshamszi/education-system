/**
 * Teacher-related TypeScript types for the Education System
 * Updated to match the new LMS API schema (staff_members table)
 */

export interface PersonInfo {
  id: string;  // UUID
  first_name: string;
  last_name: string;
  middle_name?: string | null;
  full_name: string;
}

export interface OrganizationInfo {
  id: string;  // UUID
  name: string | { az: string; en: string; ru: string };
  code?: string | null;
}

export interface Teacher {
  id: string;  // UUID
  employee_number: string;
  person: PersonInfo | null;
  position_title?: string | { az: string; en: string; ru: string } | null;
  employment_type?: string | null;
  academic_rank?: string | { az: string; en: string; ru: string } | null;
  organization: OrganizationInfo | null;
  is_active: boolean;
  hire_date?: string | null;  // ISO date string
}

export interface TeacherListResponse {
  count: number;
  total_pages: number;
  current_page: number;
  per_page: number;
  results: Teacher[];
}

export interface TeacherStatsResponse {
  total_teachers: number;
  active_teachers: number;
  organizations_count: number;
}
