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
    instructor = serializers.PrimaryKeyRelatedField(read_only=True)  # client cannot set
    students = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Student.objects.all())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ws = getattr(self.context.get("request"), "workspace", None)
        if ws:
            self.fields["students"].queryset = Student.objects.filter(workspace=ws)
    class Meta:
        model = Course
        fields = [
            "id", "title", "description", "instructor", "students",
            "start_date", "end_date", "duration", "is_active",
            "created_at", "updated_at", "summary", "category", "level"
        ]
    def validate(self, attrs):
        # Ensuring end_date >= start_date
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end < start:
            raise serializers.ValidationError("end_date must be the same or after start_date.")
        return attrs


    def validate_title(self, value):
        if Course.objects.filter(title=value).exists():
            raise serializers.ValidationError("A course with this title already exists.")
        return value
    
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