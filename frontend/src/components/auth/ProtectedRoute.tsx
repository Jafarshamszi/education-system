'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { ShieldAlert } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: ('STUDENT' | 'TEACHER' | 'ADMIN' | 'SYSADMIN')[];
  redirectTo?: string;
}

export default function ProtectedRoute({ 
  children, 
  allowedRoles,
  redirectTo 
}: ProtectedRouteProps) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [userType, setUserType] = useState<string | null>(null);

  useEffect(() => {
    const checkAuthorization = () => {
      const token = localStorage.getItem('access_token');
      const user_type = localStorage.getItem('user_type');

      // Not logged in - redirect to login
      if (!token || !user_type) {
        router.push('/login');
        return;
      }

      setUserType(user_type);

      // Check if user type is allowed
      const userTypeValue = user_type as 'STUDENT' | 'TEACHER' | 'ADMIN' | 'SYSADMIN';
      if (!allowedRoles.includes(userTypeValue)) {
        setIsAuthorized(false);
        
        // Auto-redirect after showing error message
        if (redirectTo) {
          setTimeout(() => {
            router.push(redirectTo);
          }, 3000);
        } else {
          // Default redirect based on user type
          setTimeout(() => {
            if (user_type === 'STUDENT') {
              router.push('/dashboard/student');
            } else if (user_type === 'TEACHER') {
              router.push('/dashboard/teacher');
            } else if (user_type === 'ADMIN' || user_type === 'SYSADMIN') {
              router.push('/dashboard');
            } else {
              router.push('/login');
            }
          }, 3000);
        }
        return;
      }

      setIsAuthorized(true);
    };

    checkAuthorization();
  }, [router, allowedRoles, redirectTo]);

  // Loading state
  if (isAuthorized === null) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying access...</p>
        </div>
      </div>
    );
  }

  // Unauthorized - show error
  if (!isAuthorized) {
    const errorMessages: Record<string, string> = {
      'STUDENT': 'Students do not have access to this page. Redirecting to your dashboard...',
      'TEACHER': 'Teachers do not have access to this page. Redirecting to your dashboard...',
      'ADMIN': 'You do not have sufficient permissions to access this page. Redirecting...',
      'SYSADMIN': 'You do not have sufficient permissions to access this page. Redirecting...',
    };

    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
        <div className="max-w-md w-full">
          <Alert variant="destructive">
            <ShieldAlert className="h-5 w-5" />
            <AlertTitle className="text-lg font-semibold">Access Denied</AlertTitle>
            <AlertDescription className="mt-2">
              {errorMessages[userType || ''] || 'You do not have permission to access this page.'}
            </AlertDescription>
          </Alert>
          
          <div className="mt-4 flex justify-center">
            <Button 
              onClick={() => router.push('/dashboard')}
              variant="outline"
            >
              Go to Dashboard Now
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Authorized - render children
  return <>{children}</>;
}
