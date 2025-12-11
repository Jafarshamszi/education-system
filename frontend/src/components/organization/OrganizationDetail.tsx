'use client';

import React, { useState, useEffect } from 'react';
import {
  Building,
  Calendar,
  Hash,
  Layers,
  Users,
  FileText,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Organization, useOrganizations } from '@/hooks/useOrganizations';

interface OrganizationDetailProps {
  organizationId: number;
  onNavigateToOrganization?: (orgId: number) => void;
}

interface OrganizationDetail extends Organization {
  formula?: string;
  logo_name?: number;
  create_date?: string;
  update_date?: string;
  parent_name?: string;
  children_count: number;
}

export const OrganizationDetail: React.FC<OrganizationDetailProps> = ({
  organizationId,
  onNavigateToOrganization,
}) => {
  const { fetchOrganizationDetail, fetchOrganizationChildren } = useOrganizations();
  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);
  const [children, setChildren] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOrganization = async () => {
      setLoading(true);
      setError(null);

      try {
        const [orgDetail, orgChildren] = await Promise.all([
          fetchOrganizationDetail(organizationId),
          fetchOrganizationChildren(organizationId),
        ]);

        if (orgDetail) {
          setOrganization(orgDetail);
          setChildren(orgChildren);
        } else {
          setError('Organization not found');
        }
      } catch (err) {
        setError('Failed to load organization details');
        console.error('Error loading organization:', err);
      } finally {
        setLoading(false);
      }
    };

    if (organizationId) {
      loadOrganization();
    }
  }, [organizationId, fetchOrganizationDetail, fetchOrganizationChildren]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (active?: number) => {
    if (active === 1) {
      return <Badge className="bg-green-100 text-green-800">Active</Badge>;
    }
    return <Badge variant="destructive">Inactive</Badge>;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !organization) {
    return (
      <Card>
        <CardContent className="pt-6">
          <Alert>
            <AlertDescription>
              {error || 'Organization not found'}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-5 w-5" />
              {organization.name}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Organization ID: {organization.id}
            </p>
          </div>
          {getStatusBadge(organization.active)}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Basic Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Type</label>
              <p className="text-sm">
                {organization.type_name ? (
                  <Badge variant="outline">{organization.type_name}</Badge>
                ) : (
                  'N/A'
                )}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Level</label>
              <p className="text-sm flex items-center gap-1">
                <Layers className="h-3 w-3" />
                {organization.nod_level || 'N/A'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Parent Organization</label>
              <p className="text-sm">
                {organization.parent_name ? (
                  <Button
                    variant="link"
                    className="p-0 h-auto text-blue-600"
                    onClick={() => organization.parent_id && onNavigateToOrganization?.(organization.parent_id)}
                  >
                    {organization.parent_name}
                  </Button>
                ) : (
                  'Root Organization'
                )}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Children Count</label>
              <p className="text-sm flex items-center gap-1">
                <Users className="h-3 w-3" />
                {organization.children_count}
              </p>
            </div>
          </div>
        </div>

        <Separator />

        {/* System Information */}
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Hash className="h-4 w-4" />
            System Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Created</label>
              <p className="text-sm flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(organization.create_date)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Last Updated</label>
              <p className="text-sm flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(organization.update_date)}
              </p>
            </div>
            {organization.formula && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-600">Formula</label>
                <p className="text-xs font-mono bg-gray-50 p-2 rounded border">
                  {organization.formula}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Child Organizations */}
        {children.length > 0 && (
          <>
            <Separator />
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4" />
                Child Organizations ({children.length})
              </h3>
              <div className="space-y-2">
                {children.map((child) => (
                  <div
                    key={child.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                    onClick={() => onNavigateToOrganization?.(child.id)}
                  >
                    <div className="flex items-center gap-3">
                      <Building className="h-4 w-4 text-gray-600" />
                      <div>
                        <p className="font-medium">{child.name}</p>
                        {child.type_name && (
                          <p className="text-xs text-gray-600">{child.type_name}</p>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};