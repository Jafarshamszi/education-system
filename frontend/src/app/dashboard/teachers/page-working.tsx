"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface PersonInfo {
  id: number;
  firstname?: string | null;
  lastname?: string | null;
  patronymic?: string | null;
  pincode?: string | null;
  birthdate?: string | null;
}

interface ApiTeacher {
  id: number;
  person?: PersonInfo | null;
  organization?: { id: number; name?: string | null; } | null;
  position?: { id: number; name_en?: string | null; name_az?: string | null; } | null;
  staff_type?: { id: number; name_en?: string | null; name_az?: string | null; } | null;
  contract_type?: { id: number; name_en?: string | null; name_az?: string | null; } | null;
  teaching?: number | null;
  is_active?: boolean | null;
}

export default function TeachersTestPage() {
  const [teachers, setTeachers] = useState<ApiTeacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  useEffect(() => {
    const loadTeachers = async () => {
      try {
        setLoading(true);
        setError(null);
        
        setDebugInfo(prev => [...prev, 'Starting to fetch teachers...']);
        console.log('Starting to fetch teachers...');
        
        const response = await fetch('http://localhost:8000/api/v1/teachers/?page=1&per_page=5', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        setDebugInfo(prev => [...prev, `Response status: ${response.status}`]);
        setDebugInfo(prev => [...prev, `Response ok: ${response.ok}`]);
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setDebugInfo(prev => [...prev, `Teachers found: ${data.results?.length || 0}`]);
        console.log('API Response:', data);
        console.log('Teachers found:', data.results?.length || 0);
        
        setTeachers(data.results || []);
      } catch (err) {
        const errorMessage = `Failed to load teachers: ${err}`;
        setError(errorMessage);
        setDebugInfo(prev => [...prev, `ERROR: ${err}`]);
        console.error("Error loading teachers:", err);
      } finally {
        setLoading(false);
      }
    };

    loadTeachers();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading teachers...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      <Card>
        <CardHeader>
          <CardTitle>Teachers Test ({teachers.length} found)</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Debug Info */}
          <div className="mb-4 p-2 bg-gray-100 rounded">
            <h4 className="font-semibold">Debug Info:</h4>
            {debugInfo.map((info, index) => (
              <div key={index} className="text-sm">{info}</div>
            ))}
          </div>
          
          <div className="space-y-4">
            {teachers.slice(0, 5).map((teacher) => (
              <div key={teacher.id} className="p-4 border rounded">
                <div className="font-semibold">
                  {teacher.person ? 
                    `${teacher.person.firstname || ''} ${teacher.person.lastname || ''}`.trim() || 'Unknown'
                    : 'Unknown'}
                </div>
                <div className="text-sm text-gray-600">
                  ID: {teacher.id}
                </div>
                <div className="text-sm text-gray-600">
                  Position: {teacher.position?.name_en || teacher.position?.name_az || 'Unknown'}
                </div>
                <div className="text-sm text-gray-600">
                  Teaching: {teacher.teaching === 1 ? 'Yes' : 'No'}
                </div>
                <div className="text-sm text-gray-600">
                  Active: {teacher.is_active ? 'Yes' : 'No'}
                </div>
                <div className="text-sm text-gray-600">
                  Organization: {teacher.organization?.name || 'Unknown'}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}