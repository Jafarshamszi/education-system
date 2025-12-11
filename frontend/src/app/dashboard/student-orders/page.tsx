"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Filter, 
  FileText, 
  Users, 
  Calendar,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  ArrowUpDown,
  ClipboardList
} from 'lucide-react';
import axios from 'axios';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import {
  OrdersSummaryResponse,
  OrdersListResponse,
  OrderDetailsResponse,
  OrderCategoriesResponse,
  OrderFilters,
  StudentOrder,
  OrderCategory
} from '@/types/student-orders';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function StudentOrdersPage() {
  // State management
  const [summary, setSummary] = useState<OrdersSummaryResponse | null>(null);
  const [orders, setOrders] = useState<StudentOrder[]>([]);
  const [categories, setCategories] = useState<OrderCategory[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<OrderDetailsResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter state
  const [filters, setFilters] = useState<OrderFilters>({
    page: 1,
    limit: 20,
    order_type: '',
    active_only: true,
    search: ''
  });
  
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    total_pages: 0
  });

  // Fetch data functions
  const fetchSummary = async () => {
    try {
      const response = await axios.get<OrdersSummaryResponse>(
        `${API_BASE_URL}/student-orders/orders/summary`
      );
      setSummary(response.data);
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError('Failed to fetch orders summary');
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get<OrderCategoriesResponse>(
        `${API_BASE_URL}/student-orders/orders/categories`
      );
      setCategories(response.data.categories || []);
    } catch (err) {
      console.error('Error fetching categories:', err);
      setCategories([]);
    }
  };

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.order_type) params.append('order_type', filters.order_type);
      if (filters.active_only !== undefined) params.append('active_only', filters.active_only.toString());
      if (filters.search) params.append('search', filters.search);
      
      const response = await axios.get<OrdersListResponse>(
        `${API_BASE_URL}/student-orders/orders/list?${params}`
      );
      
      setOrders(response.data.orders || []);
      setPagination(response.data.pagination || {
        page: 1,
        limit: 20,
        total: 0,
        total_pages: 0
      });
    } catch (err) {
      console.error('Error fetching orders:', err);
      setError('Failed to fetch orders');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetails = async (orderId: string) => {
    try {
      const response = await axios.get<OrderDetailsResponse>(
        `${API_BASE_URL}/student-orders/orders/${orderId}`
      );
      setSelectedOrder(response.data);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Error fetching order details:', err);
      setError('Failed to fetch order details');
    }
  };

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      await Promise.all([
        fetchSummary(),
        fetchCategories(),
        fetchOrders()
      ]);
    };
    
    loadInitialData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Refetch orders when filters change
  useEffect(() => {
    fetchOrders();
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  // Filter handlers
  const handleSearchChange = (value: string) => {
    setFilters(prev => ({ ...prev, search: value, page: 1 }));
  };

  const handleCategoryChange = (value: string) => {
    setFilters(prev => ({ 
      ...prev, 
      order_type: value === 'all' ? '' : value, 
      page: 1 
    }));
  };

  const handleActiveToggle = (activeOnly: boolean) => {
    setFilters(prev => ({ ...prev, active_only: activeOnly, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  // Format date helper
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date';
    try {
      // Handle different date formats
      if (dateString.includes('/')) {
        // Format: DD/MM/YYYY
        const [day, month, year] = dateString.split('/');
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      } else {
        return new Date(dateString).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      }
    } catch {
      return dateString; // Return original string if parsing fails
    }
  };

  if (loading && orders.length === 0) {
    return (
      <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN', 'SYSADMIN']}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading student orders...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN', 'SYSADMIN']}>
      <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Student Orders</h1>
              <p className="text-muted-foreground">
                Manage and view all student orders, transfers, and administrative actions
              </p>
            </div>
          </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Summary Statistics */}
        {summary && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.summary.total_orders}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {summary.summary.active_orders}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Inactive Orders</CardTitle>
                <XCircle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {summary.summary.inactive_orders}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Students Involved</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.summary.total_students}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Relationships</CardTitle>
                <ClipboardList className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.summary.total_relationships}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters and Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters & Search
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by order serial or description..."
                    value={filters.search || ''}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              {/* Category Filter */}
              <Select
                value={filters.order_type || 'all'}
                onValueChange={handleCategoryChange}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories?.map((category) => (
                    <SelectItem key={category.id} value={category.category_name}>
                      {category.category_name} ({category.order_count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Active Filter */}
              <Select
                value={filters.active_only ? 'active' : 'all'}
                onValueChange={(value) => handleActiveToggle(value === 'active')}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active Only</SelectItem>
                  <SelectItem value="all">All Status</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Orders Table */}
        <Card>
          <CardHeader>
            <CardTitle>Orders List</CardTitle>
            <p className="text-sm text-muted-foreground">
              Showing {orders.length} of {pagination?.total || 0} orders
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {orders.map((order) => (
                <Card key={order.id} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent 
                    className="p-4"
                    onClick={() => fetchOrderDetails(order.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold">Order #{order.serial}</h3>
                          <Badge variant={order.active ? "default" : "secondary"}>
                            {order.active ? "Active" : "Inactive"}
                          </Badge>
                          {order.order_type && (
                            <Badge variant="outline">{order.order_type}</Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {formatDate(order.order_date)}
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {order.student_count} students
                          </div>
                        </div>
                        
                        {order.description && (
                          <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                            {order.description}
                          </p>
                        )}
                      </div>
                      
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
              
              {orders.length === 0 && !loading && (
                <div className="text-center py-8">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-2 text-sm font-semibold text-gray-900">No orders found</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Try adjusting your filters or search criteria.
                  </p>
                </div>
              )}
            </div>
            
            {/* Pagination */}
            {(pagination?.total_pages || 0) > 1 && (
              <div className="flex items-center justify-between border-t pt-4">
                <div className="text-sm text-muted-foreground">
                  Page {pagination?.page || 1} of {pagination?.total_pages || 1}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange((pagination?.page || 1) - 1)}
                    disabled={(pagination?.page || 1) <= 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange((pagination?.page || 1) + 1)}
                    disabled={(pagination?.page || 1) >= (pagination?.total_pages || 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Order Details Modal */}
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            {selectedOrder && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Order #{selectedOrder.order.serial} Details
                  </DialogTitle>
                </DialogHeader>
                
                <div className="space-y-6">
                  {/* Order Information */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Order Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Order Serial</label>
                          <p className="font-medium">{selectedOrder.order.serial}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Order Date</label>
                          <p className="font-medium">{formatDate(selectedOrder.order.order_date)}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Type</label>
                          <Badge variant="outline">{selectedOrder.order.order_type || 'Unknown'}</Badge>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Status</label>
                          <div className="flex gap-2">
                            <Badge variant={selectedOrder.order.active ? "default" : "secondary"}>
                              {selectedOrder.order.active ? "Active" : "Inactive"}
                            </Badge>
                            {selectedOrder.order.status && (
                              <Badge variant="outline">{selectedOrder.order.status}</Badge>
                            )}
                          </div>
                        </div>
                        
                        {/* Education Level */}
                        {selectedOrder.order.education_level && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Education Level</label>
                            <Badge variant="secondary">{selectedOrder.order.education_level}</Badge>
                          </div>
                        )}
                        
                        {/* Creation Information */}
                        {selectedOrder.order.create_date && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Created Date</label>
                            <p className="font-medium">{formatDate(selectedOrder.order.create_date)}</p>
                          </div>
                        )}
                        
                        {/* Creator Information */}
                        {(selectedOrder.order.creator_firstname || selectedOrder.order.creator_lastname) && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Created By</label>
                            <p className="font-medium">
                              {[selectedOrder.order.creator_firstname, selectedOrder.order.creator_lastname, selectedOrder.order.creator_patronymic]
                                .filter(Boolean)
                                .join(' ') || 'Unknown'}
                            </p>
                          </div>
                        )}
                        
                        {/* File Information */}
                        {selectedOrder.order.file_info && (
                          <div className="col-span-2">
                            <label className="text-sm font-medium text-muted-foreground">Attached File</label>
                            <div className="mt-1 p-2 border rounded bg-muted/50">
                              <p className="font-medium">{selectedOrder.order.file_info.original_filename || selectedOrder.order.file_info.filename}</p>
                              <div className="text-sm text-muted-foreground">
                                {selectedOrder.order.file_info.file_size && (
                                  <span>Size: {Math.round(selectedOrder.order.file_info.file_size / 1024)} KB • </span>
                                )}
                                {selectedOrder.order.file_info.mime_type && (
                                  <span>Type: {selectedOrder.order.file_info.mime_type}</span>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Description */}
                        {selectedOrder.order.description && (
                          <div className="col-span-2">
                            <label className="text-sm font-medium text-muted-foreground">Description</label>
                            <p className="font-medium">{selectedOrder.order.description}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Students */}
                  {selectedOrder.students.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Users className="h-5 w-5" />
                          Students ({selectedOrder.students.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {selectedOrder.students.map((student) => (
                            <div key={student.student_id} className="p-3 border rounded">
                              <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                  <p className="font-medium">
                                    {student.last_name} {student.first_name} {student.patronymic}
                                  </p>
                                  <div className="text-sm text-muted-foreground space-y-1">
                                    <p>Student ID: {student.student_id}</p>
                                    {student.card_number && (
                                      <p>Card Number: {student.card_number}</p>
                                    )}
                                    {student.score && (
                                      <p>Score: {student.score}</p>
                                    )}
                                    {student.pincode && (
                                      <p>PIN Code: {student.pincode}</p>
                                    )}
                                    {student.birthdate && (
                                      <p>Birth Date: {student.birthdate}</p>
                                    )}
                                    {student.group_name && (
                                      <div className="flex flex-wrap items-center gap-2 mt-2">
                                        <Badge variant="secondary" className="text-xs">
                                          Group: {student.group_name}
                                        </Badge>
                                        {student.group_education_level && (
                                          <Badge variant="outline" className="text-xs">
                                            Level: {student.group_education_level}
                                          </Badge>
                                        )}
                                        {student.student_major && student.student_major !== 'Unknown' && (
                                          <Badge variant="default" className="text-xs">
                                            Major: {student.student_major}
                                          </Badge>
                                        )}
                                        {student.specialization_name_english && (
                                          <Badge variant="destructive" className="text-xs">
                                            🎓 {student.specialization_name_english}
                                          </Badge>
                                        )}
                                        {!student.specialization_name_english && student.academic_specialization && 
                                         student.academic_specialization !== 'Unknown' && 
                                         !student.academic_specialization.startsWith('Org-') &&
                                         !student.academic_specialization.startsWith('Speciality-') &&
                                         !student.academic_specialization.startsWith('Ixtisas-') && (
                                          <Badge variant="destructive" className="text-xs">
                                            🎓 {student.academic_specialization}
                                          </Badge>
                                        )}
                                        {!student.specialization_name_english && student.academic_specialization && 
                                         (student.academic_specialization.startsWith('Speciality-') ||
                                          student.academic_specialization.startsWith('Ixtisas-')) && (
                                          <Badge variant="outline" className="text-xs">
                                            🎓 {student.specialization_type} (ID: {student.organization_id})
                                          </Badge>
                                        )}
                                        {!student.specialization_name_english && student.academic_specialization && 
                                         student.academic_specialization.startsWith('Org-') && 
                                         student.specialization_type === 'Organization' && (
                                          <Badge variant="secondary" className="text-xs">
                                            🏢 Academic Dept: {student.organization_id}
                                          </Badge>
                                        )}
                                        {student.group_major && student.group_major !== 'Unknown' && student.group_major !== student.student_major && (
                                          <Badge variant="secondary" className="text-xs">
                                            Group Major: {student.group_major}
                                          </Badge>
                                        )}
                                        {student.student_education_line && student.student_education_line !== 'Unknown' && (
                                          <Badge variant="outline" className="text-xs">
                                            Line: {student.student_education_line}
                                          </Badge>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <Badge variant={student.relationship_active ? "default" : "secondary"}>
                                  {student.relationship_active ? "Active" : "Inactive"}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Transfer Parameters */}
                  {selectedOrder.transfer_parameters.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <ArrowUpDown className="h-5 w-5" />
                          Transfer Details ({selectedOrder.transfer_parameters.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {selectedOrder.transfer_parameters.map((transfer, index) => (
                            <div key={`${transfer.from_group_id}-${transfer.to_group_id}-${index}`} className="p-3 border rounded">
                              <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                  <label className="font-medium text-muted-foreground">From Group</label>
                                  <p>{transfer.from_group_name || `Group ${transfer.from_group_id}`}</p>
                                </div>
                                <div>
                                  <label className="font-medium text-muted-foreground">To Group</label>
                                  <p>{transfer.to_group_name || `Group ${transfer.to_group_id}`}</p>
                                </div>
                                <div>
                                  <label className="font-medium text-muted-foreground">Student ID</label>
                                  <p>{transfer.student_id}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
}