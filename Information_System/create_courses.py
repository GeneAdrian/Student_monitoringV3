from django.core.management.base import BaseCommand
from Information_System.models import BoardExamArea, Course, IntegrationCourse, CourseMapping

class Command(BaseCommand):
    help = 'Create all courses and integration courses with group names'

    def handle(self, *args, **kwargs):
        
        # ========== BOARD EXAM AREAS ==========
        area1, _ = BoardExamArea.objects.get_or_create(name="AREA 1 - History and Theory of Architecture")
        area2, _ = BoardExamArea.objects.get_or_create(name="AREA 2 - Building Utilities and Technology")
        area3, _ = BoardExamArea.objects.get_or_create(name="AREA 3 - Architectural Design and Site Planning")

        # ========== INDIVIDUAL COURSES ==========
        individual_courses = [
            # AREA 1
            ("AR 114", "History of Architecture 1", area1),
            ("AR 211", "History of Architecture 2", area1),
            ("AR 212", "History of Architecture 3", area1),
            ("AR 311", "History of Architecture 4", area1),
            ("AR 111", "Theory of Architecture 1", area1),
            ("AR 112", "Theory of Architecture 2", area1),
            ("AR 113", "Architectural Interiors", area1),
            ("AR 203", "Tropical Design", area1),
            ("AR 351", "Planning 1", area1),
            ("AR 451", "Planning 2", area1),
            ("AR 341", "Professional Practice 1", area1),
            ("AR 441", "Professional Practice 2", area1),
            ("AR 443", "Professional Practice 3", area1),
            ("AR 551", "Housing", area1),
            
            # AREA 2
            ("AR 225", "Building Utilities 1", area2),
            ("AR 226", "Building Utilities 2", area2),
            ("AR 324", "Building Utilities 3", area2),
            ("AR 221", "Building Technology 1", area2),
            ("AR 222", "Building Technology 2", area2),
            ("AR 321", "Building Technology 3", area2),
            ("AR 322", "Building Technology 4", area2),
            ("AR 421", "Building Technology 5", area2),
            
            # AREA 3
            ("AR 102", "Architectural Design 2", area3),
            ("AR 302", "Architectural Design 6", area3),
            ("AR 401", "Architectural Design 7", area3),
        ]

        course_objects = {}
        for code, title, area in individual_courses:
            course, _ = Course.objects.get_or_create(code=code, defaults={'title': title, 'area': area})
            course_objects[code] = course
            self.stdout.write(f'Created: {code} - {title}')

        # ========== INTEGRATION COURSES ==========
        integration_courses = [
            ("AR 390", "Integration Course 1", area1),
            ("AR 490", "Integration Course 2", area2),
        ]

        integration_objects = {}
        for code, title, area in integration_courses:
            integration, _ = IntegrationCourse.objects.get_or_create(code=code, defaults={'title': title, 'area': area})
            integration_objects[code] = integration
            self.stdout.write(f'Created Integration: {code} - {title}')

        # ========== IC 1 MAPPINGS WITH GROUP NAMES ==========
        ic1_mappings = [
            # History of Architecture group
            ("History of Architecture", ["AR 114", "AR 211", "AR 212", "AR 311"]),
            # Theory of Architecture and Architectural Interiors group
            ("Theory of Architecture and Architectural Interiors", ["AR 111", "AR 112", "AR 113"]),
            # Principles of Planning and Urban Design group
            ("Principles of Planning and Urban Design", ["AR 203"]),
            # Professional Practice and the Building Laws group
            ("Professional Practice and the Building Laws", ["AR 341"]),
            # Building Utilities group
            ("Building Utilities", ["AR 225", "AR 226"]),
            # Structural Conceptualization group
            ("Structural Conceptualization", ["AR 221"]),
            # Building Materials and Construction group
            ("Building Materials and Construction", ["AR 222"]),
            # Architectural Design and Site Planning group
            ("Architectural Design and Site Planning", ["AR 341", "AR 222", "AR 112", "AR 113", "AR 203", "AR 102"]),
        ]

        for group_name, codes in ic1_mappings:
            for code in codes:
                if code in course_objects:
                    CourseMapping.objects.get_or_create(
                        integration_course=integration_objects["AR 390"],
                        course=course_objects[code],
                        defaults={'group_name': group_name}
                    )
                    self.stdout.write(f'Mapped: {code} -> AR 390 [{group_name}]')

        # ========== IC 2 MAPPINGS WITH GROUP NAMES ==========
        ic2_mappings = [
            # History of Architecture group
            ("History of Architecture", ["AR 114", "AR 211", "AR 212", "AR 311"]),
            # Theory of Architecture and Architectural Interiors group
            ("Theory of Architecture and Architectural Interiors", ["AR 111", "AR 112", "AR 113"]),
            # Principles of Planning and Urban Design group
            ("Principles of Planning and Urban Design", ["AR 203", "AR 351", "AR 451"]),
            # Professional Practice and the Building Laws group
            ("Professional Practice and the Building Laws", ["AR 341", "AR 441"]),
            # Building Utilities group
            ("Building Utilities", ["AR 225", "AR 226", "AR 324"]),
            # Building Materials and Construction group
            ("Building Materials and Construction", ["AR 221", "AR 222", "AR 321", "AR 322", "AR 421"]),
            # Architectural Design and Site Planning group
            ("Architectural Design and Site Planning", ["AR 341", "AR 351", "AR 222", "AR 322", "AR 112", "AR 113", "AR 203", "AR 102", "AR 302", "AR 401"]),
        ]

        for group_name, codes in ic2_mappings:
            for code in codes:
                if code in course_objects:
                    CourseMapping.objects.get_or_create(
                        integration_course=integration_objects["AR 490"],
                        course=course_objects[code],
                        defaults={'group_name': group_name}
                    )
                    self.stdout.write(f'Mapped: {code} -> AR 490 [{group_name}]')

        self.stdout.write(self.style.SUCCESS('\nAll courses and mappings created successfully!'))