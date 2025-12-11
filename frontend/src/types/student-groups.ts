/**
 * TypeScript interfaces for Student Groups
 * Matching the backend Pydantic models
 */

export interface StudentInfo {
  id: string;
  firstname?: string;
  lastname?: string;
  pincode?: string;
  user_id?: string;
  joined_group_date?: string;
}

export interface StudentGroup {
  id: string;
  group_name?: string;
  student_count: number;
  organization_name?: string;
  education_level?: string;
  education_type?: string;
  language?: string;
  tutor_firstname?: string;
  tutor_lastname?: string;
  tutor_full_name?: string;
  create_date?: string;
  organization_id?: string;
  education_level_id?: string;
  education_type_id?: string;
  education_lang_id?: string;
  tyutor_id?: string;
}

export interface StudentGroupDetail {
  id: string;
  group_name?: string;
  student_count: number;
  organization_name?: string;
  education_level?: string;
  education_type?: string;
  language?: string;
  tutor_full_name?: string;
  create_date?: string;
  students: StudentInfo[];
}

export interface StudentGroupStats {
  total_groups: number;
  total_students: number;
  average_group_size: number;
  groups_by_education_type?: Record<string, number>;
  groups_by_education_level?: Record<string, number>;
  groups_by_organization?: Record<string, number>;
}

export interface StudentGroupsFilters {
  search?: string;
  organization?: string;
  education_type?: string;
  education_level?: string;
  limit?: number;
  offset?: number;
}

export interface StudentGroupsResponse {
  data: StudentGroup[];
  total: number;
  page: number;
  limit: number;
}