# setup_integration.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MYSITE.settings')
django.setup()

from Information_System.models import BoardExamArea, Course, IntegrationCourse, CourseMapping

def setup_board_exam_areas():
    """Create board exam areas"""
    areas = [
        {'name': 'Day 1 Morning', 'schedule': '8:00 AM - 12:00 PM'},
        {'name': 'Day 1 Afternoon', 'schedule': '1:00 PM - 5:00 PM'},
        {'name': 'Day 2', 'schedule': '8:00 AM - 5:00 PM'},
    ]
    
    for area_data in areas:
        area, created = BoardExamArea.objects.get_or_create(
            name=area_data['name'],
            defaults={'schedule': area_data['schedule']}
        )
        print(f"{'Created' if created else 'Found'} area: {area.name}")

def setup_integration_courses():
    """Create integration courses"""
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
        course, created = IntegrationCourse.objects.get_or_create(
            code=course_data['code'],
            defaults={
                'title': course_data['title'],
                'period': course_data['period'],
                'area': area
            }
        )
        print(f"{'Created' if created else 'Found'} integration course: {course.code}")

def map_courses_to_integration():
    """Map individual courses to integration courses"""
    
    # Integration Course 1 mappings (History, Theory, Planning, Professional Practice)
    integration_1_courses = [
        'AR 114', 'AR 211', 'AR 212', 'AR 311',  # History
        'AR 111', 'AR 112', 'AR 113',            # Theory & Interiors
        'AR 203', 'AR 351', 'AR 451', 'AR 452',  # Planning
        'AR 341', 'AR 442',                      # Professional Practice
    ]
    
    # Integration Course 2 mappings (Adds Design and Technical courses)
    integration_2_courses = integration_1_courses + [
        'AR 225', 'AR 224', 'AR 324',            # Building Utilities
        'AR 221', 'AR 222', 'AR 321', 'AR 322',  # Building Technology
        'AR 102', 'AR 302', 'AR 401', 'AR 402',  # Architectural Design
        'AR 551'                                 # Housing
    ]
    
    try:
        integration_1 = IntegrationCourse.objects.get(code='AR 390')
        integration_2 = IntegrationCourse.objects.get(code='AR 490')
        
        # Map courses to Integration Course 1
        for course_code in integration_1_courses:
            try:
                course = Course.objects.get(code=course_code)
                mapping, created = CourseMapping.objects.get_or_create(
                    integration_course=integration_1,
                    course=course
                )
                if created:
                    print(f"Mapped {course.code} to {integration_1.code}")
            except Course.DoesNotExist:
                print(f"Course {course_code} not found - skipping")
        
        # Map courses to Integration Course 2  
        for course_code in integration_2_courses:
            try:
                course = Course.objects.get(code=course_code)
                mapping, created = CourseMapping.objects.get_or_create(
                    integration_course=integration_2,
                    course=course
                )
                if created:
                    print(f"Mapped {course.code} to {integration_2.code}")
            except Course.DoesNotExist:
                print(f"Course {course_code} not found - skipping")
                
    except IntegrationCourse.DoesNotExist:
        print("Integration courses not found - run setup_integration_courses first")

def setup_all_courses():
    """Create all individual courses if they don't exist"""
    courses_data = [
        # History courses
        {'code': 'AR 114', 'title': 'History of Architecture 1', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 211', 'title': 'History of Architecture 2', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 212', 'title': 'History of Architecture 3', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 311', 'title': 'History of Architecture 4', 'area_name': 'Day 1 Morning'},
        
        # Theory courses
        {'code': 'AR 111', 'title': 'Theory of Architecture 1', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 112', 'title': 'Theory of Architecture 2', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 113', 'title': 'Architectural Interiors', 'area_name': 'Day 1 Morning'},
        
        # Planning courses
        {'code': 'AR 203', 'title': 'Tropical Design', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 351', 'title': 'Planning 1', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 451', 'title': 'Planning 2', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 452', 'title': 'Planning 3', 'area_name': 'Day 1 Morning'},
        
        # Professional Practice
        {'code': 'AR 341', 'title': 'Professional Practice 1', 'area_name': 'Day 1 Morning'},
        {'code': 'AR 442', 'title': 'Professional Practice 2', 'area_name': 'Day 1 Morning'},
        
        # Building Utilities (Day 1 Afternoon)
        {'code': 'AR 225', 'title': 'Building Utilities 1', 'area_name': 'Day 1 Afternoon'},
        {'code': 'AR 224', 'title': 'Building Utilities 2', 'area_name': 'Day 1 Afternoon'},
        {'code': 'AR 324', 'title': 'Building Utilities 3', 'area_name': 'Day 1 Afternoon'},
        
        # Building Technology (Day 1 Afternoon)
        {'code': 'AR 221', 'title': 'Building Technology 1', 'area_name': 'Day 1 Afternoon'},
        {'code': 'AR 222', 'title': 'Building Technology 2', 'area_name': 'Day 1 Afternoon'},
        {'code': 'AR 321', 'title': 'Building Technology 3', 'area_name': 'Day 1 Afternoon'},
        {'code': 'AR 322', 'title': 'Building Technology 4', 'area_name': 'Day 1 Afternoon'},
        
        # Architectural Design (Day 2)
        {'code': 'AR 102', 'title': 'Architectural Design 2', 'area_name': 'Day 2'},
        {'code': 'AR 302', 'title': 'Architectural Design 6', 'area_name': 'Day 2'},
        {'code': 'AR 401', 'title': 'Architectural Design 7', 'area_name': 'Day 2'},
        {'code': 'AR 402', 'title': 'Architectural Design 8', 'area_name': 'Day 2'},
        {'code': 'AR 551', 'title': 'Housing', 'area_name': 'Day 2'},
    ]
    
    for course_data in courses_data:
        area = BoardExamArea.objects.get(name=course_data['area_name'])
        course, created = Course.objects.get_or_create(
            code=course_data['code'],
            defaults={
                'title': course_data['title'],
                'area': area
            }
        )
        print(f"{'Created' if created else 'Found'} course: {course.code}")

if __name__ == '__main__':
    print("Setting up board exam system...")
    setup_board_exam_areas()
    setup_all_courses()
    setup_integration_courses()
    map_courses_to_integration()
    print("Setup complete!")