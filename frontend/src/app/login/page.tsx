'use client';

import { useRouter } from 'next/navigation';
import { GraduationCap, Users, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 p-4">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="rounded-lg bg-white/10 backdrop-blur-sm p-3">
              <GraduationCap className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white">Education System</h1>
          </div>
          <p className="text-white/90 text-lg">Select your portal to continue</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Student Portal */}
          <Card className="cursor-pointer hover:shadow-xl transition-all hover:scale-105" onClick={() => router.push('/login/student')}>
            <CardHeader>
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                <GraduationCap className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle>Student Portal</CardTitle>
              <CardDescription>
                Access your courses, grades, and attendance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                Login as Student
              </Button>
            </CardContent>
          </Card>

          {/* Teacher Portal */}
          <Card className="cursor-pointer hover:shadow-xl transition-all hover:scale-105" onClick={() => router.push('/login/teacher')}>
            <CardHeader>
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
                <Users className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle>Teacher Portal</CardTitle>
              <CardDescription>
                Manage classes, grades, and attendance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                Login as Teacher
              </Button>
            </CardContent>
          </Card>

          {/* Admin Portal */}
          <Card className="cursor-pointer hover:shadow-xl transition-all hover:scale-105" onClick={() => router.push('/login/admin')}>
            <CardHeader>
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-purple-600" />
              </div>
              <CardTitle>Admin Portal</CardTitle>
              <CardDescription>
                System administration and management
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                Login as Admin
              </Button>
            </CardContent>
          </Card>
        </div>

        <p className="text-center text-white/70 mt-8 text-sm">
          Need help? Contact your system administrator
        </p>
      </div>
    </div>
  );
}