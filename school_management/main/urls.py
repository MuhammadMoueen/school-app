from django.urls import path, include
from . import views

app_name = 'main'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile Management
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Coordinator/Admin Panel URLs (Custom - separate from Django admin)
    path('coordinator/students/create/', views.admin_create_student, name='coordinator_create_student'),
    path('coordinator/students/', views.admin_manage_students, name='coordinator_manage_students'),
    path('coordinator/students/<int:student_id>/delete/', views.admin_delete_student, name='coordinator_delete_student'),
    path('coordinator/teachers/', views.admin_view_teachers, name='coordinator_view_teachers'),
    
    # Comprehensive Admin URLs (Phase 1 & 2)
    path('panel/teachers/create/', views.admin_create_teacher, name='admin_create_teacher'),
    path('panel/teachers/<int:teacher_id>/delete/', views.admin_delete_teacher, name='admin_delete_teacher'),
    path('panel/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('panel/users/search/', views.admin_search_users, name='admin_search_users'),
    path('panel/bulk/import/', views.admin_bulk_import_students, name='admin_bulk_import'),
    path('panel/export/', views.admin_export_data, name='admin_export_data'),
    path('panel/courses/', views.admin_manage_courses, name='admin_manage_courses'),
    path('panel/courses/<int:course_id>/edit/', views.admin_edit_course, name='admin_edit_course'),
    path('panel/courses/<int:course_id>/delete/', views.admin_delete_course, name='admin_delete_course'),
    path('panel/statistics/', views.admin_statistics, name='admin_statistics'),

    # Admin Hub Pages
    path('panel/students-hub/', views.admin_students_hub, name='admin_students_hub'),
    path('panel/teachers-hub/', views.admin_teachers_hub, name='admin_teachers_hub'),
    path('panel/courses-hub/', views.admin_courses_hub, name='admin_courses_hub'),
    path('panel/search-api/', views.admin_search_api, name='admin_search_api'),
    
    # Teacher URLs
    path('teacher/courses/', views.manage_courses, name='manage_courses'),
    path('teacher/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('teacher/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('teacher/enrollments/', views.manage_enrollments, name='manage_enrollments'),
    path('teacher/enrollments/<int:enrollment_id>/delete/', views.delete_enrollment, name='delete_enrollment'),
    path('teacher/transcripts/', views.manage_transcripts, name='manage_transcripts'),
    path('teacher/transcripts/create/<int:enrollment_id>/', views.create_transcript, name='create_transcript'),
    path('teacher/transcripts/<int:transcript_id>/edit/', views.edit_transcript, name='edit_transcript'),
    path('teacher/transcripts/<int:transcript_id>/delete/', views.delete_transcript, name='delete_transcript'),
    path('teacher/reports/', views.view_reports, name='view_reports'),
    path('teacher/reports/<int:report_id>/', views.report_detail, name='report_detail'),
    
    # Student URLs
    path('student/report/<int:transcript_id>/', views.submit_marks_report, name='submit_marks_report'),
    path('student/reports/<int:report_id>/', views.student_report_detail, name='student_report_detail'),
    
    # Notification URLs
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
