from django.db import models
from django.db.models import Avg
from django.utils import timezone
from .utils import calculate_integration_grade, calculate_integration_percentage, get_integration_remarks

# ==================== BOARD EXAM MODELS ====================

class BoardExamArea(models.Model):
    name = models.CharField(max_length=100)
    schedule = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'board_exam_areas'


class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    area = models.ForeignKey(BoardExamArea, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def get_day_grade(self, day, student=None):
        """Calculate average grade for specific day - optionally for specific student"""
        day_grades = self.grades.filter(day=day)
        if student:
            day_grades = day_grades.filter(student=student)
        
        if day_grades.exists():
            return day_grades.aggregate(Avg('grade'))['grade__avg']
        return 0
    
    def get_overall_grade(self, student=None):
        """Calculate overall grade across all days - optionally for specific student"""
        all_grades = self.grades.all()
        if student:
            all_grades = all_grades.filter(student=student)
        
        if all_grades.exists():
            return all_grades.aggregate(Avg('grade'))['grade__avg']
        return 0
    
    def get_grade_percentage(self, student=None):
        """Get grade as percentage with status - optionally for specific student"""
        overall_grade = self.get_overall_grade(student)
        if overall_grade == 0:
            return {
                'percentage': 0,
                'status': 'Not Taken',
                'color': '#95a5a6',
                'passed': False
            }
        
        passed = overall_grade >= 75
        status = 'PASSED' if passed else 'FAILED'
        color = '#27ae60' if passed else '#e74c3c'
        
        return {
            'percentage': round(overall_grade, 1),
            'status': status,
            'color': color,
            'passed': passed
        }
    
    def get_grade_remarks(self, student=None):
        """Get textual remarks for the grade - optionally for specific student"""
        overall_grade = self.get_overall_grade(student)
        if overall_grade >= 90:
            return 'Excellent'
        elif overall_grade >= 80:
            return 'Very Good'
        elif overall_grade >= 75:
            return 'Good'
        elif overall_grade >= 70:
            return 'Satisfactory'
        elif overall_grade > 0:
            return 'Needs Improvement'
        else:
            return 'Not Taken'
    
    class Meta:
        db_table = 'courses'


class IntegrationCourse(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    PERIOD_CHOICES = [
        ('Prelim', 'Prelim'),
        ('Midterm', 'Midterm'),
        ('Finals', 'Finals'),
    ]
    period = models.CharField(max_length=50, choices=PERIOD_CHOICES)
    area = models.ForeignKey(BoardExamArea, on_delete=models.CASCADE, related_name='integration_courses')

    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def calculate_integration_grade(self, student=None):
        """Calculate integration grade from mapped courses - USING UTILS"""
        return calculate_integration_grade(self, student)
    
    def get_integration_percentage(self, student=None):
        """Get integration grade as percentage - USING UTILS"""
        return calculate_integration_percentage(self, student)
    
    def get_integration_remarks(self, student=None):
        """Get textual remarks for integration grade"""
        integration_grade = self.calculate_integration_grade(student)
        return get_integration_remarks(integration_grade)
    
    def get_mapped_courses_count(self):
        """Get count of mapped individual courses"""
        return self.mapped_courses.count()
    
    def get_graded_courses_count(self, student=None):
        """Get count of mapped courses that have actual grades"""
        count = 0
        for mapping in self.mapped_courses.all():
            if mapping.course.get_overall_grade(student) > 0:
                count += 1
        return count
    
    def get_mapped_courses_with_grades(self, student=None):
        """Get all mapped courses with their grades for display"""
        mapped_courses_data = []
        for mapping in self.mapped_courses.all():
            course = mapping.course
            overall_grade = course.get_overall_grade(student)
            grade_data = course.get_grade_percentage(student)
            
            mapped_courses_data.append({
                'code': course.code,
                'title': course.title,
                'grade': overall_grade,
                'percentage': grade_data['percentage'],
                'status': grade_data['status'],
                'color': grade_data['color'],
                'remarks': course.get_grade_remarks(student)
            })
        return mapped_courses_data
    
    class Meta:
        db_table = 'integration_courses'


class CourseMapping(models.Model):
    integration_course = models.ForeignKey(IntegrationCourse, on_delete=models.CASCADE, related_name='mapped_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='integrations')
    group_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.integration_course.title} ↔ {self.course.title}"
    
    class Meta:
        unique_together = ['integration_course', 'course']
        db_table = 'course_mappings'


class Student(models.Model):
    name = models.CharField(max_length=200)
    student_number = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.student_number})"
    
    def get_day_performance(self, day):
        """Get student's performance for a specific day"""
        day_grades = Grade.objects.filter(
            course_type='Individual',
            course__isnull=False,
            day=day,
            student=self
        )
        
        if day_grades.exists():
            avg_grade = day_grades.aggregate(Avg('grade'))['grade__avg']
            passed_count = day_grades.filter(grade__gte=75).count()
            total_count = day_grades.count()
            
            return {
                'average_grade': round(avg_grade, 1),
                'average_percentage': f"{round(avg_grade, 1)}%",
                'passed_count': passed_count,
                'total_count': total_count,
                'pass_rate': round((passed_count / total_count) * 100, 1) if total_count > 0 else 0,
                'pass_rate_percentage': f"{round((passed_count / total_count) * 100, 1)}%" if total_count > 0 else "0%"
            }
        return None
    
    def get_overall_performance(self):
        """Get overall performance across all days"""
        all_grades = Grade.objects.filter(
            course_type='Individual',
            course__isnull=False,
            student=self
        )
        
        if all_grades.exists():
            avg_grade = all_grades.aggregate(Avg('grade'))['grade__avg']
            passed_count = all_grades.filter(grade__gte=75).count()
            total_count = all_grades.count()
            
            return {
                'average_grade': round(avg_grade, 1),
                'average_percentage': f"{round(avg_grade, 1)}%",
                'passed_count': passed_count,
                'total_count': total_count,
                'pass_rate': round((passed_count / total_count) * 100, 1) if total_count > 0 else 0,
                'pass_rate_percentage': f"{round((passed_count / total_count) * 100, 1)}%" if total_count > 0 else "0%",
                'completed_courses': passed_count,
                'total_courses': total_count
            }
        return None
    
    def get_courses_with_percentages(self):
        """Get all courses with their percentage grades"""
        courses_data = []
        individual_grades = Grade.objects.filter(
            course_type='Individual',
            course__isnull=False,
            student=self
        ).select_related('course')
        
        for grade in individual_grades:
            course_data = {
                'code': grade.course.code,
                'title': grade.course.title,
                'grade': grade.grade,
                'percentage': f"{grade.grade}%",
                'day': grade.day,
                'status': grade.status,
                'remark': grade.remark,
                'color': '#27ae60' if grade.grade >= 75 else '#e74c3c',
                'remarks': grade.course.get_grade_remarks(self)
            }
            courses_data.append(course_data)
        
        return courses_data
    
    def get_integration_courses_with_grades(self):
        """Get all integration courses with calculated grades"""
        integration_courses = IntegrationCourse.objects.all()
        integration_data = []
        
        for integration_course in integration_courses:
            integration_grade = integration_course.calculate_integration_grade(self)
            percentage_data = integration_course.get_integration_percentage(self)
            
            integration_data.append({
                'code': integration_course.code,
                'title': integration_course.title,
                'calculated_grade': integration_grade,
                'percentage': percentage_data['percentage'],
                'status': percentage_data['status'],
                'color': percentage_data['color'],
                'remarks': integration_course.get_integration_remarks(self),
                'mapped_courses_count': integration_course.get_mapped_courses_count(),
                'graded_courses_count': integration_course.get_graded_courses_count(self),
                'mapped_courses': integration_course.get_mapped_courses_with_grades(self),
                'period': integration_course.period,
                'area': integration_course.area.name
            })
        
        return integration_data
    
    def get_board_exam_readiness(self):
        """Calculate board exam readiness by area"""
        integration_courses = self.get_integration_courses_with_grades()
        area_performance = {}
        
        for course in integration_courses:
            area = course['area']
            if area not in area_performance:
                area_performance[area] = {
                    'total_grade': 0,
                    'course_count': 0,
                    'courses': []
                }
            
            area_performance[area]['total_grade'] += course['calculated_grade']
            area_performance[area]['course_count'] += 1
            area_performance[area]['courses'].append(course)
        
        # Calculate averages for each area
        readiness_data = {}
        for area, data in area_performance.items():
            if data['course_count'] > 0:
                average_grade = data['total_grade'] / data['course_count']
                readiness_data[area] = {
                    'average_grade': round(average_grade, 1),
                    'percentage': f"{round(average_grade, 1)}%",
                    'status': 'PASSED' if average_grade >= 75 else 'FAILED',
                    'color': '#27ae60' if average_grade >= 75 else '#e74c3c',
                    'course_count': data['course_count'],
                    'courses': data['courses']
                }
        
        return readiness_data
    
    class Meta:
        db_table = 'students'
        ordering = ['name']


class Grade(models.Model):
    COURSE_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Integration', 'Integration')
    ]
    
    DAY_CHOICES = [
        (1, 'Day 1'),
        (2, 'Day 2'), 
        (3, 'Day 3')
    ]
    
    course_type = models.CharField(max_length=50, choices=COURSE_TYPE_CHOICES)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    integration_course = models.ForeignKey(IntegrationCourse, on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    grade = models.FloatField()
    day = models.IntegerField(choices=DAY_CHOICES, default=1)
    remark = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    general_average = models.FloatField(default=0)
    overall_result = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        course_display = self.course.title if self.course else (self.integration_course.title if self.integration_course else "Unknown")
        student_display = f" - {self.student.name}" if self.student else ""
        return f"{course_display}{student_display} - Day {self.day} - {self.grade} ({self.status})"
    
    def get_grade_percentage(self):
        """Get grade as percentage with formatting"""
        return {
            'percentage': self.grade,
            'formatted': f"{self.grade}%",
            'status': self.status,
            'color': '#27ae60' if self.grade >= 75 else '#e74c3c'
        }
    
    def save(self, *args, **kwargs):
        # Auto-calculate remark and status based on grade
        if self.grade >= 75:
            self.remark = "PASSED"
            self.status = "COMPLETED"
        else:
            self.remark = "FAILED" 
            self.status = "INCOMPLETE"
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'grades'
        ordering = ['-created_at']