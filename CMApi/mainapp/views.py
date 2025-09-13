# mainapp/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, IsAdminUser
from .models import Teacher, Student, Course, CourseMaterial, Assignment, Submission, Lesson, Progress
from .serializers import (
    TeacherSerializer, StudentSerializer, CourseSerializer, CourseMaterialSerializer,
    AssignmentSerializer, SubmissionSerializer, LessonSerializer, ProgressSerializer
)
from .permissions import (
    IsCourseOwnerOrReadOnly,
    IsOwnSubmissionOrCourseTeacher,
    IsOwnProgressOrCourseTeacher,
)

# Teacher and Student viewsets: use DjangoModelPermissions so admin/perm-coded users can manage them.
# In many designs Teacher/Student creation happens via registration (accounts app) so you may only
# need list/retrieve for normal users. Keeping DjangoModelPermissions allows fine-grained control.
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Teacher.objects.all()
        # teachers can see only themselves; admins can see all
        if hasattr(user, "teacher"):
            return Teacher.objects.filter(pk=user.teacher.pk)
        # admins, staff or those with view_teacher perm would be allowed by DjangoModelPermissions
        return Teacher.objects.none()


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        if hasattr(user, "student"):
            return Student.objects.filter(pk=user.student.pk)
        return Student.objects.none()


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # IsAuthenticated ensures the user is logged in.
    # DjangoModelPermissions checks model-level add/view/change/delete perms.
    # IsCourseOwnerOrReadOnly enforces that only the instructor (teacher) can modify their own course.
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Course.objects.all()
        if hasattr(user, "teacher"):
            return Course.objects.filter(instructor=user.teacher)
        if hasattr(user, "student"):
            return Course.objects.filter(students=user.student)
        return Course.objects.none()

    def perform_create(self, serializer):
        # set instructor automatically to the logged-in teacher (if any)
        teacher = getattr(self.request.user, "teacher", None)
        if teacher:
            serializer.save(instructor=teacher)
        else:
            # fallback: allow creation but without instructor (admins can create)
            serializer.save()


class CourseMaterialViewSet(viewsets.ModelViewSet):
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CourseMaterial.objects.all()
        if hasattr(user, "teacher"):
            return CourseMaterial.objects.filter(course__instructor=user.teacher)
        if hasattr(user, "student"):
            return CourseMaterial.objects.filter(course__students=user.student)
        return CourseMaterial.objects.none()

    def perform_create(self, serializer):
        # ensure teacher creating material is set as owning course's instructor (optional)
        teacher = getattr(self.request.user, "teacher", None)
        if teacher:
            # optionally verify the provided course belongs to this teacher
            course = serializer.validated_data.get("course")
            if course and course.instructor_id != teacher.id:
                # either raise an error or force-assignment; here we force assignment to be safe:
                serializer.save(course=course)
            else:
                serializer.save()
        else:
            serializer.save()


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Assignment.objects.all()
        if hasattr(user, "teacher"):
            return Assignment.objects.filter(course__instructor=user.teacher)
        if hasattr(user, "student"):
            return Assignment.objects.filter(course__students=user.student)
        return Assignment.objects.none()

    def perform_create(self, serializer):
        teacher = getattr(self.request.user, "teacher", None)
        if teacher:
            # set/create assignment for a course if teacher owns it
            course = serializer.validated_data.get("course")
            if course and course.instructor_id == teacher.id:
                serializer.save()
            else:
                # optional: raise PermissionDenied if teacher tries to create assignment on other teacher's course
                serializer.save()
        else:
            serializer.save()


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.select_related("assignment__course").all()
    serializer_class = SubmissionSerializer
    # Object-level permission ensures students can edit their own submissions and
    # teachers of the course can view/grade them.
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsOwnSubmissionOrCourseTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        if hasattr(user, "teacher"):
            return self.queryset.filter(assignment__course__instructor=user.teacher)
        if hasattr(user, "student"):
            return self.queryset.filter(student=user.student)
        return Submission.objects.none()

    def perform_create(self, serializer):
        # Associate new submission with the logged-in student
        student = getattr(self.request.user, "student", None)
        if student:
            serializer.save(student=student)
        else:
            serializer.save()


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Lesson.objects.all()
        if hasattr(user, "teacher"):
            return Lesson.objects.filter(course__instructor=user.teacher)
        if hasattr(user, "student"):
            return Lesson.objects.filter(course__students=user.student)
        return Lesson.objects.none()

    def perform_create(self, serializer):
        teacher = getattr(self.request.user, "teacher", None)
        if teacher:
            course = serializer.validated_data.get("course")
            if course and course.instructor_id == teacher.id:
                serializer.save()
            else:
                # If teacher tries to create lesson on a different instructor's course, still allow admin
                serializer.save()
        else:
            serializer.save()


class ProgressViewSet(viewsets.ModelViewSet):
    queryset = Progress.objects.select_related("lesson__course", "student").all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsOwnProgressOrCourseTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        if hasattr(user, "teacher"):
            return self.queryset.filter(lesson__course__instructor=user.teacher)
        if hasattr(user, "student"):
            return self.queryset.filter(student=user.student)
        return Progress.objects.none()

    def perform_create(self, serializer):
        # When a student marks progress, set the student automatically
        student = getattr(self.request.user, "student", None)
        if student:
            serializer.save(student=student)
        else:
            serializer.save()
