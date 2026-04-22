from rest_framework import serializers
from .models import Student, Course, Grade, IntegrationCourse, BoardExamArea

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'

class IntegrationCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationCourse
        fields = '__all__'

class BoardExamAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardExamArea
        fields = '__all__'