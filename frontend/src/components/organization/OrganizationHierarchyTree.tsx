'use client';

import React, { useState, useEffect } from 'react';
import { 
  ChevronRight, 
  ChevronDown, 
  Building2, 
  GraduationCap, 
  Users, 
  BookOpen,
  Briefcase 
} from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { Organization, useOrganizations } from '@/hooks/useOrganizations';

interface OrganizationNodeProps {
  organization: Organization;
  level: number;
  onSelect?: (org: Organization) => void;
  selectedId?: number;
  className?: string;
}

const OrganizationNode: React.FC<OrganizationNodeProps> = ({
  organization,
  level,
  onSelect,
  selectedId,
  className
}) => {
  const [isOpen, setIsOpen] = useState(level < 2); // Auto-expand first 2 levels
  const [children, setChildren] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const { fetchOrganizationChildren } = useOrganizations();

  useEffect(() => {
    if (organization.children && organization.children.length > 0) {
      setChildren(organization.children);
    }
  }, [organization.children]);

  const handleLoadChildren = async () => {
    if (children.length === 0 && organization.has_children) {
      setLoading(true);
      try {
        const fetchedChildren = await fetchOrganizationChildren(organization.id);
        setChildren(fetchedChildren);
      } catch (error) {
        console.error('Error loading children:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const getOrganizationIcon = (level: number) => {
    if (level === 1) return Building2;
    if (level === 2) return GraduationCap;
    if (level === 3) return Users;
    if (level === 4) return BookOpen;
    return Briefcase;
  };

  const getOrganizationColor = (level: number) => {
    const colors = [
      'bg-blue-50 border-blue-200 text-blue-900',
      'bg-green-50 border-green-200 text-green-900', 
      'bg-purple-50 border-purple-200 text-purple-900',
      'bg-orange-50 border-orange-200 text-orange-900',
      'bg-pink-50 border-pink-200 text-pink-900'
    ];
    return colors[level - 1] || 'bg-gray-50 border-gray-200 text-gray-900';
  };

  const IconComponent = getOrganizationIcon(level);
  const isSelected = selectedId === organization.id;
  const hasChildren = organization.has_children || children.length > 0;

  return (
    <div className={cn("w-full", className)}>
      <Collapsible
        open={isOpen}
        onOpenChange={(open) => {
          setIsOpen(open);
          if (open) {
            handleLoadChildren();
          }
        }}
      >
        <Card className={cn(
          "transition-all duration-200 hover:shadow-md",
          isSelected && "ring-2 ring-blue-500 shadow-md",
          getOrganizationColor(level)
        )}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div 
                className="flex items-center gap-3 flex-1 cursor-pointer"
                onClick={() => onSelect?.(organization)}
              >
                <div className="flex items-center gap-2">
                  <IconComponent className="h-5 w-5" />
                  <div>
                    <CardTitle className="text-sm font-semibold">
                      {organization.name}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        Level {organization.nod_level}
                      </Badge>
                      {organization.type_name && (
                        <Badge variant="secondary" className="text-xs">
                          {organization.type_name}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        #{organization.id}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {hasChildren && (
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    {loading ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    ) : isOpen ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                </CollapsibleTrigger>
              )}
            </div>
          </CardHeader>
          
          <CollapsibleContent>
            <CardContent className="pt-0">
              {children.length > 0 && (
                <>
                  <Separator className="mb-4" />
                  <div className="space-y-3">
                    {children.map((child, index) => (
                      <OrganizationNode
                        key={child.id}
                        organization={child}
                        level={level + 1}
                        onSelect={onSelect}
                        selectedId={selectedId}
                        className={index < children.length - 1 ? "mb-2" : ""}
                      />
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </div>
  );
};

interface OrganizationHierarchyTreeProps {
  onOrganizationSelect?: (org: Organization) => void;
  selectedOrganizationId?: number;
  className?: string;
}

export const OrganizationHierarchyTree: React.FC<OrganizationHierarchyTreeProps> = ({
  onOrganizationSelect,
  selectedOrganizationId,
  className
}) => {
  const { 
    organizations, 
    loading, 
    error, 
    fetchOrganizationHierarchy 
  } = useOrganizations();

  useEffect(() => {
    fetchOrganizationHierarchy();
  }, [fetchOrganizationHierarchy]);

  if (loading) {
    return (
      <div className={cn("p-6", className)}>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("p-6", className)}>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="text-red-800 text-center">
              <h3 className="font-semibold mb-2">Error Loading Organizations</h3>
              <p className="text-sm">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={cn("p-6", className)}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Organization Hierarchy
        </h2>
        <p className="text-gray-600">
          Explore the organizational structure with {organizations.length} top-level organizations
        </p>
      </div>
      
      <div className="space-y-4">
        {organizations.map((org) => (
          <OrganizationNode
            key={org.id}
            organization={org}
            level={org.nod_level || 1}
            onSelect={onOrganizationSelect}
            selectedId={selectedOrganizationId}
          />
        ))}
      </div>
    </div>
  );
};

export default OrganizationHierarchyTree;