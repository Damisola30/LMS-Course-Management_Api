# from django.contrib.auth.models import Group, User
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Teacher, Student, Course, CourseMaterial, Assignment, Submission, Lesson, Progress

User = get_user_model()

class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "first_name", "last_name"]



class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "username", "role"]


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Course
        fields = '__all__'

class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'


class SubmissionTeacherSerializer(serializers.ModelSerializer):
    """
    For teachers/admins: full view + teacher can set grade.
    """
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())

    class Meta:
        model = Submission
        # allow grade writable for teachers
        fields = ["id", "assignment", "student", "file", "submitted_at", "grade", "created_at", "updated_at"]
        read_only_fields = ["id", "submitted_at", "created_at", "updated_at"]


class SubmissionStudentSerializer(serializers.ModelSerializer):
    """
    For students: they can create a submission and update only the 'file' (and maybe replace it).
    grade is read-only here.
    """
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())

    class Meta:
        model = Submission
        fields = ["id", "assignment", "student", "file", "submitted_at", "grade", "created_at", "updated_at"]
        read_only_fields = ["id", "student", "submitted_at", "grade", "created_at", "updated_at"]

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = '__all__'