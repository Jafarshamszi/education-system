from django.urls import path
from . import views

urlpatterns = [
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/stats/', views.teacher_stats, name='teacher-stats'),
    path('teachers/filter-options/', views.filter_options,
         name='teacher-filter-options'),
    path('teachers/<str:pk>/', views.TeacherDetailView.as_view(),
         name='teacher-detail'),
]