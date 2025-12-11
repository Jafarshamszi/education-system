'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import axios from 'axios';
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { GraduationCap, AlertCircle } from 'lucide-react';
import { API_ENDPOINTS } from '@/lib/api-config';

const loginSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(1, 'Password is required')
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: ''
    }
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(API_ENDPOINTS.AUTH.LOGIN, {
        username: data.username,
        password: data.password,
        frontend_type: 'student'
      });

      const result = response.data;

      if (result.access_token) {
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('user_id', result.user_id.toString());
        localStorage.setItem('username', result.username);
        localStorage.setItem('user_type', result.user_type);
        if (result.full_name) {
          localStorage.setItem('full_name', result.full_name);
        }
        if (result.email) {
          localStorage.setItem('email', result.email);
        }
      }

      router.push('/dashboard');
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0 bg-gray-900/90 backdrop-blur-md border-gray-800">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form onSubmit={form.handleSubmit(onSubmit)} className="p-6 md:p-8">
            <FieldGroup>
              <div className="flex flex-col items-center gap-2 text-center">
                <div className="rounded-lg bg-white/10 p-3 mb-2">
                  <GraduationCap className="h-10 w-10 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-white">Student Portal</h1>
                <p className="text-gray-400 text-balance">
                  Sign in to access your student dashboard
                </p>
              </div>

              {error && (
                <div className="rounded-md bg-red-950/50 p-4 border border-red-800">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    <p className="text-sm text-red-400">{error}</p>
                  </div>
                </div>
              )}

              <Field>
                <FieldLabel htmlFor="username" className="text-gray-200">Username</FieldLabel>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  disabled={isLoading}
                  className="bg-gray-800/50 border-gray-700 text-white placeholder:text-gray-500"
                  {...form.register('username')}
                />
                {form.formState.errors.username && (
                  <p className="text-sm text-red-400 mt-1">{form.formState.errors.username.message}</p>
                )}
              </Field>

              <Field>
                <div className="flex items-center">
                  <FieldLabel htmlFor="password" className="text-gray-200">Password</FieldLabel>
                  <a
                    href="#"
                    className="ml-auto text-sm underline-offset-2 hover:underline text-gray-400 hover:text-gray-300"
                  >
                    Forgot password?
                  </a>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  disabled={isLoading}
                  className="bg-gray-800/50 border-gray-700 text-white placeholder:text-gray-500"
                  {...form.register('password')}
                />
                {form.formState.errors.password && (
                  <p className="text-sm text-red-400 mt-1">{form.formState.errors.password.message}</p>
                )}
              </Field>

              <Field>
                <Button type="submit" disabled={isLoading} className="w-full">
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </Button>
              </Field>

              <FieldDescription className="text-center text-gray-500">
                Need help? Contact your academic advisor
              </FieldDescription>
            </FieldGroup>
          </form>
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black relative hidden md:flex md:flex-col md:justify-between md:p-8 text-white">
            <div>
              <h2 className="text-3xl font-bold mb-4 text-gray-300">Welcome Student!</h2>
              <p className="text-lg text-gray-400">
                Access your courses, view grades, check schedules, and manage your academic journey.
              </p>
            </div>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-white/10 p-2">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-300">Course Materials</h3>
                  <p className="text-sm text-gray-500">Access all your course content and resources</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-white/10 p-2">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-300">Academic Progress</h3>
                  <p className="text-sm text-gray-500">Track your grades and performance</p>
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500">© 2025 Education System. All rights reserved.</p>
          </div>
        </CardContent>
      </Card>
      <FieldDescription className="px-6 text-center text-gray-500">
        By continuing, you agree to our Terms of Service and Privacy Policy
      </FieldDescription>
    </div>
  )
}
