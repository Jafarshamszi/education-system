"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Search, Eye, Edit, UserCheck, Users, GraduationCap, Building } from "lucide-react";

// API response types matching actual backend structure
interface PersonInfo {
  id: number;
  firstname?: string | null;
  lastname?: string | null;
  patronymic?: string | null;
  pincode?: string | null;
  birthdate?: string | null;
}

interface OrganizationInfo {
  id: number;
  name?: string | null;
}

interface DictionaryInfo {
  id: number;
  name_en?: string | null;
  name_az?: string | null;
  code?: string | null;
}

interface ApiTeacher {
  id: number;
  person?: PersonInfo | null;
  organization?: OrganizationInfo | null;
  position?: DictionaryInfo | null;
  staff_type?: DictionaryInfo | null;
  contract_type?: DictionaryInfo | null;
  teaching?: number | null;
  is_active?: boolean | null;
}

// Frontend display interface
interface Teacher {
  id: number;
  full_name: string;
  username?: string | null;
  email?: string | null;
  card_number?: string | null;
  position_name?: string | null;
  staff_type_name?: string | null;
  contract_type_name?: string | null;
  organization_name?: string | null;
  is_active: boolean;
  is_teaching: boolean;
  create_date: string;
  update_date: string;
}

interface TeacherStats {
  total_teachers: number;
  active_teachers: number;
  teaching_count: number;
  organizations_count: number;
}

interface TeacherFilters {
  search?: string;
  is_active?: boolean;
  is_teaching?: boolean;
  organization_id?: number;
  position_id?: number;
  staff_type_id?: number;
  contract_type_id?: number;
  page?: number;
  page_size?: number;
}

interface Organization {
  id: number;
  name: string;
}

interface TeacherFilterOptions {
  organizations: Organization[];
}

const ITEMS_PER_PAGE = 25;

// Transform API response to frontend format
const transformApiTeacher = (apiTeacher: ApiTeacher): Teacher => {
  const fullName = apiTeacher.person 
    ? [apiTeacher.person.firstname, apiTeacher.person.lastname, apiTeacher.person.patronymic]
        .filter(Boolean)
        .join(' ')
    : 'Unknown';

  return {
    id: apiTeacher.id,
    full_name: fullName,
    username: null,
    email: null,
    card_number: null,
    position_name: apiTeacher.position?.name_en || apiTeacher.position?.name_az || null,
    staff_type_name: apiTeacher.staff_type?.name_en || apiTeacher.staff_type?.name_az || null,
    contract_type_name: apiTeacher.contract_type?.name_en || apiTeacher.contract_type?.name_az || null,
    organization_name: apiTeacher.organization?.name || null,
    is_active: apiTeacher.is_active ?? false,
    is_teaching: apiTeacher.teaching === 1,
    create_date: new Date().toISOString(),
    update_date: new Date().toISOString(),
  };
};

export default function TeachersPage() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [stats, setStats] = useState<TeacherStats | null>(null);
  const [filterOptions, setFilterOptions] = useState<TeacherFilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  // Filter state
  const [filters, setFilters] = useState<TeacherFilters>({
    search: "",
    is_active: undefined,
    is_teaching: undefined,
    organization_id: undefined,
    position_id: undefined,
    staff_type_id: undefined,
    contract_type_id: undefined,
  });

  // Load functions with useCallback to prevent infinite re-renders
  const loadTeachers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Make API call to FastAPI backend
      const response = await fetch(`http://localhost:8000/api/v1/teachers/?page=${currentPage}&per_page=${ITEMS_PER_PAGE}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add auth headers if needed
          // 'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Transform API response to match frontend interface
      const transformedTeachers = data.results.map((apiTeacher: ApiTeacher) => 
        transformApiTeacher(apiTeacher)
      );
      
      setTeachers(transformedTeachers);
      setTotalCount(data.count);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError("Failed to load teachers. Please try again.");
      console.error("Error loading teachers:", err);
    } finally {
      setLoading(false);
    }
  }, [currentPage]);

  const loadStats = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/teachers/stats', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const statsData = await response.json();
        setStats(statsData as TeacherStats);
      }
    } catch (err) {
      console.error("Error loading stats:", err);
    }
  }, []);

  const loadFilterOptions = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/teachers/filter-options', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const options = await response.json();
        // Transform the filter options to match expected format
        const transformedOptions = {
          organizations: options.organizations.map((org: OrganizationInfo) => ({
            id: org.id,
            name: org.name || `Organization ${org.id}`
          }))
        };
        setFilterOptions(transformedOptions as TeacherFilterOptions);
      }
    } catch (err) {
      console.error("Error loading filter options:", err);
    }
  }, []);

  // Load initial data
  useEffect(() => {
    loadTeachers();
  }, [loadTeachers]);

  useEffect(() => {
    loadStats();
    loadFilterOptions();
  }, [loadStats, loadFilterOptions]);

  const handleFilterChange = (key: keyof TeacherFilters, value: string | number | boolean | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === "all" ? undefined : value,
    }));
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleSearch = (searchTerm: string) => {
    setFilters(prev => ({ ...prev, search: searchTerm }));
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const viewTeacherDetails = async (teacher: Teacher) => {
    try {
      // For now, just use the teacher data we have
      setSelectedTeacher(teacher);
      setShowDetails(true);
    } catch (err) {
      console.error("Error loading teacher details:", err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading && teachers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading teachers...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Teachers</h1>
        <p className="text-muted-foreground">
          Manage and view teacher information, assignments, and statistics.
        </p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Teachers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_teachers}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Teachers</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_teachers}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Teaching Staff</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.teaching_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Organizations</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.organizations_count}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle>Search and Filter</CardTitle>
          <CardDescription>
            Find teachers by name, username, or use filters to narrow down results.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name or username..."
                value={filters.search || ""}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-8"
              />
            </div>

            {/* Active Status Filter */}
            <Select
              value={filters.is_active === undefined ? "all" : filters.is_active.toString()}
              onValueChange={(value) => 
                handleFilterChange("is_active", value === "all" ? undefined : value === "true")
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Active Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>

            {/* Teaching Status Filter */}
            <Select
              value={filters.is_teaching === undefined ? "all" : filters.is_teaching.toString()}
              onValueChange={(value) => 
                handleFilterChange("is_teaching", value === "all" ? undefined : value === "true")
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Teaching Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Teaching Status</SelectItem>
                <SelectItem value="true">Teaching</SelectItem>
                <SelectItem value="false">Non-Teaching</SelectItem>
              </SelectContent>
            </Select>

            {/* Organization Filter */}
            {filterOptions && (
              <Select
                value={filters.organization_id?.toString() || "all"}
                onValueChange={(value) => 
                  handleFilterChange("organization_id", value === "all" ? undefined : parseInt(value))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Organization" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Organizations</SelectItem>
                  {filterOptions.organizations.map((org: Organization) => (
                    <SelectItem key={org.id} value={org.id.toString()}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Teachers Table */}
      <Card>
        <CardHeader>
          <CardTitle>Teachers List</CardTitle>
          <CardDescription>
            Showing {teachers.length} of {totalCount} teachers (Page {currentPage} of {totalPages})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Position</TableHead>
                  <TableHead>Staff Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teachers.map((teacher) => (
                  <TableRow key={teacher.id}>
                    <TableCell className="font-medium">
                      {teacher.full_name}
                    </TableCell>
                    <TableCell>{teacher.username || "-"}</TableCell>
                    <TableCell>{teacher.email || "-"}</TableCell>
                    <TableCell>{teacher.position_name || "-"}</TableCell>
                    <TableCell>{teacher.staff_type_name || "-"}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Badge variant={teacher.is_active ? "default" : "secondary"}>
                          {teacher.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {teacher.is_teaching && (
                          <Badge variant="outline">Teaching</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => viewTeacherDetails(teacher)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // TODO: Implement edit functionality
                            console.log("Edit teacher:", teacher.id);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between space-x-2 py-4">
              <div className="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{" "}
                {Math.min(currentPage * ITEMS_PER_PAGE, totalCount)} of {totalCount} results
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Teacher Details Dialog */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Teacher Details</DialogTitle>
            <DialogDescription>
              View detailed information about the selected teacher.
            </DialogDescription>
          </DialogHeader>
          {selectedTeacher && (
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="basic">Basic Information</TabsTrigger>
                <TabsTrigger value="professional">Professional Details</TabsTrigger>
              </TabsList>
              <TabsContent value="basic" className="space-y-4">
                <div className="grid gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Full Name</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.full_name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Username</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.username || "-"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Email</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.email || "-"}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Card Number</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.card_number || "-"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Created Date</label>
                      <p className="text-sm text-muted-foreground">{formatDate(selectedTeacher.create_date)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Updated Date</label>
                      <p className="text-sm text-muted-foreground">{formatDate(selectedTeacher.update_date)}</p>
                    </div>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="professional" className="space-y-4">
                <div className="grid gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Organization</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.organization_name || "-"}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Position</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.position_name || "-"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Staff Type</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.staff_type_name || "-"}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Contract Type</label>
                      <p className="text-sm text-muted-foreground">{selectedTeacher.contract_type_name || "-"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Status</label>
                      <div className="flex gap-2">
                        <Badge variant={selectedTeacher.is_active ? "default" : "secondary"}>
                          {selectedTeacher.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {selectedTeacher.is_teaching && (
                          <Badge variant="outline">Teaching</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}