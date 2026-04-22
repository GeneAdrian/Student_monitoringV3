# Information_System/utils.py
# 🧠 Utility functions for computing averages and evaluating board exam results

def evaluate_grade(grade):
    """
    Determines the remark and pass/fail status for a given grade.
    Passing grade threshold: 75
    """
    if grade >= 90:
        return "Excellent", "Pass"
    elif grade >= 75:
        return "Satisfactory", "Pass"
    elif grade >= 50:
        return "Needs Improvement", "Conditional"
    else:
        return "Failed", "Fail"


def compute_averages(records):
    """
    Calculates the average for both Individual and Integration courses
    and determines the overall average and result.
    """
    individual_grades = [r['grade'] for r in records if r['type'] == 'Individual']
    integration_grades = [r['grade'] for r in records if r['type'] == 'Integration']

    avg_individual = sum(individual_grades) / len(individual_grades) if individual_grades else 0
    avg_integration = sum(integration_grades) / len(integration_grades) if integration_grades else 0

    overall_avg = (avg_individual + avg_integration) / 2
    overall_status = "PASS" if overall_avg >= 75 else "FAIL"

    return avg_individual, avg_integration, overall_avg, overall_status


def calculate_board_exam_percentage(obtained_marks, total_marks):
    """
    Calculates final board exam percentage
    """
    if total_marks == 0:
        return 0, "Invalid"
    
    percentage = (obtained_marks / total_marks) * 100
    result = "PASS" if percentage >= 75 else "FAIL"
    return round(percentage, 2), result


# 🎯 INTEGRATION GRADE CALCULATIONS
def calculate_integration_grade(integration_course, student=None):
    """
    Calculate integration grade based on mapped individual course grades
    Uses the CourseMapping relationships to get individual course grades
    """
    try:
        if not hasattr(integration_course, 'mapped_courses'):
            return 0
        
        mapped_courses = integration_course.mapped_courses.all()
        if not mapped_courses.exists():
            return 0
        
        total_grade = 0
        count = 0
        
        for mapping in mapped_courses:
            # Get the overall grade from the individual course - with optional student filter
            course_grade = mapping.course.get_overall_grade(student)
            if course_grade and course_grade > 0:  # Only count courses with actual grades
                total_grade += course_grade
                count += 1
        
        return round(total_grade / count, 2) if count > 0 else 0
    except Exception as e:
        print(f"Error calculating integration grade: {e}")
        return 0


def get_integration_course_mappings():
    """
    Define the mapping between Integration Courses and Individual Courses
    Based on the 2018 BS ARCH Curriculum board exam mapping table
    """
    return {
        "AR 390": {  # Integration Course 1 - Prelim
            "title": "Integration Course 1",
            "period": "Prelim",
            "mapped_courses": [
                "AR 114", "AR 211", "AR 212", "AR 311",  # History of Architecture
                "AR 111", "AR 112", "AR 113",            # Theory of Architecture & Interiors
                "AR 203", "AR 351", "AR 451",            # Principles of Planning
                "AR 341",                                # Professional Practice
                "AR 225", "AR 224", "AR 324",            # Building Utilities
                "AR 221"                                 # Building Materials & Construction
            ]
        },
        "AR 490": {  # Integration Course 2 - Finals
            "title": "Integration Course 2", 
            "period": "Finals",
            "mapped_courses": [
                "AR 114", "AR 211", "AR 212", "AR 311",  # History of Architecture
                "AR 111", "AR 112", "AR 113",            # Theory of Architecture & Interiors  
                "AR 203", "AR 351", "AR 451",            # Principles of Planning
                "AR 341",                                # Professional Practice
                "AR 225", "AR 224", "AR 324",            # Building Utilities
                "AR 221",                                # Building Materials & Construction
                "AR 102", "AR 302", "AR 401", "AR 402",  # Architectural Design Courses
                "AR 551"                                 # Housing
            ]
        }
    }


def calculate_integration_percentage(integration_course, student=None):
    """
    Get integration grade as percentage with status and color coding
    """
    integration_grade = calculate_integration_grade(integration_course, student)
    
    if integration_grade == 0:
        return {
            'percentage': 0,
            'status': 'NOT TAKEN',
            'color': '#95a5a6',  # Gray
            'passed': False
        }
    
    passed = integration_grade >= 75
    status = 'PASSED' if passed else 'FAILED'
    color = '#27ae60' if passed else '#e74c3c'  # Green : Red
    
    return {
        'percentage': integration_grade,
        'status': status,
        'color': color,
        'passed': passed
    }


def get_integration_remarks(integration_grade):
    """
    Get textual remarks for integration course grade
    """
    if integration_grade >= 90:
        return 'Excellent'
    elif integration_grade >= 80:
        return 'Very Good'
    elif integration_grade >= 75:
        return 'Good'
    elif integration_grade >= 70:
        return 'Satisfactory'
    elif integration_grade > 0:
        return 'Needs Improvement'
    else:
        return 'No Grade'


# 🏛️ ARCHITECTURE CURRICULUM ANALYZER
def analyze_architecture_curriculum():
    """
    Analyzes and calculates individual courses based on board exam topics
    and integration courses from the 2018 BS ARCH Curriculum
    """
    curriculum = {
        "DAY 1 (Morning) - History, Theory, Planning & Professional Practice": {
            "History of Architecture": [
                "AR 114 - History of Architecture 1",
                "AR 211 - History of Architecture 2", 
                "AR 212 - History of Architecture 3",
                "AR 311 - History of Architecture 4"
            ],
            "Theory of Architecture and Architectural Interiors": [
                "AR 111 - Theory of Architecture 1",
                "AR 112 - Theory of Architecture 2",
                "AR 113 - Architectural Interiors"
            ],
            "Principles of Planning and Urban Design": [
                "AR 203 - Tropical Design",
                "AR 351 - Planning 1",
                "AR 451 - Planning 2", 
                "AR 452 - Planning 3"
            ],
            "Professional Practice and the Building Laws": [
                "AR 341 - Professional Practice 1",
                "AR 442 - Professional Practice 2"
            ]
        },
        "DAY 1 (Afternoon) - Technical Systems & Construction": {
            "Building Utilities": [
                "AR 225 - Building Utilities 1",
                "AR 224 - Building Utilities 2",
                "AR 324 - Building Utilities 3"
            ],
            "Structural Conceptualization": [
                "Structural Conceptualization (Integrated Topic)"
            ],
            "Building Materials and Construction": [
                "AR 221 - Building Technology 1",
                "AR 222 - Building Technology 2", 
                "AR 321 - Building Technology 3",
                "AR 322 - Building Technology 4"
            ]
        },
        "DAY 2 (Whole Day) - Design Integration & Site Planning": {
            "Architectural Design and Site Planning": [
                "AR 102 - Architectural Design 2",
                "AR 302 - Architectural Design 6", 
                "AR 401 - Architectural Design 7",
                "AR 402 - Architectural Design 8",
                "AR 551 - Housing",
                "AR 112 - Theory of Architecture 2",
                "AR 113 - Architectural Interiors", 
                "AR 203 - Tropical Design",
                "AR 341 - Professional Practice 1",
                "AR 351 - Planning 1",
                "AR 222 - Building Technology 2",
                "AR 322 - Building Technology 4"
            ]
        }
    }
    
    return curriculum


def calculate_course_statistics():
    """
    Calculates statistics for all courses in the architecture curriculum
    """
    curriculum = analyze_architecture_curriculum()
    
    total_courses = 0
    area_stats = {}
    
    print("📊 ARCHITECTURE BOARD EXAM COURSE STATISTICS")
    print("=" * 60)
    
    for area, topics in curriculum.items():
        area_total = 0
        print(f"\n{area}:")
        print("-" * 50)
        
        for topic, courses in topics.items():
            count = len(courses)
            area_total += count
            total_courses += count
            print(f"  {topic}: {count} courses")
            
            # List individual courses
            for course in courses:
                print(f"    • {course}")
        
        area_stats[area] = area_total
        print(f"  🎯 AREA TOTAL: {area_total} courses")
    
    print(f"\n📈 OVERALL SUMMARY:")
    print(f"   Total Individual Courses: {total_courses}")
    print(f"   Day 1 Morning: {area_stats.get('DAY 1 (Morning) - History, Theory, Planning & Professional Practice', 0)} courses")
    print(f"   Day 1 Afternoon: {area_stats.get('DAY 1 (Afternoon) - Technical Systems & Construction', 0)} courses") 
    print(f"   Day 2 Whole Day: {area_stats.get('DAY 2 (Whole Day) - Design Integration & Site Planning', 0)} courses")
    
    return total_courses, area_stats


def get_courses_by_topic(topic_name):
    """
    Get all courses for a specific board exam topic
    """
    curriculum = analyze_architecture_curriculum()
    
    for area, topics in curriculum.items():
        for topic, courses in topics.items():
            if topic_name.lower() in topic.lower():
                return courses, area
    
    return [], "Topic not found"


def calculate_board_exam_readiness(student_grades):
    """
    Calculate board exam readiness based on individual course grades
    Returns comprehensive readiness analysis by topic area
    """
    curriculum = analyze_architecture_curriculum()
    readiness_data = {}
    
    # Convert student grades to a dictionary for easy lookup
    grade_dict = {grade['code']: grade for grade in student_grades}
    
    for area, topics in curriculum.items():
        readiness_data[area] = {}
        
        for topic, courses in topics.items():
            topic_grades = []
            valid_courses = []
            
            for course_str in courses:
                # Extract course code (e.g., "AR 114" from "AR 114 - History of Architecture 1")
                course_code = course_str.split(' - ')[0]
                
                if course_code in grade_dict:
                    grade_value = grade_dict[course_code]['grade']
                    topic_grades.append(grade_value)
                    valid_courses.append({
                        'code': course_code,
                        'title': course_str,
                        'grade': grade_value,
                        'status': 'PASSED' if grade_value >= 75 else 'FAILED'
                    })
                elif "Structural Conceptualization" not in course_str:  # Skip integrated topics
                    valid_courses.append({
                        'code': course_code,
                        'title': course_str,
                        'grade': 0,
                        'status': 'NOT TAKEN'
                    })
            
            # Calculate topic average
            if topic_grades:
                topic_average = sum(topic_grades) / len(topic_grades)
                passed_count = sum(1 for grade in topic_grades if grade >= 75)
                total_count = len(topic_grades)
                
                readiness_data[area][topic] = {
                    'average_grade': round(topic_average, 1),
                    'percentage': f"{round(topic_average, 1)}%",
                    'passed_count': passed_count,
                    'total_count': total_count,
                    'pass_rate': round((passed_count / total_count) * 100, 1) if total_count > 0 else 0,
                    'status': 'READY' if topic_average >= 75 else 'NEEDS REVIEW',
                    'color': '#27ae60' if topic_average >= 75 else '#e74c3c',
                    'courses': valid_courses
                }
            else:
                readiness_data[area][topic] = {
                    'average_grade': 0,
                    'percentage': "0%",
                    'passed_count': 0,
                    'total_count': len(valid_courses),
                    'pass_rate': 0,
                    'status': 'NO DATA',
                    'color': '#95a5a6',
                    'courses': valid_courses
                }
    
    return readiness_data


def get_student_progress_summary(student_grades):
    """
    Get overall progress summary for a student
    """
    total_courses = 0
    completed_courses = 0
    total_grade = 0
    
    for grade in student_grades:
        total_courses += 1
        if grade['grade'] >= 75:
            completed_courses += 1
        total_grade += grade['grade']
    
    average_grade = total_grade / total_courses if total_courses > 0 else 0
    completion_rate = (completed_courses / total_courses) * 100 if total_courses > 0 else 0
    
    return {
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'average_grade': round(average_grade, 1),
        'completion_rate': round(completion_rate, 1),
        'overall_status': 'ON TRACK' if completion_rate >= 75 else 'NEEDS IMPROVEMENT'
    }


def generate_study_recommendations(readiness_data):
    """
    Generate personalized study recommendations based on readiness analysis
    """
    recommendations = []
    priority_areas = []
    
    for area, topics in readiness_data.items():
        for topic, data in topics.items():
            if data['average_grade'] < 75 and data['total_count'] > 0:
                priority_areas.append({
                    'topic': topic,
                    'area': area,
                    'current_grade': data['average_grade'],
                    'passed_courses': data['passed_count'],
                    'total_courses': data['total_count']
                })
    
    # Sort by lowest grade first
    priority_areas.sort(key=lambda x: x['current_grade'])
    
    for priority in priority_areas[:3]:  # Top 3 priority areas
        recommendations.append({
            'priority': f"High Priority - {priority['topic']}",
            'message': f"Focus on {priority['topic']} (Current: {priority['current_grade']}%, {priority['passed_courses']}/{priority['total_courses']} courses passed)",
            'area': priority['area']
        })
    
    # Add general recommendation if no priorities
    if not recommendations:
        recommendations.append({
            'priority': "Maintain Performance",
            'message': "You're doing well! Keep reviewing all topics to maintain your performance.",
            'area': "All Areas"
        })
    
    return recommendations