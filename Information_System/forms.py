# Information_System/forms.py
from django import forms
from django.contrib.auth import password_validation
from django.utils import timezone
from .models import Student
from .admin_models import Admin, AdminAuthorization

# ==================== ADMIN AUTHENTICATION FORMS ====================

class AdminLoginForm(forms.Form):
    """Admin login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter username or email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox-input'
        })
    )


class AdminSignupForm(forms.Form):
    """Admin signup form with authorization code"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Choose username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter email'
        })
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter first name (optional)'
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter last name (optional)'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm password'
        })
    )
    auth_code = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter admin authorization code'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Admin.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Admin.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def clean_auth_code(self):
        code = self.cleaned_data.get('auth_code')
        
        # Check if code exists in AdminAuthorization
        try:
            auth = AdminAuthorization.objects.get(code=code)
            if auth.is_used:
                raise forms.ValidationError('This authorization code has already been used.')
            if auth.expires_at < timezone.now():
                raise forms.ValidationError('This authorization code has expired.')
            self.cleaned_data['auth_obj'] = auth
        except AdminAuthorization.DoesNotExist:
            # Check if it's the master admin code from settings
            from django.conf import settings
            if code != getattr(settings, 'ADMIN_SIGNUP_CODE', 'ADMIN123'):
                raise forms.ValidationError('Invalid authorization code.')
        
        return code


class AdminProfileForm(forms.ModelForm):
    """Form for editing admin profile"""
    class Meta:
        model = Admin
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter email'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter phone number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            })
        }


class AdminChangePasswordForm(forms.Form):
    """Form for changing admin password"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter current password'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_new_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data


class CreateAdminCodeForm(forms.ModelForm):
    """Form for creating admin authorization codes"""
    class Meta:
        model = AdminAuthorization
        fields = ['code', 'description', 'expires_at']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter authorization code'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter description (e.g., "For Faculty 2025")'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            })
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if AdminAuthorization.objects.filter(code=code).exists():
            raise forms.ValidationError('This code already exists.')
        return code
    
    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at < timezone.now():
            raise forms.ValidationError('Expiration date must be in the future.')
        return expires_at


# ==================== STUDENT FORMS (KEEP ALL OF THESE) ====================

class StudentForm(forms.ModelForm):
    """Form for adding/editing students"""
    class Meta:
        model = Student
        fields = ['name', 'student_number', 'course', 'academic_year', 'profile_picture']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter full name'
            }),
            'student_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter student number'
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter course'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter academic year (e.g., 2024-2025)'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            })
        }
    
    def clean_student_number(self):
        student_number = self.cleaned_data.get('student_number')
        # Check if student number already exists (excluding current instance if editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if Student.objects.filter(student_number=student_number).exclude(pk=instance.pk).exists():
                raise forms.ValidationError('This student number already exists.')
        else:
            if Student.objects.filter(student_number=student_number).exists():
                raise forms.ValidationError('This student number already exists.')
        return student_number


class StudentProfileForm(forms.ModelForm):
    """Form for editing student profile (kept for backward compatibility)"""
    class Meta:
        model = Student
        fields = ['name', 'course', 'academic_year', 'profile_picture']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter full name'
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter course'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter academic year'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            })
        }


class StudentSearchForm(forms.Form):
    """Form for searching/filtering students"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search by name or student number...'
        })
    )
    
    course = forms.ChoiceField(
        required=False,
        choices=[('', 'All Courses')],
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    academic_year = forms.ChoiceField(
        required=False,
        choices=[('', 'All Years')],
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            if Student.objects.exists():
                # Get unique courses
                courses = Student.objects.values_list('course', flat=True).distinct()
                course_choices = [('', 'All Courses')] + [(c, c) for c in courses if c]
                self.fields['course'].choices = course_choices
                
                # Get unique academic years
                years = Student.objects.values_list('academic_year', flat=True).distinct()
                year_choices = [('', 'All Years')] + [(y, y) for y in years if y]
                self.fields['academic_year'].choices = year_choices
        except Exception:
            pass


# ==================== GRADE FORMS (OPTIONAL - ADD IF NEEDED) ====================

class GradeEntryForm(forms.Form):
    """Form for entering a single grade"""
    course = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    grade = forms.FloatField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter grade (0-100)',
            'step': '0.01'
        })
    )
    
    def __init__(self, *args, **kwargs):
        course_queryset = kwargs.pop('course_queryset', None)
        super().__init__(*args, **kwargs)
        if course_queryset is not None:
            self.fields['course'].queryset = course_queryset


class BulkGradeEntryForm(forms.Form):
    """Form for entering multiple grades at once"""
    grades_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Enter grades in format: COURSE_CODE:GRADE (one per line)',
            'rows': 10
        })
    )