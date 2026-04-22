# Information_System/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import StudentViewSet, CourseViewSet, GradeViewSet, IntegrationCourseViewSet, BoardExamAreaViewSet, CustomAuthToken

# Create router for API
router = DefaultRouter()
router.register('students', StudentViewSet)
router.register('courses', CourseViewSet)
router.register('grades', GradeViewSet, basename='grade')
router.register('integration-courses', IntegrationCourseViewSet)
router.register('board-exam-areas', BoardExamAreaViewSet)

urlpatterns = [
    # ========== API ROUTES ==========
    path('api/', include(router.urls)),
    path('api/login/', CustomAuthToken.as_view(), name='api_login'),
    
    # ========== AUTHENTICATION ==========
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('register/', views.signup_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ========== DASHBOARD ROUTES ==========
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),

    # ========== PROFILE ==========
    path('profile/', views.profile_page, name='profile'),

    # ========== PERFORMANCE PAGES ==========
    path('individual/', views.individual_page, name='individual'),
    path('integration/', views.integration_page, name='integration'),
    path('overall/', views.overall_page, name='overall'),
    
    # ========== GRADE MANAGEMENT ==========
    path('grade-management/', views.grade_management, name='grade_management'),
    path('grades-management/', views.grades_management, name='grades_management'),  # ✅ ITO ANG BAGONG IDINAGDAG
    path('choose-grade-type/', views.choose_grade_type, name='choose_grade_type'),
    path('grade-summary/', views.grade_summary, name='grade_summary'),
    
    # ========== UPDATE GRADES ==========
    path('update-grades/', views.update_grades, name='update_grades'),
    path('update_grades/', views.update_grades, name='update_grades'),

    # ========== ADD GRADES ==========
    path('add_individual_grade/', views.add_individual_grade, name='add_individual_grade'),
    path('add-grade/', views.choose_grade_type, name='add_grade'),
    path('add-grade/individual/', views.add_individual_grade, name='add_individual_grade'),
    path('add-grade/integration/', views.add_integration_grade, name='add_integration_grade'),

    # ========== GRADE CALCULATIONS ==========
    path('evaluate-grades/', views.evaluate_grades_view, name='evaluate_grades'),
    path('board-exam-percentage/', views.board_exam_percentage, name='board_exam_percentage'),

    # ========== STUDENT MANAGEMENT ==========
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('students/switch/<int:student_id>/', views.switch_student, name='switch_student'),
    path('students/clear/', views.clear_student, name='clear_student'),

    # ========== ADDITIONAL FEATURES ==========
    path('add-grade/<int:course_id>/<int:day>/<str:grade_value>/', views.add_grade_view, name='add_grade_course'),
    path('student-report/<int:student_id>/', views.student_report, name='student_report'),

    # ========== INTEGRATION SYSTEM ==========
    path('integration-courses/', views.integration_page, name='integration_courses'),
    path('board-exam-readiness/', views.board_exam_readiness, name='board_exam_readiness'),
    
    # ========== DEBUG & SETUP ==========
    path('debug-integration/', views.debug_integration, name='debug_integration'),
    path('setup-integration-system/', views.setup_integration_system, name='setup_integration_system'),
]