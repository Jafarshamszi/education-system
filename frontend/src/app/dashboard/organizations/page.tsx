'use client';

import React, { useState } from 'react';
import { Building, ArrowLeft, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ShadcnOrganizationTree, type Organization } from '@/components/organization/ShadcnOrganizationTree';

interface MultilingualName {
  az?: string;
  en?: string;
  ru?: string;
}

export default function OrganizationPage() {
  const [selectedOrganization, setSelectedOrganization] = useState<Organization | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'detail'>('tree');

  const handleOrganizationSelect = (org: Organization) => {
    setSelectedOrganization(org);
    setViewMode('detail');
  };

  const handleBackToTree = () => {
    setViewMode('tree');
    setSelectedOrganization(null);
  };

  const getOrganizationName = (name: string | MultilingualName | undefined): string => {
    if (!name) return 'Unknown';
    if (typeof name === 'string') return name;
    return name.az || name.en || name.ru || 'Unknown';
  };

  const getLevelName = (level: number | undefined) => {
    if (!level) return 'Unknown Level';
    switch (level) {
      case 1: return 'University';
      case 2: return 'Division';
      case 3: return 'Faculty';
      case 4: return 'Department';
      case 5: return 'Unit';
      default: return `Level ${level}`;
    }
  };

  const getBadgeVariant = (level: number | undefined) => {
    if (!level) return 'outline' as const;
    switch (level) {
      case 1: return 'default' as const;
      case 2: return 'secondary' as const;
      case 3: return 'outline' as const;
      case 4: return 'destructive' as const;
      case 5: return 'secondary' as const;
      default: return 'outline' as const;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {viewMode === 'detail' && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToTree}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Hierarchy
            </Button>
          )}
          <Building className="h-6 w-6 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Organization Management
          </h1>
        </div>
        
        {viewMode === 'detail' && selectedOrganization && (
          <div className="flex items-center gap-2">
            <Badge variant={getBadgeVariant(selectedOrganization.nod_level)}>
              {getLevelName(selectedOrganization.nod_level)}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToTree}
              className="flex items-center gap-2"
            >
              <Building className="h-4 w-4" />
              View All
            </Button>
          </div>
        )}
      </div>

      <Separator />

      {/* Content */}
      <div className="grid grid-cols-1 gap-6">
        {/* Tree View */}
        {viewMode === 'tree' && (
          <div className="w-full">
            <ShadcnOrganizationTree onSelect={handleOrganizationSelect} />
          </div>
        )}

        {/* Detail View */}
        {viewMode === 'detail' && selectedOrganization && (
          <div className="w-full max-w-4xl mx-auto">
            <Card className="shadow-lg">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Building className="h-6 w-6 text-blue-600" />
                    <CardTitle className="text-2xl">Organization Details</CardTitle>
                  </div>
                  <Badge variant={getBadgeVariant(selectedOrganization.nod_level)}>
                    {getLevelName(selectedOrganization.nod_level)}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                      <Info className="h-5 w-5" />
                      Basic Information
                    </h3>
                    
                    <div className="space-y-3 bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Name:</span>
                        <span className="text-gray-900 font-semibold">{getOrganizationName(selectedOrganization.name)}</span>
                      </div>
                      
                      <Separator />
                      
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Organization ID:</span>
                        <Badge variant="outline" className="font-mono">
                          {selectedOrganization.id}
                        </Badge>
                      </div>
                      
                      <Separator />
                      
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Type:</span>
                        <span className="text-gray-900">{selectedOrganization.type_name}</span>
                      </div>
                      
                      <Separator />
                      
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Type ID:</span>
                        <Badge variant="secondary" className="font-mono">
                          {selectedOrganization.type_id}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Hierarchy Information</h3>
                    
                    <div className="space-y-3 bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <div className="flex justify-between">
                        <span className="font-medium text-blue-700">Hierarchy Level:</span>
                        <Badge variant={getBadgeVariant(selectedOrganization.nod_level)}>
                          Level {selectedOrganization.nod_level}
                        </Badge>
                      </div>
                      
                      <Separator />
                      
                      <div className="flex justify-between">
                        <span className="font-medium text-blue-700">Level Type:</span>
                        <span className="text-blue-900 font-semibold">
                          {getLevelName(selectedOrganization.nod_level)}
                        </span>
                      </div>
                      
                      <Separator />
                      
                      {selectedOrganization.parent_id && (
                        <>
                          <div className="flex justify-between">
                            <span className="font-medium text-blue-700">Parent ID:</span>
                            <Badge variant="outline" className="font-mono">
                              {selectedOrganization.parent_id}
                            </Badge>
                          </div>
                          <Separator />
                        </>
                      )}
                      
                      <div className="flex justify-between">
                        <span className="font-medium text-blue-700">Status:</span>
                        <Badge variant={selectedOrganization.active === 1 ? "default" : "destructive"}>
                          {selectedOrganization.active === 1 ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                      
                      {selectedOrganization.has_children && (
                        <>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="font-medium text-blue-700">Children:</span>
                            <Badge variant="secondary">
                              {selectedOrganization.children?.length || 0} sub-organizations
                            </Badge>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Children Organizations */}
                {selectedOrganization.children && selectedOrganization.children.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Sub-Organizations ({selectedOrganization.children.length})
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {selectedOrganization.children.map((child) => (
                        <Card 
                          key={child.id} 
                          className="hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => handleOrganizationSelect(child)}
                        >
                          <CardContent className="p-4">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-900 truncate">
                                  {getOrganizationName(child.name)}
                                </h4>
                                <Badge variant={getBadgeVariant(child.nod_level)} className="text-xs">
                                  {getLevelName(child.nod_level)}
                                </Badge>
                              </div>
                              
                              <div className="text-sm text-gray-600">
                                <div>ID: {child.id}</div>
                                <div>Type: {child.type_name}</div>
                                {child.has_children && (
                                  <div className="text-blue-600 font-medium">
                                    {child.children?.length || 0} children
                                  </div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}