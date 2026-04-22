# Information_System/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    BoardExamArea, Course, IntegrationCourse, CourseMapping,
    Student, Grade
)
from .admin_models import Admin, AdminAuthorization, AdminLoginHistory

# ==================== ADMIN AUTHENTICATION MODELS ====================

class AdminAdmin(admin.ModelAdmin):
    # REMOVED EMAIL FROM LIST_DISPLAY - TANG INA WALA NA!
    list_display = ('username', 'role', 'is_active', 'last_login', 'colored_status')
    list_filter = ('role', 'is_active', 'date_joined')
    # REMOVED EMAIL FROM SEARCH_FIELDS
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Login Info', {
            # REMOVED EMAIL FROM FIELDS
            'fields': ('username', 'password_hash', 'auth_code')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'profile_picture', 'phone_number')
        }),
        ('Admin Details', {
            'fields': ('role', 'department', 'approved_by', 'is_superuser')
        }),
        ('Status', {
            'fields': ('is_active', 'last_login', 'last_login_ip', 'date_joined')
        }),
    )
    
    readonly_fields = ('password_hash', 'last_login', 'date_joined')
    
    def colored_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #27ae60; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #e74c3c; font-weight: bold;">✗ Inactive</span>')
    colored_status.short_description = 'Status'


class AdminAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'created_by', 'created_at', 'expires_at', 'is_used', 'code_status')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('code', 'description', 'created_by__username')
    readonly_fields = ('created_at', 'used_at')
    
    def code_status(self, obj):
        if obj.is_used:
            return format_html('<span style="color: #e74c3c;">Used</span>')
        elif obj.expires_at < timezone.now():
            return format_html('<span style="color: #f39c12;">Expired</span>')
        else:
            return format_html('<span style="color: #27ae60;">Valid</span>')
    code_status.short_description = 'Status'


class AdminLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('admin', 'login_time', 'ip_address', 'login_successful')
    list_filter = ('login_successful', 'login_time')
    search_fields = ('admin__username', 'ip_address')
    readonly_fields = ('login_time',)


# ==================== BOARD EXAM MODELS (STUDENTS ARE HERE!) ====================

class BoardExamAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'schedule', 'courses_count')
    search_fields = ('name',)
    
    def courses_count(self, obj):
        return obj.courses.count()
    courses_count.short_description = 'Courses'


class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'area', 'integrations_count')
    list_filter = ('area',)
    search_fields = ('code', 'title')
    
    def integrations_count(self, obj):
        return obj.integrations.count()
    integrations_count.short_description = 'Integrations'


class IntegrationCourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'period', 'area', 'mapped_courses_count')
    list_filter = ('period', 'area')
    search_fields = ('code', 'title')
    
    def mapped_courses_count(self, obj):
        return obj.mapped_courses.count()
    mapped_courses_count.short_description = 'Mapped Courses'


class CourseMappingAdmin(admin.ModelAdmin):
    list_display = ('integration_course', 'course')
    list_filter = ('integration_course__period', 'integration_course__area')
    search_fields = ('integration_course__title', 'course__title')


class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_number', 'course', 'academic_year', 'grades_count', 'profile_thumbnail')
    list_filter = ('course', 'academic_year')
    search_fields = ('name', 'student_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'student_number', 'course', 'academic_year')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'profile_thumbnail_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def grades_count(self, obj):
        count = obj.grades.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    grades_count.short_description = 'Grades'
    
    def profile_thumbnail(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', 
                             obj.profile_picture.url)
        return format_html('<span style="color: #95a5a6;">No image</span>')
    profile_thumbnail.short_description = 'Photo'
    
    def profile_thumbnail_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 10px;" />', 
                             obj.profile_picture.url)
        return "No profile picture uploaded"
    profile_thumbnail_preview.short_description = 'Profile Preview'


class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_display', 'grade', 'day', 'status', 'remark', 'colored_grade')
    list_filter = ('course_type', 'day', 'status', 'created_at')
    search_fields = ('student__name', 'course__title', 'integration_course__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Grade Information', {
            'fields': ('student', 'course_type', 'grade', 'day')
        }),
        ('Course Details', {
            'fields': ('course', 'integration_course')
        }),
        ('Results', {
            'fields': ('remark', 'status', 'general_average', 'overall_result')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_display(self, obj):
        if obj.course:
            return obj.course.code
        elif obj.integration_course:
            return f"{obj.integration_course.code} (Integration)"
        return "N/A"
    course_display.short_description = 'Course'
    
    def colored_grade(self, obj):
        if obj.grade >= 75:
            color = '#27ae60'  # Green
        elif obj.grade > 0:
            color = '#e74c3c'  # Red
        else:
            color = '#95a5a6'  # Gray
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, obj.grade)
    colored_grade.short_description = 'Grade'


# ==================== REGISTER ALL MODELS ====================

# Register admin authentication models
admin.site.register(Admin, AdminAdmin)
admin.site.register(AdminAuthorization, AdminAuthorizationAdmin)
admin.site.register(AdminLoginHistory, AdminLoginHistoryAdmin)

# Register board exam models (STUDENTS INCLUDED!)
admin.site.register(Student, StudentAdmin)
admin.site.register(BoardExamArea, BoardExamAreaAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(IntegrationCourse, IntegrationCourseAdmin)
admin.site.register(CourseMapping, CourseMappingAdmin)
admin.site.register(Grade, GradeAdmin)