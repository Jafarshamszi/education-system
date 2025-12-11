'use client';

import React, { useState, useEffect } from 'react';
import { 
  Building, 
  ChevronRight, 
  ChevronDown, 
  University, 
  School, 
  GraduationCap, 
  Users, 
  MapPin,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface MultilingualName {
  az?: string;
  en?: string;
  ru?: string;
}

export interface Organization {
  id: number;
  name: string | MultilingualName;
  type_id?: number;
  type_name?: string;
  type?: string;
  code?: string;
  parent_id: number | null;
  nod_level?: number;
  active?: number;
  is_active?: boolean;
  children: Organization[];
  has_children: boolean;
}

// Helper function to get name string from multilingual object
const getOrganizationName = (name: string | MultilingualName): string => {
  if (typeof name === 'string') {
    return name;
  }
  // Prefer English, fallback to Azerbaijani, then Russian, then default
  return name.en || name.az || name.ru || 'Unnamed Organization';
};

interface OrganizationResponse {
  organizations: Organization[];
  total_count: number;
}

// Icon mapping based on organization level
const getOrganizationIcon = (level: number) => {
  switch (level) {
    case 1:
      return <University className="h-5 w-5 text-blue-600" />;
    case 2:
      return <Building className="h-5 w-5 text-purple-600" />;
    case 3:
      return <School className="h-5 w-5 text-green-600" />;
    case 4:
      return <GraduationCap className="h-4 w-4 text-orange-600" />;
    case 5:
      return <Users className="h-4 w-4 text-red-600" />;
    default:
      return <MapPin className="h-4 w-4 text-gray-600" />;
  }
};

// Badge color mapping based on level
const getBadgeVariant = (level: number) => {
  switch (level) {
    case 1:
      return 'default';
    case 2:
      return 'secondary';
    case 3:
      return 'outline';
    case 4:
      return 'destructive';
    case 5:
      return 'secondary';
    default:
      return 'outline';
  }
};

// Get level name
const getLevelName = (level: number) => {
  switch (level) {
    case 1:
      return 'University';
    case 2:
      return 'Division';
    case 3:
      return 'Faculty';
    case 4:
      return 'Department';
    case 5:
      return 'Unit';
    default:
      return `Level ${level}`;
  }
};

interface OrganizationNodeProps {
  organization: Organization;
  level?: number;
  onSelect?: (org: Organization) => void;
}

const OrganizationNode: React.FC<OrganizationNodeProps> = ({ 
  organization, 
  level = 0, 
  onSelect 
}) => {
  const [isOpen, setIsOpen] = useState(level < 2); // Auto-expand first 2 levels
  const hasChildren = organization.children && organization.children.length > 0;
  
  const handleClick = () => {
    if (onSelect) {
      onSelect(organization);
    }
  };

  return (
    <div className="w-full">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <Card className="mb-2 hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              {/* Expand/Collapse Button */}
              {hasChildren && (
                <CollapsibleTrigger className="flex items-center justify-center h-6 w-6 rounded hover:bg-gray-100">
                  {isOpen ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CollapsibleTrigger>
              )}
              {!hasChildren && <div className="w-6" />}

              {/* Organization Icon */}
              {getOrganizationIcon(organization.nod_level || 1)}

              {/* Organization Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 
                    className="font-medium text-gray-900 truncate cursor-pointer hover:text-blue-600"
                    onClick={handleClick}
                  >
                    {getOrganizationName(organization.name)}
                  </h3>
                  <Badge variant={getBadgeVariant(organization.nod_level || 1)}>
                    {getLevelName(organization.nod_level || 1)}
                  </Badge>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>ID: {organization.id}</span>
                  {organization.code && <span>Code: {organization.code}</span>}
                  {(organization.type_name || organization.type) && (
                    <span>Type: {organization.type_name || organization.type}</span>
                  )}
                  {hasChildren && (
                    <span className="text-blue-600 font-medium">
                      {organization.children.length} children
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Children */}
        {hasChildren && (
          <CollapsibleContent className="ml-6">
            <div className="border-l-2 border-gray-200 pl-4 space-y-1">
              {organization.children.map((child) => (
                <OrganizationNode
                  key={child.id}
                  organization={child}
                  level={level + 1}
                  onSelect={onSelect}
                />
              ))}
            </div>
          </CollapsibleContent>
        )}
      </Collapsible>
    </div>
  );
};

interface ShadcnOrganizationTreeProps {
  onSelect?: (org: Organization) => void;
}

export const ShadcnOrganizationTree: React.FC<ShadcnOrganizationTreeProps> = ({ onSelect }) => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('🔄 Fetching organizations from API...');
        
        const response = await fetch('http://127.0.0.1:8000/api/v1/organizations/hierarchy?include_children=true', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });

        console.log('📡 Response status:', response.status);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: OrganizationResponse = await response.json();
        console.log('✅ Data received:', data);
        
        setOrganizations(data.organizations || []);
        setTotalCount(data.total_count || 0);
      } catch (err) {
        console.error('❌ Failed to fetch organizations:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch organizations');
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizations();
  }, []);

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-gray-600">Loading organization hierarchy...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load organization hierarchy: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (organizations.length === 0) {
    return (
      <Card className="p-8">
        <div className="text-center text-gray-500">
          <Building className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium mb-2">No Organizations Found</h3>
          <p>There are no organizations to display.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-blue-900">
              Organization Hierarchy
            </h2>
          </div>
          <Badge variant="outline" className="text-blue-700 border-blue-300">
            {totalCount} total organizations
          </Badge>
        </div>
      </Card>

      <Separator />

      {/* Organization Tree */}
      <div className="space-y-2">
        {organizations.map((org) => (
          <OrganizationNode
            key={org.id}
            organization={org}
            level={0}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
};