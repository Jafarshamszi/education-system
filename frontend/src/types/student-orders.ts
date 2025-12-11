// Student Orders Types
// Based on database analysis and API responses

export interface OrderSummary {
  total_orders: number;
  active_orders: number;
  inactive_orders: number;
  total_students: number;
  total_relationships: number;
}

export interface OrderType {
  order_type: string;
  count: number;
  active_count: number;
}

export interface OrdersSummaryResponse {
  summary: OrderSummary;
  order_types: OrderType[];
}

export interface StudentOrder {
  id: string; // Changed from number to string to handle large integers
  serial: string;
  order_date: string | null;
  description: string | null;
  active: number;
  create_date?: string;
  update_date?: string;
  form_id?: string;
  file_id?: string;
  create_user_id?: string;
  
  // Order type/category
  order_type: string;
  order_type_en?: string;
  order_type_ru?: string;
  type_id: number;
  
  // Order status
  status?: string;
  status_az?: string;
  status_ru?: string;
  
  // Education level
  education_level?: string;
  education_level_az?: string;
  education_level_ru?: string;
  
  // Creator information
  creator_firstname?: string;
  creator_lastname?: string;
  creator_patronymic?: string;
  
  // File information (if available)
  file_info?: {
    file_id: string;
    filename?: string;
    original_filename?: string;
    file_size?: number;
    mime_type?: string;
    file_create_date?: string;
  };
  
  // For list view
  student_count?: number;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface OrdersListResponse {
  orders: StudentOrder[];
  pagination: PaginationInfo;
}

export interface Student {
  student_id: number;
  first_name: string;
  last_name: string;
  patronymic: string;
  pincode?: string;
  birthdate?: string;
  card_number?: string;
  score?: string;
  relationship_active: number;
  
  // Education group information
  group_name?: string;
  group_id?: string;
  group_education_level?: string;
  group_education_level_az?: string;
  
  // Student's major/specialty information
  student_major?: string;
  student_major_az?: string;
  student_education_line?: string;
  student_education_line_az?: string;
  
  // Group's major/specialty information
  group_major?: string;
  group_major_az?: string;
  
  // Academic specialization/organization (ixtisas)
  organization_id?: string;
  academic_specialization?: string;
  academic_specialization_az?: string;
  academic_specialization_ru?: string;
  specialization_type?: string;
  specialization_name_english?: string;
}

export interface TransferParameter {
  student_id: number;
  from_group_id: number;
  to_group_id: number;
  active: number;
  from_group_name: string;
  to_group_name: string;
}

export interface OrderDetailsResponse {
  order: StudentOrder;
  students: Student[];
  transfer_parameters: TransferParameter[];
}

export interface OrderCategory {
  id: number;
  category_name: string;
  order_count: number;
}

export interface OrderCategoriesResponse {
  categories: OrderCategory[];
}

export interface OrderFilters {
  page?: number;
  limit?: number;
  order_type?: string;
  active_only?: boolean;
  search?: string;
}

// Additional types for UI components
export interface OrderDetailsModalProps {
  orderId: string | null; // Changed from number to string
  isOpen: boolean;
  onClose: () => void;
}

export interface OrderFiltersState {
  search: string;
  selectedCategory: string;
  activeOnly: boolean;
  currentPage: number;
}