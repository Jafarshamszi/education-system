"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import axios from 'axios';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('No authentication token found. Please login again.');
        setLoading(false);
        return;
      }

      console.log('Fetching user profile with token:', token.substring(0, 20) + '...');
      
      const response = await axios.get('http://localhost:8000/api/v1/auth/user/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Profile response:', response.data);
      
      setUser(response.data);
      setFormData({
        first_name: response.data.first_name || '',
        last_name: response.data.last_name || '',
        email: response.data.email || '',
      });
      setError(null);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          setError('Session expired. Please login again.');
          // Optionally redirect to login
          setTimeout(() => {
            window.location.href = '/login';
          }, 2000);
        } else {
          setError(err.response?.data?.detail || 'Failed to load profile');
        }
      } else {
        setError('Failed to load profile');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setEditing(false);
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
    });
    setError(null);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('No authentication token found. Please login again.');
        return;
      }

      console.log('Updating profile with data:', formData);

      const response = await axios.put(
        'http://localhost:8000/api/v1/auth/user/',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        }
      );

      console.log('Update response:', response.data);

      setUser(response.data);
      
      // Update localStorage with new name
      const fullName = `${response.data.first_name} ${response.data.last_name}`.trim();
      if (fullName) {
        localStorage.setItem('full_name', fullName);
      }
      
      setEditing(false);
    } catch (err) {
      console.error('Failed to update profile:', err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          setError('Session expired. Please login again.');
        } else {
          setError(err.response?.data?.detail || 'Failed to update profile');
        }
      } else {
        setError('Failed to update profile');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-4">
              <Skeleton className="h-20 w-20 rounded-lg" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-64" />
              </div>
            </div>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!user) {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    const userType = localStorage.getItem('user_type');
    
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl space-y-4">
        <Alert variant="destructive">
          <AlertDescription>{error || 'Failed to load profile'}</AlertDescription>
        </Alert>
        
        <Card>
          <CardHeader>
            <CardTitle>Debug Information</CardTitle>
            <CardDescription>LocalStorage contents</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 font-mono text-sm">
            <div>
              <strong>Token:</strong> {token ? `${token.substring(0, 50)}...` : 'NOT FOUND'}
            </div>
            <div>
              <strong>Username:</strong> {username || 'NOT FOUND'}
            </div>
            <div>
              <strong>User Type:</strong> {userType || 'NOT FOUND'}
            </div>
            <Separator className="my-2" />
            <Button onClick={() => window.location.href = '/login'}>
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const userInitials = `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || user.username.substring(0, 2).toUpperCase();
  const userName = `${user.first_name} ${user.last_name}`.trim() || user.username;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Profile</h1>
          <p className="text-muted-foreground mt-2">Manage your personal information and account settings</p>
        </div>
        {!editing && (
          <Button onClick={handleEdit}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round">
              <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
              <path d="M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1" />
              <path d="M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z" />
              <path d="M16 5l3 3" />
            </svg>
            Edit Profile
          </Button>
        )}
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-6">
        {/* Profile Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-4">
              <Avatar className="h-20 w-20 rounded-lg">
                <AvatarFallback className="rounded-lg text-2xl">{userInitials}</AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-2xl">{userName}</CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                    <path d="M3 7a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-10z" />
                    <path d="M3 7l9 6l9 -6" />
                  </svg>
                  {user.email}
                </CardDescription>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant={user.is_active ? "default" : "destructive"}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <Badge variant="outline" className="capitalize">
                    {user.role}
                  </Badge>
                </div>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Personal Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Your basic account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                {editing ? (
                  <Input
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => handleInputChange('first_name', e.target.value)}
                    placeholder="Enter first name"
                  />
                ) : (
                  <div className="p-2 bg-muted rounded-md">{user.first_name}</div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                {editing ? (
                  <Input
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => handleInputChange('last_name', e.target.value)}
                    placeholder="Enter last name"
                  />
                ) : (
                  <div className="p-2 bg-muted rounded-md">{user.last_name}</div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                {editing ? (
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="Enter email"
                  />
                ) : (
                  <div className="p-2 bg-muted rounded-md">{user.email}</div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <div className="p-2 bg-muted rounded-md text-muted-foreground">{user.username}</div>
                <p className="text-xs text-muted-foreground">Username cannot be changed</p>
              </div>
            </div>

            {editing && (
              <>
                <Separator />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={handleCancel} disabled={saving}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round">
                      <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                      <path d="M18 6l-12 12" />
                      <path d="M6 6l12 12" />
                    </svg>
                    Cancel
                  </Button>
                  <Button onClick={handleSave} disabled={saving}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round">
                      <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                      <path d="M5 12l5 5l10 -10" />
                    </svg>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Account Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>Read-only account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>User ID</Label>
                <div className="p-2 bg-muted rounded-md font-mono text-sm">{user.id}</div>
              </div>

              <div className="space-y-2">
                <Label>Account Created</Label>
                <div className="p-2 bg-muted rounded-md">
                  {new Date(user.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Last Updated</Label>
                <div className="p-2 bg-muted rounded-md">
                  {new Date(user.updated_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Role</Label>
                <div className="p-2 bg-muted rounded-md capitalize">{user.role}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
