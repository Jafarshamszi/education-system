"use client";

import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Info, Calculator, Users, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Separator } from '@/components/ui/separator';
import axios from 'axios';

interface EvaluationSystem {
  name: string;
  variant_count: number;
  min_pass_percent: number | null;
  max_pass_percent: number | null;
  formulas: string;
}

interface EvaluationDetail {
  id: string;
  name: string;
  points: string;
  parsed_points: Array<{
    id: string | null;
    code: string;
    name_en?: string;
    name_ru?: string;
    type: string;
  }>;
  successful_pass_percent: number | null;
  formula_with_cw: string | null;
  formula_without_cw: string | null;
  colloquium_status: number | null;
  type: string | null;
}

interface GradeDictionary {
  id: string;
  code: string;
  name_en: string;
  name_ru: string;
  type_id: string | null;
  category: string;
}

interface EvaluationStatistics {
  total_records: number;
  usage_by_system: Array<{
    name: string;
    usage_count: number;
  }>;
  grade_distribution: Array<{
    grade_type: string;
    count: number;
  }>;
}

export default function EvaluationSystemPage() {
  const [systems, setSystems] = useState<EvaluationSystem[]>([]);
  const [expandedSystems, setExpandedSystems] = useState<{ [key: string]: boolean }>({});
  const [systemDetails, setSystemDetails] = useState<{ [key: string]: EvaluationDetail[] }>({});
  const [gradeDictionary, setGradeDictionary] = useState<GradeDictionary[]>([]);
  const [statistics, setStatistics] = useState<EvaluationStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvaluationSystems();
    fetchGradeDictionary();
    fetchStatistics();
  }, []);

  const fetchEvaluationSystems = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/evaluation-systems');
      setSystems(response.data);
    } catch (err) {
      setError('Failed to fetch evaluation systems');
      console.error('Error fetching evaluation systems:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchGradeDictionary = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/grade-dictionary');
      setGradeDictionary(response.data);
    } catch (err) {
      console.error('Error fetching grade dictionary:', err);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/evaluation-statistics');
      setStatistics(response.data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  const fetchSystemDetails = async (systemName: string) => {
    if (systemDetails[systemName]) {
      return; // Already loaded
    }

    try {
      const response = await axios.get(`http://localhost:8000/api/v1/evaluation-systems/${systemName}/details`);
      setSystemDetails(prev => ({
        ...prev,
        [systemName]: response.data
      }));
    } catch (err) {
      console.error(`Error fetching details for ${systemName}:`, err);
    }
  };

  const toggleSystemExpansion = async (systemName: string) => {
    const isCurrentlyExpanded = expandedSystems[systemName];
    
    if (!isCurrentlyExpanded) {
      await fetchSystemDetails(systemName);
    }
    
    setExpandedSystems(prev => ({
      ...prev,
      [systemName]: !isCurrentlyExpanded
    }));
  };

  const getSystemColor = (systemName: string) => {
    switch (systemName) {
      case 'MS': return 'bg-blue-100 text-blue-800';
      case 'MSL': return 'bg-green-100 text-green-800';
      case 'XDS': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getGradeTypeColor = (category: string) => {
    switch (category) {
      case 'numeric': return 'bg-blue-100 text-blue-800';
      case 'letter': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Evaluation System</h1>
            <p className="text-gray-600 mt-2">
              Comprehensive overview of grading systems and evaluation methods
            </p>
          </div>
          <Calculator className="h-8 w-8 text-blue-600" />
        </div>

        {/* Statistics Overview */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.total_records.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">Grade entries in database</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Evaluation Systems</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systems.length}</div>
                <p className="text-xs text-muted-foreground">Active grading systems</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Grade Types</CardTitle>
                <Info className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{gradeDictionary.length}</div>
                <p className="text-xs text-muted-foreground">Available grade codes</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Grade Dictionary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Grade Dictionary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {gradeDictionary.map((grade) => (
                <div key={grade.id} className="flex items-center gap-2">
                  <Badge className={getGradeTypeColor(grade.category)}>
                    {grade.code}
                  </Badge>
                  <span className="text-sm text-gray-600">
                    {grade.name_en || grade.name_ru || 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Evaluation Systems */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-900">Evaluation Systems</h2>
          
          {systems.map((system) => (
            <Card key={system.name} className="overflow-hidden">
              <Collapsible
                open={expandedSystems[system.name]}
                onOpenChange={() => toggleSystemExpansion(system.name)}
              >
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    className="w-full p-6 h-auto justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center space-x-4">
                      <Badge className={getSystemColor(system.name)}>
                        {system.name}
                      </Badge>
                      <div className="text-left">
                        <div className="font-semibold text-lg">{system.name} Evaluation System</div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{system.variant_count} variants</span>
                          {system.min_pass_percent && (
                            <span>Pass: {system.min_pass_percent}%</span>
                          )}
                          <span>Formulas: {system.formulas.split(' | ').length}</span>
                        </div>
                      </div>
                    </div>
                    {expandedSystems[system.name] ? (
                      <ChevronUp className="h-5 w-5" />
                    ) : (
                      <ChevronDown className="h-5 w-5" />
                    )}
                  </Button>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <Separator />
                  <div className="p-6 space-y-6">
                    {/* System Overview */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2">System Information</h4>
                        <div className="space-y-1 text-sm">
                          <div>Variants: {system.variant_count}</div>
                          {system.min_pass_percent && (
                            <div>Pass Threshold: {system.min_pass_percent}%</div>
                          )}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2">Available Formulas</h4>
                        <div className="flex flex-wrap gap-1">
                          {system.formulas.split(' | ').map((formula, index) => (
                            <Badge key={`${system.name}-formula-${index}-${formula}`} variant="outline" className="text-xs">
                              {formula}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Detailed Variants */}
                    {systemDetails[system.name] && (
                      <div>
                        <h4 className="font-semibold mb-4">System Variants</h4>
                        <div className="space-y-4">
                          {systemDetails[system.name].map((detail, index) => (
                            <Card key={detail.id} className="border-l-4 border-l-blue-500">
                              <CardContent className="p-4">
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                  <div>
                                    <h5 className="font-medium mb-2">Variant {index + 1}</h5>
                                    <div className="space-y-1 text-sm">
                                      <div>ID: {detail.id}</div>
                                      {detail.successful_pass_percent && (
                                        <div>Pass Rate: {detail.successful_pass_percent}%</div>
                                      )}
                                      <div>Formula (with CW): {detail.formula_with_cw || 'N/A'}</div>
                                      <div>Formula (without CW): {detail.formula_without_cw || 'N/A'}</div>
                                    </div>
                                  </div>
                                  <div>
                                    <h6 className="font-medium mb-2">Grading Scale</h6>
                                    <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                                      {detail.parsed_points.map((point, pointIndex) => (
                                        <Badge
                                          key={`${detail.id}-point-${pointIndex}-${point.code}`}
                                          variant="secondary"
                                          className={getGradeTypeColor(
                                            point.type === 'dictionary' && 
                                            ['QB', 'IE', 'QISH', 'EQB'].includes(point.code) 
                                              ? 'letter' : 'numeric'
                                          )}
                                        >
                                          {point.code}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          ))}
        </div>

        {/* Usage Statistics */}
        {statistics && statistics.usage_by_system.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {statistics.usage_by_system.map((stat) => (
                  <div key={stat.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={getSystemColor(stat.name)}>
                        {stat.name}
                      </Badge>
                      <span>{stat.name} System</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{stat.usage_count.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">records</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  );
}