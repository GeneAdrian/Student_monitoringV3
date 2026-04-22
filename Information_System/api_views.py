from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
from .models import Student, Course, Grade, IntegrationCourse, BoardExamArea
from .admin_models import Admin
from .serializers import StudentSerializer, CourseSerializer, GradeSerializer, IntegrationCourseSerializer, BoardExamAreaSerializer

# LAHAT NG VIEWSET AY NAKA-ALLOWANY - WALANG TOKEN NEEDED
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.AllowAny]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.AllowAny]

class IntegrationCourseViewSet(viewsets.ModelViewSet):
    queryset = IntegrationCourse.objects.all()
    serializer_class = IntegrationCourseSerializer
    permission_classes = [permissions.AllowAny]

class BoardExamAreaViewSet(viewsets.ModelViewSet):
    queryset = BoardExamArea.objects.all()
    serializer_class = BoardExamAreaSerializer
    permission_classes = [permissions.AllowAny]

class CustomAuthToken(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            admin = Admin.objects.get(username=username)
            if check_password(password, admin.password_hash):
                return Response({
                    'token': f"{admin.id}_{admin.username}",
                    'user_id': admin.id,
                    'username': admin.username
                })
        except Admin.DoesNotExist:
            pass
        
        return Response({'error': 'Invalid credentials'}, status=400)