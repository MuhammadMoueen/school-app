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
    path('panel/courses/create/', views.admin_create_course, name='admin_create_course'),
    path('panel/courses/', views.admin_manage_courses, name='admin_manage_courses'),
    path('panel/courses/<int:course_id>/edit/', views.admin_edit_course, name='admin_edit_course'),
    path('panel/courses/<int:course_id>/delete/', views.admin_delete_course, name='admin_delete_course'),
    path('panel/statistics/', views.admin_statistics, name='admin_statistics'),
    path('panel/teachers/activity-logs/', views.admin_teacher_activity_logs, name='admin_teacher_activity_logs'),
    path('panel/notifications/<int:notification_id>/', views.admin_notification_detail, name='admin_notification_detail'),

    # Admin Hub Pages
    path('panel/students-hub/', views.admin_students_hub, name='admin_students_hub'),
    path('panel/teachers-hub/', views.admin_teachers_hub, name='admin_teachers_hub'),
    path('panel/courses-hub/', views.admin_courses_hub, name='admin_courses_hub'),
    path('panel/search-api/', views.admin_search_api, name='admin_search_api'),
    path('panel/students/update-status/', views.update_student_status, name='update_student_status'),
    
    # Teacher URLs
    path('teacher/courses/', views.manage_courses, name='manage_courses'),
    path('teacher/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('teacher/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    
    # Lecture/Material Management URLs
    path('teacher/lectures/', views.manage_lectures, name='manage_lectures'),
    path('teacher/lectures/create/', views.create_lecture, name='create_lecture'),
    path('teacher/lectures/<int:lecture_id>/edit/', views.edit_lecture, name='edit_lecture'),
    path('teacher/lectures/<int:lecture_id>/delete/', views.delete_lecture, name='delete_lecture'),
    path('teacher/lectures/<int:lecture_id>/attachments/<int:attachment_id>/delete/', views.delete_lecture_attachment, name='delete_lecture_attachment'),
    path('teacher/courses/<int:course_id>/lectures/', views.view_course_lectures, name='view_course_lectures'),

    # Assignment Management URLs
    path('teacher/assignments/', views.manage_assignments, name='manage_assignments'),
    path('teacher/assignments/create/', views.create_assignment, name='create_assignment'),
    path('teacher/assignments/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('teacher/assignments/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('teacher/assignments/<int:assignment_id>/attachments/<int:attachment_id>/delete/', views.delete_assignment_attachment, name='delete_assignment_attachment'),
    path('teacher/assignments/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('teacher/assignment-submissions/<int:submission_id>/grade/', views.grade_assignment_submission, name='grade_assignment_submission'),
    
    # Attendance Management URLs
    path('teacher/attendance/', views.manage_attendance, name='manage_attendance'),
    path('teacher/attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('teacher/attendance/report/<int:course_id>/', views.attendance_report, name='attendance_report'),
    
    # Quiz Management URLs
    path('teacher/quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('teacher/quizzes/create/', views.create_quiz, name='create_quiz'),
    path('teacher/quizzes/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('teacher/quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('teacher/quizzes/<int:quiz_id>/questions/', views.add_questions, name='add_questions'),
    path('teacher/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('teacher/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('teacher/quizzes/<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    path('teacher/quiz-attempts/<int:attempt_id>/grade/', views.grade_quiz_attempt, name='grade_quiz_attempt'),
    
    # Analytics & Performance URLs
    path('teacher/analytics/', views.course_analytics, name='course_analytics'),
    path('teacher/admin-chat/', views.teacher_admin_chat, name='teacher_admin_chat'),
    path('teacher/performance/<int:course_id>/', views.student_performance, name='student_performance'),
    
    # Discussion Forum URLs
    path('lectures/<int:lecture_id>/discussions/', views.lecture_discussions, name='lecture_discussions'),
    path('discussions/<int:thread_id>/', views.discussion_detail, name='discussion_detail'),
    path('discussions/<int:thread_id>/resolve/', views.mark_discussion_resolved, name='mark_discussion_resolved'),
    
    path('teacher/enrollments/', views.manage_enrollments, name='manage_enrollments'),
    path('teacher/enrollments/students/', views.get_course_students, name='get_course_students'),
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
    path('student/lectures/<int:lecture_id>/', views.student_lecture_detail, name='student_lecture_detail'),
    path('student/lectures/<int:lecture_id>/download/', views.student_download_lecture_file, name='student_download_lecture_file'),
    path('student/lectures/<int:lecture_id>/attachments/<int:attachment_id>/download/', views.student_download_lecture_attachment, name='student_download_lecture_attachment'),
    path('student/assignments/', views.student_my_assignments, name='student_my_assignments'),
    path('student/assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('student/quizzes/', views.student_my_quizzes, name='student_my_quizzes'),
    path('student/quizzes/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('student/quiz-attempts/<int:attempt_id>/result/', views.student_quiz_result, name='student_quiz_result'),
    
    # Notification URLs
    path('presence/ping/', views.presence_ping, name='presence_ping'),
    path('notifications/get/', views.get_notifications, name='get_notifications')
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
