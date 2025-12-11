"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

type Language = 'en' | 'ru' | 'az';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  isLoading: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('az');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load language preference from backend on mount
    const fetchUserLanguage = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const response = await axios.get('http://localhost:8000/api/v1/user-preferences/', {
            headers: { Authorization: `Bearer ${token}` }
          });
          const userLang = response.data.language as Language;
          if (userLang && ['en', 'ru', 'az'].includes(userLang)) {
            setLanguageState(userLang);
            localStorage.setItem('language', userLang);
          }
        } else {
          // If not logged in, use localStorage
          const savedLanguage = localStorage.getItem('language') as Language;
          if (savedLanguage && ['en', 'ru', 'az'].includes(savedLanguage)) {
            setLanguageState(savedLanguage);
          }
        }
      } catch (error) {
        console.error('Failed to fetch user language preference:', error);
        // Fallback to localStorage
        const savedLanguage = localStorage.getItem('language') as Language;
        if (savedLanguage && ['en', 'ru', 'az'].includes(savedLanguage)) {
          setLanguageState(savedLanguage);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserLanguage();
  }, []);

  const setLanguage = async (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);

    // Save to backend if user is logged in
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await axios.put(
          'http://localhost:8000/api/v1/user-preferences/language',
          { language: lang },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (error) {
      console.error('Failed to save language preference to backend:', error);
    }
  };

  const t = (key: string): string => {
    return translations[language]?.[key] || translations.en[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isLoading }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

// Translations object
const translations: Record<Language, Record<string, string>> = {
  en: {
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.retry': 'Retry',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.edit': 'Edit',
    'common.delete': 'Delete',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.export': 'Export',
    'common.import': 'Import',
    'common.enabled': 'Enabled',
    'common.disabled': 'Disabled',
    'common.blocked': 'Blocked',

    // Dashboard
    'dashboard.title': 'Dashboard',
    'dashboard.description': 'System overview and statistics',
    'dashboard.welcome': 'System overview and statistics',
    'dashboard.totalStudents': 'Total Students',
    'dashboard.totalTeachers': 'Total Teachers',
    'dashboard.totalCourses': 'Total Courses',
    'dashboard.enrollments': 'Enrollments',
    'dashboard.pendingRequests': 'Pending Requests',
    'dashboard.faculties': 'Faculties',
    'dashboard.departments': 'Departments',
    'dashboard.enrolledStudents': 'Enrolled students',
    'dashboard.activeFaculty': 'Active faculty members',
    'dashboard.activeFacultyMembers': 'Active faculty members',
    'dashboard.availableCourses': 'Available courses',
    'dashboard.activeEnrollments': 'Active enrollments',
    'dashboard.awaitingReview': 'Awaiting review',
    'dashboard.activeFaculties': 'Active faculties',
    'dashboard.academicDepartments': 'Academic departments',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.latestUpdates': 'Latest updates from your system',
    'dashboard.quickStats': 'Quick Stats',
    'dashboard.performanceMetrics': 'System performance metrics',
    'dashboard.systemPerformance': 'System performance metrics',
    'dashboard.studentAttendance': 'Student Attendance',
    'dashboard.courseCompletion': 'Course Completion',
    'dashboard.facultyUtilization': 'Faculty Utilization',
    'dashboard.noRecentActivity': 'No recent activity',

    // Sidebar
    'sidebar.dashboard': 'Dashboard',
    'sidebar.academicManagement': 'Academic Management',
    'sidebar.students': 'Students',
    'sidebar.teachers': 'Teachers',
    'sidebar.studentGroups': 'Student Groups',
    'sidebar.evaluationSystem': 'Evaluation System',
    'sidebar.curriculumPlanning': 'Curriculum & Planning',
    'sidebar.educationPlans': 'Education Plans',
    'sidebar.curriculum': 'Curriculum',
    'sidebar.academicSchedule': 'Academic Schedule',
    'sidebar.classSchedule': 'Class Schedule',
    'sidebar.administration': 'Administration',
    'sidebar.requests': 'Requests',
    'sidebar.studentOrders': 'Student Orders',
    'sidebar.organization': 'Organization',
    'sidebar.analytics': 'Analytics',
    'sidebar.settings': 'Settings',
    'sidebar.search': 'Search',
    'sidebar.profile': 'Profile',
    'sidebar.notifications': 'Notifications',
    'sidebar.logout': 'Log out',

    // Settings
    'settings.title': 'Settings',
    'settings.description': 'Manage your application preferences and settings',
    'settings.appearance': 'Appearance',
    'settings.appearanceDescription': 'Customize the look and feel of your application',
    'settings.theme': 'Theme',
    'settings.themeDescription': 'Select your preferred theme',
    'settings.light': 'Light',
    'settings.dark': 'Dark',
    'settings.system': 'System',
    'settings.language': 'Language',
    'settings.languageSettings': 'Language Settings',
    'settings.languageDescription': 'Choose your preferred language',
    'settings.selectLanguage': 'Select Language',
    'settings.english': 'English',
    'settings.russian': 'Russian',
    'settings.azerbaijani': 'Azerbaijani',
    'settings.notifications': 'Notifications',
    'settings.notificationSettings': 'Notification Settings',
    'settings.notificationsDescription': 'Manage notification preferences',
    'settings.enableNotifications': 'Enable Notifications',
    'settings.notificationStatus': 'Notification Status',
    'settings.saved': 'Settings saved successfully!',
    'settings.settingsSaved': 'Settings saved successfully!',
    'settings.notificationsBlocked': 'Notifications are blocked. Please enable them in your browser settings.',
    'settings.notificationsEnabled': 'Notifications are enabled. You will receive updates from the Education System.',
    'settings.about': 'About',
    'settings.applicationInfo': 'Application information',
    'settings.version': 'Version',
    'settings.build': 'Build',
    'settings.environment': 'Environment',
    'settings.development': 'Development',

    // Profile
    'profile.title': 'Profile',
    'profile.description': 'Manage your personal information and account settings',
    'profile.editProfile': 'Edit Profile',
    'profile.personalInfo': 'Personal Information',
    'profile.personalInfoDescription': 'Your basic account information',
    'profile.accountInfo': 'Account Information',
    'profile.accountInfoDescription': 'Read-only account details',
    'profile.firstName': 'First Name',
    'profile.lastName': 'Last Name',
    'profile.email': 'Email',
    'profile.username': 'Username',
    'profile.usernameNote': 'Username cannot be changed',
    'profile.userId': 'User ID',
    'profile.accountCreated': 'Account Created',
    'profile.lastUpdated': 'Last Updated',
    'profile.role': 'Role',
    'profile.active': 'Active',
    'profile.inactive': 'Inactive',
    'profile.saving': 'Saving...',
    'profile.saveChanges': 'Save Changes',
  },
  ru: {
    // Common
    'common.loading': 'Загрузка...',
    'common.error': 'Ошибка',
    'common.retry': 'Повторить',
    'common.save': 'Сохранить',
    'common.cancel': 'Отмена',
    'common.edit': 'Редактировать',
    'common.delete': 'Удалить',
    'common.search': 'Поиск',
    'common.filter': 'Фильтр',
    'common.export': 'Экспорт',
    'common.import': 'Импорт',
    'common.enabled': 'Включено',
    'common.disabled': 'Отключено',
    'common.blocked': 'Заблокировано',

    // Dashboard
    'dashboard.title': 'Панель управления',
    'dashboard.description': 'Обзор системы и статистика',
    'dashboard.welcome': 'Обзор системы и статистика',
    'dashboard.totalStudents': 'Всего студентов',
    'dashboard.totalTeachers': 'Всего преподавателей',
    'dashboard.totalCourses': 'Всего курсов',
    'dashboard.enrollments': 'Записи',
    'dashboard.pendingRequests': 'Ожидающие запросы',
    'dashboard.faculties': 'Факультеты',
    'dashboard.departments': 'Кафедры',
    'dashboard.enrolledStudents': 'Зачисленные студенты',
    'dashboard.activeFaculty': 'Активные преподаватели',
    'dashboard.activeFacultyMembers': 'Активные преподаватели',
    'dashboard.availableCourses': 'Доступные курсы',
    'dashboard.activeEnrollments': 'Активные записи',
    'dashboard.awaitingReview': 'Ожидают рассмотрения',
    'dashboard.activeFaculties': 'Активные факультеты',
    'dashboard.academicDepartments': 'Академические кафедры',
    'dashboard.recentActivity': 'Последняя активность',
    'dashboard.latestUpdates': 'Последние обновления системы',
    'dashboard.quickStats': 'Быстрая статистика',
    'dashboard.performanceMetrics': 'Показатели системы',
    'dashboard.systemPerformance': 'Показатели системы',
    'dashboard.studentAttendance': 'Посещаемость студентов',
    'dashboard.courseCompletion': 'Завершение курсов',
    'dashboard.facultyUtilization': 'Загрузка преподавателей',
    'dashboard.noRecentActivity': 'Нет последней активности',

    // Sidebar
    'sidebar.dashboard': 'Панель управления',
    'sidebar.academicManagement': 'Академическое управление',
    'sidebar.students': 'Студенты',
    'sidebar.teachers': 'Преподаватели',
    'sidebar.studentGroups': 'Группы студентов',
    'sidebar.evaluationSystem': 'Система оценивания',
    'sidebar.curriculumPlanning': 'Учебный план',
    'sidebar.educationPlans': 'Образовательные планы',
    'sidebar.curriculum': 'Учебная программа',
    'sidebar.academicSchedule': 'Академическое расписание',
    'sidebar.classSchedule': 'Расписание занятий',
    'sidebar.administration': 'Администрирование',
    'sidebar.requests': 'Запросы',
    'sidebar.studentOrders': 'Приказы студентов',
    'sidebar.organization': 'Организация',
    'sidebar.analytics': 'Аналитика',
    'sidebar.settings': 'Настройки',
    'sidebar.search': 'Поиск',
    'sidebar.profile': 'Профиль',
    'sidebar.notifications': 'Уведомления',
    'sidebar.logout': 'Выйти',

    // Settings
    'settings.title': 'Настройки',
    'settings.description': 'Управление настройками приложения',
    'settings.appearance': 'Внешний вид',
    'settings.appearanceDescription': 'Настройте внешний вид приложения',
    'settings.theme': 'Тема',
    'settings.themeDescription': 'Выберите предпочитаемую тему',
    'settings.light': 'Светлая',
    'settings.dark': 'Темная',
    'settings.system': 'Системная',
    'settings.language': 'Язык',
    'settings.languageSettings': 'Настройки языка',
    'settings.languageDescription': 'Выберите предпочитаемый язык',
    'settings.selectLanguage': 'Выберите язык',
    'settings.english': 'Английский',
    'settings.russian': 'Русский',
    'settings.azerbaijani': 'Азербайджанский',
    'settings.notifications': 'Уведомления',
    'settings.notificationSettings': 'Настройки уведомлений',
    'settings.notificationsDescription': 'Управление настройками уведомлений',
    'settings.enableNotifications': 'Включить уведомления',
    'settings.notificationStatus': 'Статус уведомлений',
    'settings.saved': 'Настройки сохранены успешно!',
    'settings.settingsSaved': 'Настройки сохранены успешно!',
    'settings.notificationsBlocked': 'Уведомления заблокированы. Пожалуйста, включите их в настройках браузера.',
    'settings.notificationsEnabled': 'Уведомления включены. Вы будете получать обновления от системы образования.',
    'settings.about': 'О программе',
    'settings.applicationInfo': 'Информация о приложении',
    'settings.version': 'Версия',
    'settings.build': 'Сборка',
    'settings.environment': 'Окружение',
    'settings.development': 'Разработка',

    // Profile
    'profile.title': 'Профиль',
    'profile.description': 'Управление личной информацией и настройками аккаунта',
    'profile.editProfile': 'Редактировать профиль',
    'profile.personalInfo': 'Личная информация',
    'profile.personalInfoDescription': 'Основная информация о вашем аккаунте',
    'profile.accountInfo': 'Информация об аккаунте',
    'profile.accountInfoDescription': 'Данные аккаунта только для чтения',
    'profile.firstName': 'Имя',
    'profile.lastName': 'Фамилия',
    'profile.email': 'Email',
    'profile.username': 'Имя пользователя',
    'profile.usernameNote': 'Имя пользователя нельзя изменить',
    'profile.userId': 'ID пользователя',
    'profile.accountCreated': 'Аккаунт создан',
    'profile.lastUpdated': 'Последнее обновление',
    'profile.role': 'Роль',
    'profile.active': 'Активный',
    'profile.inactive': 'Неактивный',
    'profile.saving': 'Сохранение...',
    'profile.saveChanges': 'Сохранить изменения',
  },
  az: {
    // Common
    'common.loading': 'Yüklənir...',
    'common.error': 'Xəta',
    'common.retry': 'Yenidən cəhd et',
    'common.save': 'Yadda saxla',
    'common.cancel': 'Ləğv et',
    'common.edit': 'Redaktə et',
    'common.delete': 'Sil',
    'common.search': 'Axtar',
    'common.filter': 'Filtr',
    'common.export': 'İxrac',
    'common.import': 'İdxal',
    'common.enabled': 'Aktiv',
    'common.disabled': 'Deaktiv',
    'common.blocked': 'Bloklanıb',

    // Dashboard
    'dashboard.title': 'İdarə paneli',
    'dashboard.description': 'Sistem icmalı və statistika',
    'dashboard.welcome': 'Sistem icmalı və statistika',
    'dashboard.totalStudents': 'Ümumi tələbələr',
    'dashboard.totalTeachers': 'Ümumi müəllimlər',
    'dashboard.totalCourses': 'Ümumi kurslar',
    'dashboard.enrollments': 'Qeydiyyatlar',
    'dashboard.pendingRequests': 'Gözləyən sorğular',
    'dashboard.faculties': 'Fakültələr',
    'dashboard.departments': 'Kafedralılar',
    'dashboard.enrolledStudents': 'Qeydiyyatdan keçmiş tələbələr',
    'dashboard.activeFaculty': 'Aktiv müəllimlər',
    'dashboard.activeFacultyMembers': 'Aktiv müəllimlər',
    'dashboard.availableCourses': 'Mövcud kurslar',
    'dashboard.activeEnrollments': 'Aktiv qeydiyyatlar',
    'dashboard.awaitingReview': 'Nəzərdən keçirilməyi gözləyir',
    'dashboard.activeFaculties': 'Aktiv fakültələr',
    'dashboard.academicDepartments': 'Akademik kafedralılar',
    'dashboard.recentActivity': 'Son fəaliyyət',
    'dashboard.latestUpdates': 'Sistemdən son yeniləmələr',
    'dashboard.quickStats': 'Sürətli statistika',
    'dashboard.performanceMetrics': 'Sistem göstəriciləri',
    'dashboard.systemPerformance': 'Sistem göstəriciləri',
    'dashboard.studentAttendance': 'Tələbə iştirakı',
    'dashboard.courseCompletion': 'Kurs başa çatma',
    'dashboard.facultyUtilization': 'Müəllim istifadəsi',
    'dashboard.noRecentActivity': 'Son fəaliyyət yoxdur',

    // Sidebar
    'sidebar.dashboard': 'İdarə paneli',
    'sidebar.academicManagement': 'Akademik idarəetmə',
    'sidebar.students': 'Tələbələr',
    'sidebar.teachers': 'Müəllimlər',
    'sidebar.studentGroups': 'Tələbə qrupları',
    'sidebar.evaluationSystem': 'Qiymətləndirmə sistemi',
    'sidebar.curriculumPlanning': 'Kurrikulum və planlaşdırma',
    'sidebar.educationPlans': 'Təhsil planları',
    'sidebar.curriculum': 'Kurrikulum',
    'sidebar.academicSchedule': 'Akademik cədvəl',
    'sidebar.classSchedule': 'Dərs cədvəli',
    'sidebar.administration': 'İnzibatçılıq',
    'sidebar.requests': 'Sorğular',
    'sidebar.studentOrders': 'Tələbə əmrləri',
    'sidebar.organization': 'Təşkilat',
    'sidebar.analytics': 'Analitika',
    'sidebar.settings': 'Parametrlər',
    'sidebar.search': 'Axtar',
    'sidebar.profile': 'Profil',
    'sidebar.notifications': 'Bildirişlər',
    'sidebar.logout': 'Çıxış',

    // Settings
    'settings.title': 'Parametrlər',
    'settings.description': 'Tətbiq parametrlərini idarə edin',
    'settings.appearance': 'Görünüş',
    'settings.appearanceDescription': 'Tətbiqin görünüşünü fərdiləşdirin',
    'settings.theme': 'Tema',
    'settings.themeDescription': 'Üstünlük verdiyiniz temanı seçin',
    'settings.light': 'İşıqlı',
    'settings.dark': 'Qaranlıq',
    'settings.system': 'Sistem',
    'settings.language': 'Dil',
    'settings.languageSettings': 'Dil parametrləri',
    'settings.languageDescription': 'Üstünlük verdiyiniz dili seçin',
    'settings.selectLanguage': 'Dil seçin',
    'settings.english': 'İngilis',
    'settings.russian': 'Rus',
    'settings.azerbaijani': 'Azərbaycan',
    'settings.notifications': 'Bildirişlər',
    'settings.notificationSettings': 'Bildiriş parametrləri',
    'settings.notificationsDescription': 'Bildiriş parametrlərini idarə edin',
    'settings.enableNotifications': 'Bildirişləri aktiv et',
    'settings.notificationStatus': 'Bildiriş statusu',
    'settings.saved': 'Parametrlər uğurla yadda saxlanıldı!',
    'settings.settingsSaved': 'Parametrlər uğurla yadda saxlanıldı!',
    'settings.notificationsBlocked': 'Bildirişlər bloklanıb. Zəhmət olmasa brauzer parametrlərində onları aktiv edin.',
    'settings.notificationsEnabled': 'Bildirişlər aktiv edilib. Təhsil sistemindən yeniləmələr alacaqsınız.',
    'settings.about': 'Haqqında',
    'settings.applicationInfo': 'Tətbiq məlumatı',
    'settings.version': 'Versiya',
    'settings.build': 'Quraşdırma',
    'settings.environment': 'Mühit',
    'settings.development': 'İnkişaf',

    // Profile
    'profile.title': 'Profil',
    'profile.description': 'Şəxsi məlumatları və hesab parametrlərini idarə edin',
    'profile.editProfile': 'Profili redaktə et',
    'profile.personalInfo': 'Şəxsi məlumat',
    'profile.personalInfoDescription': 'Əsas hesab məlumatınız',
    'profile.accountInfo': 'Hesab məlumatı',
    'profile.accountInfoDescription': 'Yalnız oxunulan hesab təfərrüatları',
    'profile.firstName': 'Ad',
    'profile.lastName': 'Soyad',
    'profile.email': 'Email',
    'profile.username': 'İstifadəçi adı',
    'profile.usernameNote': 'İstifadəçi adı dəyişdirilə bilməz',
    'profile.userId': 'İstifadəçi ID',
    'profile.accountCreated': 'Hesab yaradılıb',
    'profile.lastUpdated': 'Son yenilənmə',
    'profile.role': 'Rol',
    'profile.active': 'Aktiv',
    'profile.inactive': 'Qeyri-aktiv',
    'profile.saving': 'Yadda saxlanılır...',
    'profile.saveChanges': 'Dəyişiklikləri yadda saxla',
  },
};
