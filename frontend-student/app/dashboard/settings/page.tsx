"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function SettingsPage() {
  const [language, setLanguage] = useState<'en' | 'ru' | 'az'>('en');
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>("default");
  const [mounted, setMounted] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Check current notification permission
    if ("Notification" in window) {
      setNotificationPermission(Notification.permission);
    }
    // Load language from localStorage
    const savedLanguage = localStorage.getItem('language') as 'en' | 'ru' | 'az' || 'en';
    setLanguage(savedLanguage);
  }, []);

  const handleLanguageChange = (newLanguage: 'en' | 'ru' | 'az') => {
    setLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const requestNotificationPermission = async () => {
    if (!("Notification" in window)) {
      alert("This browser does not support desktop notifications");
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);

      if (permission === "granted") {
        new Notification("Notifications Enabled", {
          body: "You will now receive notifications from Education System",
          icon: "/favicon.ico",
        });
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
      }
    } catch (error) {
      console.error("Error requesting notification permission:", error);
    }
  };

  // Avoid hydration mismatch by not rendering theme-dependent content until mounted
  if (!mounted) {
    return (
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Loading...</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your preferences and application settings</p>
      </div>

      {showSuccess && (
        <Alert className="bg-green-50 border-green-200">
          <AlertDescription className="text-green-800">
            Settings saved successfully!
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-6">
        {/* Language Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Language Settings</CardTitle>
            <CardDescription>Choose your preferred language</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="language">Select Language</Label>
              <Select value={language} onValueChange={handleLanguageChange}>
                <SelectTrigger id="language">
                  <SelectValue placeholder="Select Language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">
                    <div className="flex items-center gap-2">
                      <span>🇬🇧</span>
                      <span>English</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="ru">
                    <div className="flex items-center gap-2">
                      <span>🇷🇺</span>
                      <span>Russian</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="az">
                    <div className="flex items-center gap-2">
                      <span>🇦🇿</span>
                      <span>Azerbaijani</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm font-medium">Current Language</p>
                <p className="text-xs text-muted-foreground">
                  {language === "en" && "English"}
                  {language === "ru" && "Russian"}
                  {language === "az" && "Azerbaijani"}
                </p>
              </div>
              <Badge variant="outline">
                {language.toUpperCase()}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Notification Settings</CardTitle>
            <CardDescription>Manage how you receive notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm font-medium">Notification Status</p>
                <p className="text-xs text-muted-foreground">
                  {notificationPermission === "granted" && "Enabled"}
                  {notificationPermission === "denied" && "Blocked"}
                  {notificationPermission === "default" && "Disabled"}
                </p>
              </div>
              <Badge
                variant={notificationPermission === "granted" ? "default" : "outline"}
                className={notificationPermission === "granted" ? "bg-green-500" : ""}
              >
                {notificationPermission === "granted" && "Enabled"}
                {notificationPermission === "denied" && "Blocked"}
                {notificationPermission === "default" && "Disabled"}
              </Badge>
            </div>

            {notificationPermission !== "granted" && (
              <div className="space-y-2">
                <Button
                  onClick={requestNotificationPermission}
                  disabled={notificationPermission === "denied"}
                  className="w-full"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    className="mr-2 h-4 w-4"
                  >
                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                  </svg>
                  Enable Notifications
                </Button>
                {notificationPermission === "denied" && (
                  <p className="text-xs text-muted-foreground">
                    Notifications are blocked. Please enable them in your browser settings.
                  </p>
                )}
              </div>
            )}

            {notificationPermission === "granted" && (
              <Alert className="bg-green-50 border-green-200">
                <AlertDescription className="text-green-800">
                  Notifications are enabled. You will receive updates from the Education System.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}