'use client';

import React, { useState, useEffect } from 'react';
import { Building2, ChevronRight, ChevronDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Organization {
  id: number;
  name: string;
  type_name?: string;
  nod_level?: number;
  parent_id?: number;
  has_children?: boolean;
  children?: Organization[];
}

interface OrganizationHierarchyResponse {
  organizations: Organization[];
  total_count: number;
}

const OrganizationNode: React.FC<{ org: Organization; level: number }> = ({ org, level }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2);

  return (
    <div style={{ marginLeft: `${level * 20}px` }} className="mb-2">
      <Card className="w-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-blue-600" />
              <CardTitle className="text-sm">
                {org.name}
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                Level {org.nod_level}
              </Badge>
              {org.type_name && (
                <Badge variant="secondary" className="text-xs">
                  {org.type_name}
                </Badge>
              )}
              <span className="text-xs text-gray-500">#{org.id}</span>
            </div>
            
            {org.children && org.children.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-6 w-6 p-0"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </CardHeader>
        
        {isExpanded && org.children && org.children.length > 0 && (
          <CardContent className="pt-0">
            <div className="space-y-2">
              {org.children.map((child) => (
                <OrganizationNode key={child.id} org={child} level={level + 1} />
              ))}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};

export const SimpleOrganizationTree: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        setLoading(true);
        console.log('Fetching organizations...');
        
        const response = await fetch('http://127.0.0.1:8000/api/v1/organizations/hierarchy', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: OrganizationHierarchyResponse = await response.json();
        console.log('Data received:', data);
        setOrganizations(data.organizations);
        setError(null);
      } catch (err) {
        console.error('Error fetching organizations:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizations();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p>Loading organizations...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="text-center text-red-800">
              <h3 className="font-semibold mb-2">Error Loading Organizations</h3>
              <p className="text-sm">{error}</p>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                className="mt-4"
              >
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Organization Hierarchy
        </h2>
        <p className="text-gray-600">
          Found {organizations.length} top-level organizations
        </p>
      </div>
      
      <div className="space-y-3">
        {organizations.map((org) => (
          <OrganizationNode key={org.id} org={org} level={0} />
        ))}
      </div>
    </div>
  );
};

export default SimpleOrganizationTree;