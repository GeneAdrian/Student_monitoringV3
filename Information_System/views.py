# Information_System/views.py
import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.urls import reverse
from .models import Grade, Student, Course, IntegrationCourse, BoardExamArea, CourseMapping
from .admin_models import Admin, AdminAuthorization, AdminLoginHistory
from .utils import (
    evaluate_grade, compute_averages, calculate_board_exam_percentage, 
    calculate_integration_grade, calculate_integration_percentage, 
    get_integration_remarks, calculate_board_exam_readiness, 
    get_student_progress_summary, generate_study_recommendations
)


# ==================== AUTHENTICATION VIEWS ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            admin = Admin.objects.get(username=username)
            
            if admin.check_password(password) and admin.is_active:
                AdminLoginHistory.objects.create(
                    admin=admin,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    login_successful=True
                )
                
                admin.backend = 'Information_System.auth_backend.AdminAuthBackend'
                auth_login(request, admin)
                
                if not remember_me:
                    request.session.set_expiry(0)
                
                admin.last_login = timezone.now()
                admin.last_login_ip = ip_address
                admin.save(update_fields=['last_login', 'last_login_ip'])
                
                messages.success(request, f'Welcome back, {admin.get_full_name()}!')
                return redirect('admin_dashboard')
            else:
                try:
                    AdminLoginHistory.objects.create(
                        admin=admin,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        login_successful=False
                    )
                except:
                    pass
                messages.error(request, 'Invalid password or account is inactive.')
                
        except Admin.DoesNotExist:
            messages.error(request, 'No account found with that username.')
    
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        auth_code = request.POST.get('auth_code')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        ADMIN_CODE = getattr(settings, 'ADMIN_SIGNUP_CODE', 'ADMIN123')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif Admin.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            if auth_code == ADMIN_CODE:
                admin = Admin.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    role='admin'
                )
                admin.set_password(password)
                admin.save()
                
                messages.success(request, "Account created successfully! You can now log in.")
                return redirect('login')
            else:
                try:
                    auth = AdminAuthorization.objects.get(code=auth_code, is_used=False)
                    if auth.expires_at > timezone.now():
                        admin = Admin.objects.create(
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                            auth_code=auth_code,
                            is_active=True,
                            role='admin'
                        )
                        admin.set_password(password)
                        admin.save()
                        
                        auth.is_used = True
                        auth.used_by = admin
                        auth.used_at = timezone.now()
                        auth.save()
                        
                        messages.success(request, "Account created successfully! You can now log in.")
                        return redirect('login')
                    else:
                        messages.error(request, "Authorization code has expired.")
                except AdminAuthorization.DoesNotExist:
                    messages.error(request, "Invalid authorization code.")
    
    return render(request, 'signup.html')


@login_required(login_url='login')
def logout_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, f'You have been logged out.')
    return redirect('login')


# ==================== DASHBOARD VIEWS ====================

@login_required(login_url='login')
def dashboard_router(request):
    return redirect('admin_dashboard')


@login_required(login_url='login')
def dashboard(request):
    return redirect('dashboard_router')


@login_required(login_url='login')
def admin_dashboard(request):
    student_id = request.session.get('active_student_id')
    students = Student.objects.all()
    admins = Admin.objects.all()
    current_admin = request.user

    student = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
            messages.warning(request, "Previous student profile not found. Please select a new student.")
    
    individual_grades = calculate_individual_course_grades(student)
    integration_grades_data = calculate_integration_grades(student)
    
    individual_avg = sum([item['overall_grade'] for item in individual_grades]) / len(individual_grades) if individual_grades else 0
    integration_avg = sum([item['calculated_grade'] for item in integration_grades_data]) / len(integration_grades_data) if integration_grades_data else 0
    overall_avg = (individual_avg + integration_avg) / 2 if individual_avg and integration_avg else 0

    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    
    context = {
        'individual': round(individual_avg, 2),
        'integration': round(integration_avg, 2),
        'overall': round(overall_avg, 2),
        'students': students,
        'admins': admins,
        'active_student': student,
        'total_students': total_students,
        'total_courses': total_courses,
        'is_system_wide': not student,
        'current_admin': current_admin,
    }
    
    if student:
        context.update({
            'name': student.name,
            'number': student.student_number,
            'course': student.course,
            'ay': student.academic_year,
        })
    else:
        context.update({
            'name': 'No Student Selected',
            'number': 'N/A',
            'course': 'N/A', 
            'ay': 'N/A',
        })

    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def faculty_dashboard(request):
    student_id = request.session.get('active_student_id')
    students = Student.objects.all()
    admins = Admin.objects.all()
    current_admin = request.user

    student = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
    
    individual_grades = calculate_individual_course_grades(student)
    integration_grades_data = calculate_integration_grades(student)
    
    individual_avg = sum([item['overall_grade'] for item in individual_grades]) / len(individual_grades) if individual_grades else 0
    integration_avg = sum([item['calculated_grade'] for item in integration_grades_data]) / len(integration_grades_data) if integration_grades_data else 0
    overall_avg = (individual_avg + integration_avg) / 2 if individual_avg and integration_avg else 0

    context = {
        'individual': round(individual_avg, 2),
        'integration': round(integration_avg, 2),
        'overall': round(overall_avg, 2),
        'students': students,
        'admins': admins,
        'active_student': student,
        'user_type': 'faculty',
        'is_system_wide': not student,
        'current_admin': current_admin,
    }
    
    if student:
        context.update({
            'name': student.name,
            'number': student.student_number,
            'course': student.course,
            'ay': student.academic_year,
        })
    else:
        context.update({
            'name': 'No Student Selected',
            'number': 'N/A',
            'course': 'N/A', 
            'ay': 'N/A',
        })

    return render(request, 'dashboard.html', context)


# ==================== GRADING CALCULATOR FUNCTIONS ====================

def calculate_individual_course_grades(student=None, course_code=None):
    courses = Course.objects.all().order_by('code')
    if course_code:
        courses = courses.filter(code=course_code)
    
    results = []
    
    for course in courses:
        grade_filter = {'course': course}
        if student:
            grade_filter['student'] = student
            
        latest_grade = Grade.objects.filter(**grade_filter).order_by('-id').first()
        overall_grade = latest_grade.grade if latest_grade else 0
        
        if overall_grade >= 75:
            status = 'PASSED'
        elif overall_grade > 0:
            status = 'FAILED'
        else:
            status = 'NOT TAKEN'
        
        results.append({
            'course': course,
            'overall_grade': round(overall_grade, 2),
            'status': status,
            'has_grade': overall_grade > 0
        })
    
    return results


def calculate_integration_grades(student=None):
    integration_courses = IntegrationCourse.objects.all()
    results = []
    
    for integration_course in integration_courses:
        integration_grade = integration_course.calculate_integration_grade(student)
        
        if integration_grade >= 75:
            status = 'PASSED'
        elif integration_grade > 0:
            status = 'FAILED'
        else:
            status = 'NOT TAKEN'
        
        results.append({
            'integration_course': integration_course,
            'calculated_grade': round(integration_grade, 2),
            'status': status,
            'mapped_courses_count': integration_course.mapped_courses.count()
        })
    
    return results


# ==================== INDIVIDUAL COURSES PAGE ====================

@login_required(login_url='login')
def individual_page(request):
    student_id = request.GET.get('student_id')
    
    if not student_id:
        student_id = request.session.get('active_student_id')
    
    students = Student.objects.all()
    
    student = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            request.session['active_student_id'] = student.id
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
            messages.error(request, "Student not found!")
    
    active_tab = request.GET.get('tab', 'view')
    
    all_courses = Course.objects.all().select_related('area').order_by('code')
    
    subjects = []
    completed_courses = 0
    all_grades = []
    
    for course in all_courses:
        grade_obj = None
        if student:
            grade_obj = Grade.objects.filter(
                student=student,
                course=course,
                course_type='Individual'
            ).order_by('-id').first()
        
        grade_value = grade_obj.grade if grade_obj else None
        
        if grade_value and grade_value > 0:
            all_grades.append(grade_value)
            if grade_value >= 75:
                completed_courses += 1
            status = 'PASSED' if grade_value >= 75 else 'FAILED'
        else:
            status = 'NOT TAKEN'
        
        if grade_value:
            if grade_value >= 90:
                remark = 'Excellent'
            elif grade_value >= 80:
                remark = 'Very Good'
            elif grade_value >= 75:
                remark = 'Good'
            elif grade_value >= 70:
                remark = 'Satisfactory'
            else:
                remark = 'Needs Improvement'
        else:
            remark = 'Not Yet Taken'
        
        subjects.append({
            'id': course.id,
            'code': course.code,
            'name': course.title,
            'score': grade_value,
            'status': status,
            'remark': remark,
            'area': course.area.name if course.area else None
        })
    
    total_courses = len(all_courses)
    graded_courses = len([s for s in subjects if s['score']])
    average_grade = sum(all_grades) / len(all_grades) if all_grades else 0
    pass_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
    
    context = {
        'page_title': 'Individual Courses',
        'students': students,
        'active_student': student,
        'student_name': student.name if student else 'No Student Selected',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'subjects': subjects,
        'completed_courses': completed_courses,
        'graded_courses': graded_courses,
        'total_courses': total_courses,
        'average_grade': round(average_grade, 1),
        'pass_rate': round(pass_rate, 1),
        'has_data': graded_courses > 0,
        'active_tab': active_tab,
    }
    
    return render(request, 'individual.html', context)


# ==================== INTEGRATION COURSES PAGE ====================

@login_required(login_url='login')
def integration_page(request):
    student_id = request.GET.get('student_id') or request.session.get('active_student_id')
    
    students = Student.objects.all()
    student = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            request.session['active_student_id'] = student.id
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
    
    integration_courses = IntegrationCourse.objects.all().prefetch_related('mapped_courses__course')
    
    integration_courses_data = []
    total_calculated_grade = 0
    valid_courses_count = 0
    
    for ic in integration_courses:
        mappings = CourseMapping.objects.filter(integration_course=ic).select_related('course')
        
        mapped_courses_data = []
        for mapping in mappings:
            course = mapping.course
            group_name = mapping.group_name or "General"
            
            grade_value = 0
            if student:
                grade_obj = Grade.objects.filter(
                    student=student,
                    course=course,
                    course_type='Individual'
                ).order_by('-id').first()
                grade_value = grade_obj.grade if grade_obj else 0
            
            if grade_value >= 75:
                status = 'PASSED'
                color = '#27ae60'
            elif grade_value > 0:
                status = 'FAILED'
                color = '#e74c3c'
            else:
                status = 'NOT TAKEN'
                color = '#95a5a6'
            
            mapped_courses_data.append({
                'code': course.code,
                'title': course.title,
                'grade': grade_value if grade_value > 0 else None,
                'display_grade': f"{grade_value}%" if grade_value > 0 else '--',
                'status': status,
                'color': color,
                'group_name': group_name
            })
        
        grouped_courses = {}
        for course in mapped_courses_data:
            group = course['group_name']
            if group not in grouped_courses:
                grouped_courses[group] = []
            grouped_courses[group].append(course)
        
        calculated_grade = 0
        if student and mapped_courses_data:
            grades = [c['grade'] for c in mapped_courses_data if c['grade'] and c['grade'] > 0]
            if grades:
                calculated_grade = sum(grades) / len(grades)
        
        if calculated_grade > 0:
            total_calculated_grade += calculated_grade
            valid_courses_count += 1
        
        if calculated_grade >= 75:
            status = 'PASSED'
            color = '#27ae60'
        elif calculated_grade > 0:
            status = 'FAILED'
            color = '#e74c3c'
        else:
            status = 'NOT TAKEN'
            color = '#95a5a6'
        
        integration_courses_data.append({
            'code': ic.code,
            'title': ic.title,
            'period': ic.period,
            'calculated_grade': round(calculated_grade, 2) if calculated_grade > 0 else 0,
            'display_grade': f"{round(calculated_grade, 2)}%" if calculated_grade > 0 else '--',
            'status': status,
            'color': color,
            'progress': calculated_grade if calculated_grade > 0 else 0,
            'mapped_courses_count': len(mapped_courses_data),
            'graded_courses_count': len([c for c in mapped_courses_data if c['grade'] and c['grade'] > 0]),
            'grouped_courses': grouped_courses
        })
    
    completed_courses = len([ic for ic in integration_courses_data if ic['status'] == 'PASSED'])
    total_courses = len(integration_courses_data)
    average_grade = total_calculated_grade / valid_courses_count if valid_courses_count > 0 else 0
    pass_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
    
    context = {
        'page_title': 'Integration Courses',
        'students': students,
        'active_student': student,
        'student_name': student.name if student else 'No Student Selected',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'integration_courses': integration_courses_data,
        'completed_courses': completed_courses,
        'total_courses': total_courses,
        'average_grade': round(average_grade, 1),
        'pass_rate': round(pass_rate, 1),
        'has_data': valid_courses_count > 0,
    }
    
    return render(request, 'integration.html', context)


# ==================== OVERALL PERFORMANCE PAGE ====================

@login_required(login_url='login')
def overall_page(request):
    student_id = request.session.get('active_student_id')
    student = None
    students = Student.objects.all()
    
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
    
    individual_grades = calculate_individual_course_grades(student)
    integration_grades_data = calculate_integration_grades(student)
    
    individual_avg = sum([item['overall_grade'] for item in individual_grades]) / len(individual_grades) if individual_grades else 0
    integration_avg = sum([item['calculated_grade'] for item in integration_grades_data]) / len(integration_grades_data) if integration_grades_data else 0
    overall_avg = (individual_avg + integration_avg) / 2 if individual_avg and integration_avg else 0
    
    board_areas = BoardExamArea.objects.all()
    board_areas_data = []
    for area in board_areas:
        board_areas_data.append({
            'name': area.name,
            'schedule': area.schedule,
            'status': 'READY' if overall_avg >= 75 else 'NEEDS REVIEW'
        })
    
    completed_individual = len([g for g in individual_grades if g['overall_grade'] >= 75])
    completed_integration = len([g for g in integration_grades_data if g['calculated_grade'] >= 75])
    completed_courses = completed_individual + completed_integration
    total_courses = len(individual_grades) + len(integration_grades_data)
    
    if overall_avg >= 90:
        remarks = 'Excellent Performance! You are well-prepared for the board exam.'
    elif overall_avg >= 80:
        remarks = 'Very Good Performance. Keep up the good work!'
    elif overall_avg >= 75:
        remarks = 'Good Performance. Focus on improving your weak areas.'
    elif overall_avg >= 60:
        remarks = 'Satisfactory Performance. Need more practice and review.'
    else:
        remarks = 'Needs Significant Improvement. Consider intensive review sessions.'
    
    context = {
        'page_title': 'Overall Performance',
        'students': students,
        'active_student': student,
        'student_name': student.name if student else 'No Student Selected',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'individual': round(individual_avg, 2),
        'integration': round(integration_avg, 2),
        'overall': round(overall_avg, 2),
        'board_areas': board_areas_data,
        'completed_courses': completed_courses,
        'total_courses': total_courses,
        'remarks': remarks,
        # ← These two were missing:
        'individual_grades': individual_grades,
        'integration_grades': integration_grades_data,
    }
    
    return render(request, 'overall.html', context)


# ==================== UPDATE GRADES VIEW ====================

@login_required(login_url='login')
def update_grades(request):
    student_id = request.session.get('active_student_id')
    student = None
    
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
                messages.error(request, "Selected student not found. Please select a student first.")
                return redirect('student_list')
    else:
        messages.error(request, "No student selected. Please select a student first.")
        return redirect('student_list')
    
    courses = Course.objects.all().order_by('code')
    
    existing_grades = {}
    if student:
        grades = Grade.objects.filter(student=student, course_type='Individual')
        for grade in grades:
            existing_grades[grade.course.id] = grade.grade
    
    if request.method == 'POST':
        updated_count = 0
        created_count = 0
        csv_imported = 0
        csv_errors = []

        csv_file = request.FILES.get('grades_csv')
        if csv_file:
            try:
                decoded_file = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded_file))

                if not reader.fieldnames:
                    raise ValueError('CSV file is missing header row.')

                for row_idx, row in enumerate(reader, start=2):
                    raw_course = (row.get('course_code') or row.get('code') or row.get('course_id'))
                    raw_grade = (row.get('grade') or row.get('grade_value') or row.get('score'))

                    if not raw_course or not raw_grade:
                        csv_errors.append(f'Row {row_idx}: Missing course or grade.')
                        continue

                    course = None
                    if raw_course.isdigit():
                        course = Course.objects.filter(id=int(raw_course)).first()
                    if not course:
                        course = Course.objects.filter(code__iexact=raw_course.strip()).first()

                    if not course:
                        csv_errors.append(f'Row {row_idx}: Course "{raw_course}" not found.')
                        continue

                    try:
                        grade_float = float(raw_grade)
                    except (ValueError, TypeError):
                        csv_errors.append(f'Row {row_idx}: Invalid grade "{raw_grade}".')
                        continue

                    if not (0 <= grade_float <= 100):
                        csv_errors.append(f'Row {row_idx}: Grade {grade_float} is out of range (0-100).')
                        continue

                    grade_obj = Grade.objects.filter(
                        student=student,
                        course=course,
                        course_type='Individual'
                    ).order_by('-id').first()

                    if grade_obj:
                        grade_obj.grade = grade_float
                        grade_obj.save()
                        updated_count += 1
                    else:
                        Grade.objects.create(
                            student=student,
                            course=course,
                            course_type='Individual',
                            grade=grade_float
                        )
                        created_count += 1

                    csv_imported += 1

            except Exception as e:
                messages.error(request, f'Failed to process CSV: {str(e)}')

        for course in courses:
            grade_key = f"grade_{course.id}"
            grade_value = request.POST.get(grade_key)
            
            if grade_value and grade_value.strip():
                try:
                    grade_float = float(grade_value)
                    
                    if 0 <= grade_float <= 100:
                        grade_obj = Grade.objects.filter(
                            student=student,
                            course=course,
                            course_type='Individual'
                        ).order_by('-id').first()
                        
                        if grade_obj:
                            grade_obj.grade = grade_float
                            grade_obj.save()
                            updated_count += 1
                        else:
                            Grade.objects.create(
                                student=student,
                                course=course,
                                course_type='Individual',
                                grade=grade_float
                            )
                            created_count += 1
                except (ValueError, TypeError):
                    continue
        
        if csv_imported > 0:
            messages.success(request, f"CSV import complete: {csv_imported} rows processed.")
        if csv_errors:
            messages.warning(request, "CSV import completed with issues: " + "; ".join(csv_errors[:5]) + ("..." if len(csv_errors) > 5 else ""))
        if created_count > 0 or updated_count > 0:
            messages.success(
                request, 
                f"Grades updated successfully! {created_count} new grades added, {updated_count} grades updated."
            )
        elif not csv_file:
            messages.info(request, "No grades were updated.")
        
        return redirect('update_grades')
    
    course_data = []
    for course in courses:
        current_grade = existing_grades.get(course.id, '')
        
        if current_grade:
            try:
                grade_float = float(current_grade)
                status = 'PASSED' if grade_float >= 75 else 'FAILED'
                color = '#27ae60' if grade_float >= 75 else '#e74c3c'
            except (ValueError, TypeError):
                status = 'NOT TAKEN'
                color = '#95a5a6'
        else:
            status = 'NOT TAKEN'
            color = '#95a5a6'
            
        course_info = {
            'course': course,
            'current_grade': current_grade,
            'status': status,
            'color': color
        }
            
        course_data.append(course_info)
    
    total_courses = len(course_data)
    
    completed_courses = 0
    graded_courses = []
    
    for course_info in course_data:
        if course_info['current_grade']:
            try:
                grade_float = float(course_info['current_grade'])
                if grade_float >= 75:
                    completed_courses += 1
                graded_courses.append(grade_float)
            except (ValueError, TypeError):
                continue
    
    pending_courses = total_courses - len([c for c in course_data if c['current_grade']])
    average_grade = sum(graded_courses) / len(graded_courses) if graded_courses else 0
    
    context = {
        'page_title': 'Update Grades',
        'student': student,
        'student_name': student.name if student else 'Student',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'course_data': course_data,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'pending_courses': pending_courses,
        'average_grade': round(average_grade, 1),
        'completion_rate': round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0,
    }
    
    return render(request, 'update_grades.html', context)


# ==================== GRADES MANAGEMENT VIEW ====================

@login_required(login_url='login')
def grades_management(request):
    student_id = request.GET.get('student_id') or request.session.get('active_student_id')
    student = None
    
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            request.session['active_student_id'] = student.id
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
            messages.error(request, "Student not found. Please select a student first.")
            return redirect('student_list')
    else:
        messages.error(request, "No student selected. Please select a student first.")
        return redirect('student_list')
    
    courses = Course.objects.all().order_by('code')
    
    existing_grades = {}
    if student:
        grades = Grade.objects.filter(student=student, course_type='Individual')
        for grade in grades:
            existing_grades[grade.course.id] = grade.grade
    
    if request.method == 'POST':
        updated_count = 0
        created_count = 0
        csv_imported = 0
        csv_errors = []

        csv_file = request.FILES.get('grades_csv')
        if csv_file:
            try:
                decoded_file = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded_file))

                if not reader.fieldnames:
                    raise ValueError('CSV file is missing header row.')

                for row_idx, row in enumerate(reader, start=2):
                    raw_course = (row.get('course_code') or row.get('code') or row.get('course_id'))
                    raw_grade = (row.get('grade') or row.get('grade_value') or row.get('score'))

                    if not raw_course or not raw_grade:
                        csv_errors.append(f'Row {row_idx}: Missing course or grade.')
                        continue

                    course = None
                    if raw_course.isdigit():
                        course = Course.objects.filter(id=int(raw_course)).first()
                    if not course:
                        course = Course.objects.filter(code__iexact=raw_course.strip()).first()

                    if not course:
                        csv_errors.append(f'Row {row_idx}: Course "{raw_course}" not found.')
                        continue

                    try:
                        grade_float = float(raw_grade)
                    except (ValueError, TypeError):
                        csv_errors.append(f'Row {row_idx}: Invalid grade "{raw_grade}".')
                        continue

                    if not (0 <= grade_float <= 100):
                        csv_errors.append(f'Row {row_idx}: Grade {grade_float} is out of range (0-100).')
                        continue

                    grade_obj = Grade.objects.filter(
                        student=student,
                        course=course,
                        course_type='Individual'
                    ).order_by('-id').first()

                    if grade_obj:
                        grade_obj.grade = grade_float
                        grade_obj.save()
                        updated_count += 1
                    else:
                        Grade.objects.create(
                            student=student,
                            course=course,
                            course_type='Individual',
                            grade=grade_float
                        )
                        created_count += 1

                    csv_imported += 1

            except Exception as e:
                messages.error(request, f'Failed to process CSV: {str(e)}')

        for course in courses:
            grade_key = f"grade_{course.id}"
            grade_value = request.POST.get(grade_key)
            
            if grade_value and grade_value.strip():
                try:
                    grade_float = float(grade_value)
                    
                    if 0 <= grade_float <= 100:
                        grade_obj = Grade.objects.filter(
                            student=student,
                            course=course,
                            course_type='Individual'
                        ).order_by('-id').first()
                        
                        if grade_obj:
                            grade_obj.grade = grade_float
                            grade_obj.save()
                            updated_count += 1
                        else:
                            Grade.objects.create(
                                student=student,
                                course=course,
                                course_type='Individual',
                                grade=grade_float
                            )
                            created_count += 1
                except (ValueError, TypeError):
                    continue
        
        if csv_imported > 0:
            messages.success(request, f"CSV import complete: {csv_imported} rows processed.")
        if csv_errors:
            messages.warning(request, "CSV import completed with issues: " + "; ".join(csv_errors[:5]) + ("..." if len(csv_errors) > 5 else ""))
        if created_count > 0 or updated_count > 0:
            messages.success(
                request, 
                f"Grades changed successfully! {created_count} new grades added, {updated_count} grades updated."
            )
        elif not csv_file:
            messages.info(request, "No grades were changed.")
        
        return redirect(f"{reverse('grades_management')}?student_id={student.id}")
    
    course_data = []
    for course in courses:
        current_grade = existing_grades.get(course.id, '')
        
        if current_grade:
            try:
                grade_float = float(current_grade)
                status = 'PASSED' if grade_float >= 75 else 'FAILED'
                color = '#27ae60' if grade_float >= 75 else '#e74c3c'
            except (ValueError, TypeError):
                status = 'NOT TAKEN'
                color = '#95a5a6'
        else:
            status = 'NOT TAKEN'
            color = '#95a5a6'
            
        course_info = {
            'course': course,
            'current_grade': current_grade,
            'status': status,
            'color': color
        }
            
        course_data.append(course_info)
    
    total_courses = len(course_data)
    
    completed_courses = 0
    graded_courses = []
    
    for course_info in course_data:
        if course_info['current_grade']:
            try:
                grade_float = float(course_info['current_grade'])
                if grade_float >= 75:
                    completed_courses += 1
                graded_courses.append(grade_float)
            except (ValueError, TypeError):
                continue
    
    pending_courses = total_courses - len([c for c in course_data if c['current_grade']])
    average_grade = sum(graded_courses) / len(graded_courses) if graded_courses else 0
    
    context = {
        'page_title': 'Grades Management',
        'student': student,
        'student_name': student.name if student else 'Student',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'course_data': course_data,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'pending_courses': pending_courses,
        'average_grade': round(average_grade, 1),
        'completion_rate': round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0,
    }
    
    return render(request, 'grades_management.html', context)


# ==================== ADD INDIVIDUAL GRADE ====================

@login_required(login_url='login')
def add_individual_grade(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id') or request.session.get('active_student_id')
        course_code = request.POST.get('course')
        grade_value = request.POST.get('grade')
        
        if not student_id:
            messages.error(request, "No student selected!")
            return redirect('individual')
        
        try:
            student = Student.objects.get(id=student_id)
            course = Course.objects.get(code=course_code)
            grade_float = float(grade_value)
            
            if 0 <= grade_float <= 100:
                remark, status = evaluate_grade(grade_float)
                
                existing_grade = Grade.objects.filter(
                    student=student,
                    course=course,
                    course_type='Individual'
                ).first()
                
                if existing_grade:
                    existing_grade.grade = grade_float
                    existing_grade.remark = remark
                    existing_grade.status = status
                    existing_grade.save()
                    messages.success(request, f"Grade updated for {course.title}!")
                else:
                    Grade.objects.create(
                        student=student,
                        course=course,
                        course_type='Individual',
                        grade=grade_float,
                        remark=remark,
                        status=status
                    )
                    messages.success(request, f"Grade added for {course.title}!")
                
                request.session['active_student_id'] = student.id
                
                return redirect(f"{reverse('individual')}?student_id={student.id}&tab=view")
            else:
                messages.error(request, "Grade must be between 0 and 100!")
                
        except Student.DoesNotExist:
            messages.error(request, "Student not found!")
        except Course.DoesNotExist:
            messages.error(request, "Course not found!")
        except ValueError:
            messages.error(request, "Invalid grade value!")
        except Exception as e:
            messages.error(request, f"Error saving grade: {str(e)}")
    
    return redirect('individual')


# ==================== CHOOSE GRADE TYPE ====================

@login_required(login_url='login')
def choose_grade_type(request):
    return render(request, 'choose_grade_type.html')


# ==================== ADD INTEGRATION GRADE ====================

@login_required(login_url='login')
def add_integration_grade(request):
    integration_courses = IntegrationCourse.objects.all()
    if request.method == 'POST':
        course_id = request.POST.get('course')
        grade_value = float(request.POST.get('grade'))
        course = get_object_or_404(IntegrationCourse, id=course_id)
        remark, status = evaluate_grade(grade_value)

        Grade.objects.create(
            course_type='Integration',
            integration_course=course,
            grade=grade_value,
            remark=remark,
            status=status,
        )
        messages.success(request, f"{course.title} integration grade added successfully!")
        return redirect('integration')

    return render(request, 'add_integration_grade.html', {'integration_courses': integration_courses})


# ==================== EVALUATE GRADES ====================

@login_required(login_url='login')
def evaluate_grades_view(request):
    student_id = request.session.get('active_student_id')
    student = Student.objects.get(id=student_id) if student_id else None
    
    if request.method == 'POST':
        subjects = request.POST.getlist('course_name')
        grades = request.POST.getlist('grade')
        course_types = request.POST.getlist('course_type')

        records = []
        for i in range(len(subjects)):
            g = float(grades[i])
            t = course_types[i]
            remark, status = evaluate_grade(g)
            records.append({
                'subject': subjects[i], 
                'type': t, 
                'grade': g, 
                'remark': remark, 
                'status': status
            })

        avg_individual, avg_integration, overall_avg, overall_status = compute_averages(records)

        for rec in records:
            if rec['type'] == 'Individual':
                course = Course.objects.filter(title=rec['subject']).first()
                integration_course = None
            else:
                course = None
                integration_course = IntegrationCourse.objects.filter(title=rec['subject']).first()

            Grade.objects.create(
                course_type=rec['type'],
                course=course,
                integration_course=integration_course,
                student=student,
                grade=rec['grade'],
                remark=rec['remark'],
                status=rec['status'],
                general_average=overall_avg,
                overall_result=overall_status
            )

        return render(request, 'result.html', {
            'records': records,
            'avg_individual': avg_individual,
            'avg_integration': avg_integration,
            'overall_avg': overall_avg,
            'overall_status': overall_status
        })

    courses = Course.objects.all()
    integration_courses = IntegrationCourse.objects.all()
    return render(request, 'grade_form.html', {
        'courses': courses,
        'integration_courses': integration_courses,
    })


# ==================== BOARD EXAM PERCENTAGE ====================

@login_required(login_url='login')
def board_exam_percentage(request):
    if request.method == 'POST':
        total_marks = float(request.POST.get('total_marks'))
        obtained_marks = float(request.POST.get('obtained_marks'))
        percentage, result = calculate_board_exam_percentage(obtained_marks, total_marks)

        context = {'percentage': percentage, 'result': result}
        return render(request, 'board_result.html', context)

    return render(request, 'board_form.html')


# ==================== STUDENT MANAGEMENT ====================

@login_required(login_url='login')
def student_list(request):
    students = Student.objects.all()
    return render(request, 'students.html', {'students': students})


@login_required(login_url='login')
def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        student_number = request.POST.get('student_number')
        course = request.POST.get('course')
        academic_year = request.POST.get('academic_year')

        Student.objects.create(name=name, student_number=student_number, course=course, academic_year=academic_year)
        messages.success(request, 'Student added successfully!')
        return redirect('student_list')

    return render(request, 'add_student.html')


@login_required(login_url='login')
def delete_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        student.delete()
        messages.success(request, f"Student '{student.name}' deleted successfully!")
    except Student.DoesNotExist:
        messages.error(request, "Student not found or already deleted!")
    return redirect('student_list')


@login_required(login_url='login')
def switch_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        request.session['active_student_id'] = student.id
        messages.success(request, f"Switched active student to {student.name}.")
    except Student.DoesNotExist:
        messages.error(request, "Student not found! Cannot switch.")
        if 'active_student_id' in request.session:
            del request.session['active_student_id']
    return redirect('dashboard')


def clear_student(request):
    if 'active_student_id' in request.session:
        del request.session['active_student_id']
        messages.success(request, "Cleared student selection. Viewing system-wide data.")
    return redirect('dashboard')


# ==================== ADD GRADE VIEW ====================

@login_required(login_url='login')
def add_grade_view(request, course_id, grade_value):
    student_id = request.session.get('active_student_id')
    student = Student.objects.get(id=student_id) if student_id else None
    
    course = get_object_or_404(Course, id=course_id)
    
    try:
        grade_float = float(grade_value)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid grade value'})
    
    grade, created = Grade.objects.get_or_create(
        course=course,
        student=student,
        course_type='Individual',
        defaults={'grade': grade_float}
    )
    
    if not created:
        grade.grade = grade_float
        grade.save()
    
    return JsonResponse({'status': 'success', 'grade_id': grade.id})


# ==================== STUDENT REPORT ====================

@login_required(login_url='login')
def student_report(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        
        individual_grades = calculate_individual_course_grades(student)
        integration_grades_data = calculate_integration_grades(student)
        
        context = {
            'student': student,
            'individual_grades': individual_grades,
            'integration_grades': integration_grades_data,
        }
        
        return render(request, 'student_report.html', context)
    except Student.DoesNotExist:
        messages.error(request, "Student not found!")
        return redirect('student_list')


# ==================== GRADE SUMMARY ====================

@login_required(login_url='login')
def grade_summary(request):
    individual_courses = Course.objects.all().prefetch_related('grades')
    
    course_data = []
    for course in individual_courses:
        overall_grade = course.get_overall_grade() or 0
        
        course_data.append({
            'course': course,
            'overall_grade': overall_grade,
            'remark': 'PASSED' if overall_grade >= 75 else ('FAILED' if overall_grade > 0 else 'NOT TAKEN')
        })
    
    integration_courses = IntegrationCourse.objects.all().prefetch_related('mapped_courses__course')
    
    integration_data = []
    for integration_course in integration_courses:
        calculated_grade = integration_course.calculate_integration_grade()
        manual_grades = integration_course.grades.all()
        
        integration_data.append({
            'integration_course': integration_course,
            'calculated_grade': calculated_grade,
            'manual_grades': manual_grades,
            'mapped_courses': integration_course.mapped_courses.all()
        })
    
    all_grades = Grade.objects.filter(course_type='Individual', course__isnull=False)
    overall_avg = all_grades.aggregate(Avg('grade'))['grade__avg'] or 0
    
    context = {
        'course_data': course_data,
        'integration_data': integration_data,
        'overall_avg': overall_avg,
        'total_courses': individual_courses.count(),
        'passed_courses': len([c for c in course_data if c['overall_grade'] >= 75]),
    }
    
    return render(request, 'grade_summary.html', context)


# ==================== GRADE MANAGEMENT ====================

@login_required(login_url='login')
def grade_management(request):
    student_id = request.session.get('active_student_id')
    students = Student.objects.all()

    student = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']
    
    individual_grades = calculate_individual_course_grades(student)
    integration_grades_data = calculate_integration_grades(student)
    
    individual_avg = sum([item['overall_grade'] for item in individual_grades]) / len(individual_grades) if individual_grades else 0
    integration_avg = sum([item['calculated_grade'] for item in integration_grades_data]) / len(integration_grades_data) if integration_grades_data else 0
    overall_avg = (individual_avg + integration_avg) / 2 if individual_avg and integration_avg else 0

    context = {
        'individual': round(individual_avg, 2),
        'integration': round(integration_avg, 2),
        'overall': round(overall_avg, 2),
        'students': students,
        'active_student': student,
    }
    
    if student:
        context.update({
            'name': student.name,
            'number': student.student_number,
            'course': student.course,
            'ay': student.academic_year,
        })
    else:
        context.update({
            'name': 'No Student Selected',
            'number': 'N/A',
            'course': 'N/A', 
            'ay': 'N/A',
        })
    
    return render(request, 'grade_management.html', context)


# ==================== INTEGRATION VIEW ====================

@login_required(login_url='login')
def integration(request):
    student_id = request.GET.get('student_id') or request.session.get('active_student_id')
    student = None

    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            request.session['active_student_id'] = student.id
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']

    board_areas = BoardExamArea.objects.all()

    board_schedule = [
        {
            'day': 'DAY 1 (Morning)',
            'time': '8:00 AM - 12:00 PM',
            'title': 'History, Theory, Planning & Professional Practice',
            'subjects_count': 4
        },
        {
            'day': 'DAY 1 (Afternoon)',
            'time': '1:00 PM - 5:00 PM',
            'title': 'Technical Systems & Construction',
            'subjects_count': 3
        },
        {
            'day': 'DAY 2 (Whole Day)',
            'time': '8:00 AM - 5:00 PM',
            'title': 'Design Integration & Site Planning',
            'subjects_count': 1
        }
    ]

    integration_courses_qs = IntegrationCourse.objects.all()
    integration_courses_data = []
    total_calculated_grade = 0
    valid_courses_count = 0

    for ic in integration_courses_qs:
        mappings = CourseMapping.objects.filter(integration_course=ic).select_related('course')

        mapped_courses_data = []
        grouped_courses = {}

        for mapping in mappings:
            course = mapping.course
            group_name = mapping.group_name or "General"
            grade_value = 0

            if student:
                grade_obj = Grade.objects.filter(
                    student=student,
                    course=course,
                    course_type='Individual'
                ).order_by('-id').first()
                grade_value = grade_obj.grade if grade_obj else 0

            if grade_value >= 75:
                m_status = 'PASSED'
                m_color = '#27ae60'
            elif grade_value > 0:
                m_status = 'FAILED'
                m_color = '#e74c3c'
            else:
                m_status = 'NOT TAKEN'
                m_color = '#95a5a6'

            course_entry = {
                'code': course.code,
                'title': course.title,
                'grade': grade_value if grade_value > 0 else None,
                'display_grade': f"{grade_value}%" if grade_value > 0 else '--',
                'status': m_status,
                'color': m_color,
                'group_name': group_name,
            }
            mapped_courses_data.append(course_entry)

            if group_name not in grouped_courses:
                grouped_courses[group_name] = []
            grouped_courses[group_name].append(course_entry)

        grades = [c['grade'] for c in mapped_courses_data if c['grade'] and c['grade'] > 0]
        calculated_grade = round(sum(grades) / len(grades), 2) if grades else 0

        if calculated_grade > 0:
            total_calculated_grade += calculated_grade
            valid_courses_count += 1

        if calculated_grade >= 75:
            ic_status = 'PASSED'
            ic_color = '#27ae60'
        elif calculated_grade > 0:
            ic_status = 'FAILED'
            ic_color = '#e74c3c'
        else:
            ic_status = 'NOT TAKEN'
            ic_color = '#95a5a6'

        integration_courses_data.append({
            'code': ic.code,
            'title': ic.title,
            'period': ic.period,
            'calculated_grade': calculated_grade,
            'display_grade': f"{calculated_grade}%" if calculated_grade > 0 else '--',
            'status': ic_status,
            'color': ic_color,
            'progress': calculated_grade,
            'mapped_courses_count': len(mapped_courses_data),
            'graded_courses_count': len([c for c in mapped_courses_data if c['grade']]),
            'grouped_courses': grouped_courses,
        })

    completed_courses = len([ic for ic in integration_courses_data if ic['status'] == 'PASSED'])
    total_courses = len(integration_courses_data)
    average_grade = round(total_calculated_grade / valid_courses_count, 1) if valid_courses_count > 0 else 0
    pass_rate = round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0

    context = {
        'students': Student.objects.all(),
        'active_student': student,
        'student_name': student.name if student else 'Architecture Student',
        'student_number': student.student_number if student else '',
        'student_course': student.course if student else '',
        'student_academic_year': student.academic_year if student else '',
        'board_areas': board_areas,
        'board_schedule': board_schedule,
        'integration_courses': integration_courses_data,
        'completed_courses': completed_courses,
        'total_courses': total_courses,
        'average_grade': average_grade,
        'pass_rate': pass_rate,
        'has_data': valid_courses_count > 0,
    }
    return render(request, 'integration.html', context)


# ==================== BOARD EXAM READINESS ====================

@login_required(login_url='login')
def board_exam_readiness(request):
    student_id = request.GET.get('student_id') or request.session.get('active_student_id')
    student = None

    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            request.session['active_student_id'] = student.id
        except Student.DoesNotExist:
            if 'active_student_id' in request.session:
                del request.session['active_student_id']

    student_grades = []
    individual_grades = []

    if student:
        individual_grades = calculate_individual_course_grades(student)
        for grade_data in individual_grades:
            if grade_data['overall_grade'] > 0:
                student_grades.append({
                    'code': grade_data['course'].code,
                    'grade': grade_data['overall_grade']
                })

    readiness_data = calculate_board_exam_readiness(student_grades)
    progress_summary = get_student_progress_summary(student_grades)
    study_recommendations = generate_study_recommendations(readiness_data)

    total_courses = len(individual_grades)
    completed_courses = len([g for g in individual_grades if g['overall_grade'] >= 75])
    graded = [g['overall_grade'] for g in individual_grades if g['overall_grade'] > 0]
    average_grade = round(sum(graded) / len(graded), 1) if graded else 0
    pass_rate = round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0

    context = {
        'student': student,
        'student_name': student.name if student else 'No Student Selected',
        'student_number': student.student_number if student else 'N/A',
        'student_course': student.course if student else 'N/A',
        'student_academic_year': student.academic_year if student else 'N/A',
        'readiness_data': readiness_data,
        'progress_summary': progress_summary,
        'study_recommendations': study_recommendations,
        'completed_courses': completed_courses,
        'total_courses': total_courses,
        'average_grade': average_grade,
        'pass_rate': pass_rate,
    }

    return render(request, 'board_readiness.html', context)


# ==================== DEBUG INTEGRATION ====================

@login_required(login_url='login')
def debug_integration(request):
    student_id = request.session.get('active_student_id')
    student = Student.objects.get(id=student_id) if student_id else None
    
    integration_courses = IntegrationCourse.objects.all()
    integration_data = []
    
    for course in integration_courses:
        calculated_grade = course.calculate_integration_grade(student)
        mapped_courses = course.mapped_courses.all()
        
        integration_data.append({
            'course': course,
            'calculated_grade': calculated_grade,
            'mapped_courses_count': mapped_courses.count(),
            'mapped_courses_list': list(mapped_courses.values_list('course__code', flat=True))
        })
    
    individual_grades = Grade.objects.filter(course_type='Individual')
    grade_data = []
    for grade in individual_grades:
        grade_data.append({
            'course': grade.course.code if grade.course else 'None',
            'grade': grade.grade,
        })
    
    context = {
        'integration_data': integration_data,
        'individual_grades': grade_data,
        'total_integration_courses': integration_courses.count(),
        'total_individual_grades': individual_grades.count(),
    }
    
    return render(request, 'debug_integration.html', context)


# ==================== SETUP INTEGRATION SYSTEM ====================

@login_required(login_url='login')
def setup_integration_system(request):
    from django.db import transaction
    
    try:
        with transaction.atomic():
            areas = [
                {'name': 'Day 1 Morning', 'schedule': '8:00 AM - 12:00 PM'},
                {'name': 'Day 1 Afternoon', 'schedule': '1:00 PM - 5:00 PM'},
                {'name': 'Day 2', 'schedule': '8:00 AM - 5:00 PM'},
            ]
            
            for area_data in areas:
                BoardExamArea.objects.get_or_create(
                    name=area_data['name'],
                    defaults={'schedule': area_data['schedule']}
                )
            
            integration_courses = [
                {
                    'code': 'AR 390',
                    'title': 'Integration Course 1',
                    'period': 'Prelim',
                    'area_name': 'Day 1 Morning'
                },
                {
                    'code': 'AR 490', 
                    'title': 'Integration Course 2',
                    'period': 'Finals',
                    'area_name': 'Day 2'
                }
            ]
            
            for course_data in integration_courses:
                area = BoardExamArea.objects.get(name=course_data['area_name'])
                IntegrationCourse.objects.get_or_create(
                    code=course_data['code'],
                    defaults={
                        'title': course_data['title'],
                        'period': course_data['period'],
                        'area': area
                    }
                )
            
            messages.success(request, "Integration system setup completed successfully!")
            
    except Exception as e:
        messages.error(request, f"Error setting up integration system: {str(e)}")
    
    return redirect('integration')


# ==================== PROFILE PAGE ====================

@login_required(login_url='login')
def profile_page(request):
    students = Student.objects.all()
    selected_student = None
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    
    if student_id:
        try:
            selected_student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            selected_student = None
            messages.error(request, "Selected student not found!")
    
    if request.method == 'POST' and selected_student:
        selected_student.name = request.POST.get('student_name', selected_student.name)
        selected_student.student_number = request.POST.get('student_number', selected_student.student_number)
        selected_student.course = request.POST.get('course', selected_student.course)
        selected_student.academic_year = request.POST.get('academic_year', selected_student.academic_year)
        
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "Profile picture too large. Please upload an image smaller than 5MB.")
            else:
                selected_student.profile_picture = profile_picture
                messages.success(request, "Profile picture updated successfully!")
        
        try:
            selected_student.save()
            messages.success(request, f"Profile updated for {selected_student.name}!")
        except Exception as e:
            messages.error(request, f"Error saving profile: {str(e)}")
        
        return redirect(f'{request.path}?student_id={selected_student.id}')
    
    individual = 0
    integration = 0
    overall = 0
    
    if selected_student:
        individual_grades = calculate_individual_course_grades(selected_student)
        integration_grades_data = calculate_integration_grades(selected_student)
        
        if individual_grades:
            individual = sum([item['overall_grade'] for item in individual_grades]) / len(individual_grades)
        
        if integration_grades_data:
            integration = sum([item['calculated_grade'] for item in integration_grades_data]) / len(integration_grades_data)
        
        if individual and integration:
            overall = (individual + integration) / 2
    
    context = {
        'students': students,
        'selected_student': selected_student,
        'individual': round(individual, 2),
        'integration': round(integration, 2),
        'overall': round(overall, 2),
    }
    
    return render(request, 'profile.html', context)