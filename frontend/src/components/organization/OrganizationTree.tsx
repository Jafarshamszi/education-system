'use client';

import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Building, Users, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Organization, useOrganizations } from '@/hooks/useOrganizations';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface OrganizationNodeProps {
  organization: Organization;
  level: number;
  onSelect: (org: Organization) => void;
  selectedId?: number;
  onFetchChildren: (parentId: number) => Promise<Organization[]>;
}

const OrganizationNode: React.FC<OrganizationNodeProps> = ({
  organization,
  level,
  onSelect,
  selectedId,
  onFetchChildren,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [children, setChildren] = useState<Organization[]>([]);
  const [loadingChildren, setLoadingChildren] = useState(false);

  const handleToggle = async () => {
    if (!organization.has_children) return;

    if (!isExpanded && children.length === 0) {
      setLoadingChildren(true);
      try {
        const fetchedChildren = await onFetchChildren(organization.id);
        setChildren(fetchedChildren);
      } catch (error) {
        console.error('Error fetching children:', error);
      } finally {
        setLoadingChildren(false);
      }
    }
    setIsExpanded(!isExpanded);
  };

  const handleSelect = () => {
    onSelect(organization);
  };

  const getOrgIcon = (typeName?: string) => {
    if (typeName?.toLowerCase().includes('universitet')) return Building;
    if (typeName?.toLowerCase().includes('fakulte')) return Users;
    if (typeName?.toLowerCase().includes('kafedra')) return FileText;
    return Building;
  };

  const IconComponent = getOrgIcon(organization.type_name);

  return (
    <div className="w-full">
      <div
        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors hover:bg-gray-50 ${
          selectedId === organization.id ? 'bg-blue-50 border border-blue-200' : ''
        }`}
        style={{ marginLeft: `${level * 20}px` }}
      >
        {/* Expand/Collapse Button */}
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={handleToggle}
          disabled={!organization.has_children || loadingChildren}
        >
          {loadingChildren ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          ) : organization.has_children ? (
            isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <div className="h-4 w-4" />
          )}
        </Button>

        {/* Organization Info */}
        <div className="flex items-center gap-2 flex-1" onClick={handleSelect}>
          <IconComponent className="h-4 w-4 text-gray-600" />
          <span className="font-medium text-gray-900">{organization.name}</span>
          {organization.type_name && (
            <Badge variant="secondary" className="text-xs">
              {organization.type_name}
            </Badge>
          )}
          <span className="text-xs text-gray-500">#{organization.id}</span>
        </div>
      </div>

      {/* Children */}
      {isExpanded && children.length > 0 && (
        <div className="mt-1">
          {children.map((child) => (
            <OrganizationNode
              key={child.id}
              organization={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
              onFetchChildren={onFetchChildren}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface OrganizationTreeProps {
  onOrganizationSelect?: (org: Organization) => void;
}

export const OrganizationTree: React.FC<OrganizationTreeProps> = ({
  onOrganizationSelect,
}) => {
  const {
    organizations,
    loading,
    error,
    fetchOrganizationChildren,
  } = useOrganizations();
  
  const [selectedOrgId, setSelectedOrgId] = useState<number>();

  const handleOrgSelect = (org: Organization) => {
    setSelectedOrgId(org.id);
    onOrganizationSelect?.(org);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Organization Structure
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Organization Structure
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertDescription>
              Error loading organizations: {error}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building className="h-5 w-5" />
          Organization Structure
          <Badge variant="outline">{organizations.length} organizations</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {organizations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No organizations found
          </div>
        ) : (
          <div className="space-y-1">
            {organizations.map((org) => (
              <OrganizationNode
                key={org.id}
                organization={org}
                level={0}
                onSelect={handleOrgSelect}
                selectedId={selectedOrgId}
                onFetchChildren={fetchOrganizationChildren}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};