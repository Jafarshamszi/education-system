import { useState, useEffect } from 'react';
import { API_BASE_URL } from '@/lib/api-config';

export interface Organization {
  id: number;
  name: string;
  type_id?: number;
  type_name?: string;
  parent_id?: number;
  nod_level?: number;
  active?: number;
  children?: Organization[];
  has_children?: boolean;
}

export interface OrganizationHierarchy {
  organizations: Organization[];
  total_count: number;
}

export const useOrganizations = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrganizationHierarchy = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/organizations/hierarchy`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch organizations: ${response.statusText}`);
      }

      const data: OrganizationHierarchy = await response.json();
      setOrganizations(data.organizations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching organizations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganizationChildren = async (parentId: number): Promise<Organization[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/organizations/${parentId}/children`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch children: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      console.error('Error fetching organization children:', err);
      return [];
    }
  };

  const fetchOrganizationDetail = async (organizationId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/organizations/${organizationId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch organization detail: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      console.error('Error fetching organization detail:', err);
      return null;
    }
  };

  useEffect(() => {
    fetchOrganizationHierarchy();
  }, []);

  return {
    organizations,
    loading,
    error,
    fetchOrganizationHierarchy,
    fetchOrganizationChildren,
    fetchOrganizationDetail,
  };
};