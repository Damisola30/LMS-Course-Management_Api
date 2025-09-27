# mainapp/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, IsAdminUser
from .models import Teacher, Student, Course, CourseMaterial, Assignment, Submission, Lesson, Progress, Guest
from .serializers import (
    TeacherSerializer, StudentSerializer, CourseSerializer, CourseMaterialSerializer,
    AssignmentSerializer, SubmissionStudentSerializer, SubmissionTeacherSerializer, LessonSerializer, ProgressSerializer, UserDetailsSerializer,UserSummarySerializer
)
from .permissions import (
    IsCourseOwnerOrReadOnly,
    IsOwnSubmissionOrCourseTeacher,
    IsOwnProgressOrCourseTeacher,
    IsOwnProfileOrAdmin,
    HasWorkspace,
    IsUserInWorkspace
)
from rest_framework import serializers  # for ValidationError

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
# Teacher and Student viewsets: use DjangoModelPermissions so admin/perm-coded users can manage them.
# In many designs Teacher/Student creation happens via registration (accounts app) so you may only
# need list/retrieve for normal users. Keeping DjangoModelPermissions allows fine-grained control.
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [HasWorkspace,IsUserInWorkspace, IsAuthenticated, DjangoModelPermissions, IsOwnProfileOrAdmin]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Teacher.objects.filter(workspace=workspace)

        user = self.request.user
        if user.is_superuser:
            return Teacher.objects.all()
        # teachers can see only themselves; admins can see all
        if hasattr(user, "teacher"):
            return Teacher.objects.filter(pk=user.teacher.pk)
        # admins, staff or those with view_teacher perm would be allowed by DjangoModelPermissions
        return Teacher.objects.none()
    
    @action(detail=True, methods=["patch"], url_path="user_details")
    def update_user_details(self, request, pk=None):
        teacher = self.get_object()
        user = teacher.user
        serializer = UserDetailsSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated,HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsOwnProfileOrAdmin]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Student.objects.filter(workspace=workspace)

        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        if hasattr(user, "student"):
            return Student.objects.filter(pk=user.student.pk)
        return Student.objects.none()
    
    @action(detail=True, methods=["patch"], url_path="user_details")
    def update_user_details(self, request, pk=None):
        student = self.get_object()
        user = student.user
        serializer = UserDetailsSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersViews(APIView):
    permission_classes = [HasWorkspace]

    def get(self, request):
        workspace = request.workspace
        teachers = Teacher.objects.filter(workspace=workspace).select_related('user')
        students = Student.objects.filter(workspace=workspace).select_related('user')
        guests = Guest.objects.filter(workspace=workspace).select_related('user')
        return Response({
            "teachers": UserSummarySerializer([t.user for t in teachers if t.user], many=True).data,
            "students": UserSummarySerializer([s.user for s in students if s.user], many=True).data,
            "guests": UserSummarySerializer([g.user for g in guests if g.user], many=True).data,
        })


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # IsAuthenticated ensures the user is logged in.
    # DjangoModelPermissions checks model-level add/view/change/delete perms.
    # IsCourseOwnerOrReadOnly enforces that only the instructor (teacher) can modify their own course.
    permission_classes = [IsAuthenticated,HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Course.objects.filter(workspace=workspace)

        user = self.request.user
        if user.is_superuser:
            return Course.objects.all()
        if hasattr(user, "teacher"):
            return Course.objects.filter(instructor=user.teacher)
        if hasattr(user, "student"):
            return Course.objects.filter(students=user.student)
        return Course.objects.none()
    
    def _request_includes_instructor(self):
        """
        Helper: checks whether the raw request payload included an instructor field.
        We use request.data (works for JSON/form/multipart).
        """
        return 'instructor' in (self.request.data or {})
    
    def perform_create(self, serializer):
        ws = getattr(self.request, "workspace", None)
        if not ws:
        # If you added HasWorkspace permission, this branch should never hit
            raise PermissionDenied("Missing or invalid API key (workspace not set).")

        user = self.request.user

        # If a teacher is creating, forbid them from supplying instructor explicitly.
        # (Either ignore it quietly or raise an error — here we raise to be explicit.)
        if hasattr(user, "teacher"):
                # 👇 New: ensure this teacher actually belongs to this workspace
                # (only works if Teacher has a workspace FK; if you haven't added it yet, you can drop this check)
                if getattr(user.teacher, "workspace_id", None) and user.teacher.workspace != ws.id:
                    raise PermissionDenied("Your teacher profile does not belong to this workspace.")

                # Your existing guard: teachers may not set instructor explicitly
                if self._request_includes_instructor():
                    raise PermissionDenied("You may not set the instructor manually. The instructor will be set to your account.")

                # 👇 New: force the course into THIS workspace
                serializer.save(instructor=user.teacher, workspace=ws)
                return

            # --- Your existing admin branch, kept intact ---
        if user.is_superuser:
            instructor = serializer.validated_data.get("instructor", None)

            # 👇 New: if admin supplies an instructor, it must belong to this workspace
            if instructor and getattr(instructor, "workspace_id", None) and instructor.workspace_id != ws.id:
                raise PermissionDenied("Instructor is not in this workspace.")

            # 👇 Optional but recommended: if students are passed at create time, ensure they’re in this workspace
            students = serializer.validated_data.get("students", [])
            for s in students:
                if getattr(s, "workspace_id", None) and s.workspace_id != ws.id:
                    raise serializers.ValidationError("All students must belong to this workspace.")

            # 👇 New: force workspace on save (admin can set or omit instructor)
            serializer.save(instructor=instructor, workspace=ws)
            return

        # --- Your existing default branch ---
        raise PermissionDenied("Only teachers or admins can create courses.")
    
    def update(self, request, *args, **kwargs):
        """
        Handles both PUT and PATCH (DRF calls update for both).
        Disallow an instructor user from changing the course's instructor field.
        Admins are allowed.
        """
        user = request.user

        # If the user is a teacher (instructor), block any attempt to change instructor
        if hasattr(user, "teacher"):
            if self._request_includes_instructor():
                # explicit message
                raise PermissionDenied("You cannot change the course instructor. Contact an admin to change the instructor.")
        # If user is superuser, allow changes (default flow)
        return super().update(request, *args, **kwargs)


class CourseMaterialViewSet(viewsets.ModelViewSet):
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated, HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return CourseMaterial.objects.filter(workspace=workspace)

        user = self.request.user
        if user.is_superuser:
            return CourseMaterial.objects.all()
        if hasattr(user, "teacher"):
            return CourseMaterial.objects.filter(course__instructor=user.teacher)
        if hasattr(user, "student"):
            return CourseMaterial.objects.filter(course__students=user.student)
        return CourseMaterial.objects.none()

    def perform_create(self, serializer):
        ws = getattr(self.request, "workspace", None)
        if not ws:
            raise PermissionDenied("Missing or invalid API key.")
        # enforce instructor same workspace (if you allow passing instructor)
        instructor = serializer.validated_data.get("instructor")
        if instructor and instructor.workspace_id != ws.id:
            raise serializers.ValidationError("Instructor is not in this workspace.")
        serializer.save(workspace=ws)  # 👈 force tenant    
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
    permission_classes = [IsAuthenticated, HasWorkspace,IsUserInWorkspace,  DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Assignment.objects.filter(workspace=workspace)
        
        user = self.request.user
        if user.is_superuser:
            return Assignment.objects.all()
        if hasattr(user, "teacher"):
            return Assignment.objects.filter(course__instructor=user.teacher)
        if hasattr(user, "student"):
            return Assignment.objects.filter(course__students=user.student)
        return Assignment.objects.none()

    def perform_create(self, serializer):
        ws = getattr(self.request, "workspace", None)
        course = serializer.validated_data.get("course")
        if course.workspace_id != ws.id:
            raise serializers.ValidationError("Course does not belong to this workspace.")
        serializer.save(workspace=ws)
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
    queryset = Submission.objects.select_related("assignment__course", "student__user").all()

    # Use object-level permission plus model perms
    permission_classes = [IsAuthenticated, HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsOwnSubmissionOrCourseTeacher]

    def get_serializer_class(self):
        user = self.request.user
        # superusers and teachers of the course should get teacher serializer
        if user.is_superuser or hasattr(user, "teacher"):
            return SubmissionTeacherSerializer
        # students use the student serializer
        return SubmissionStudentSerializer

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Submission.objects.filter(workspace=workspace)


        user = self.request.user
        if user.is_superuser:
            return self.queryset
        if hasattr(user, "teacher"):
            # teacher sees submissions for their courses
            return self.queryset.filter(assignment__course__instructor=user.teacher)
        if hasattr(user, "student"):
            # student sees only their submissions
            return self.queryset.filter(student=user.student)
        return Submission.objects.none()

    def perform_create(self, serializer):
        ws = getattr(self.request, "workspace", None)
        assignment = serializer.validated_data["assignment"]
        if assignment.workspace_id != ws.id:
            raise serializers.ValidationError("Assignment not in this workspace.")
        user = self.request.user
        if not hasattr(user, "student") or user.student.workspace_id != ws.id:
            raise PermissionDenied("Only students in this workspace can submit.")
        serializer.save(workspace=ws, student=user.student)
        # When a student creates a submission, attach their Student profile as owner.
        user = self.request.user
        if hasattr(user, "student"):
            serializer.save(student=user.student)
        else:
            raise PermissionDenied({"detail": "Only students can create submissions."})

    def update(self, request, *args, **kwargs):
        """
        Override update so we can enforce:
        - students can only change their own submission and only certain fields (handled by serializer),
          optionally only before assignment due_date.
        - teachers can only change grade (serializer allows it), but still object-level perm checked.
        """
        instance = self.get_object()
        user = request.user

        # If user is student: ensure they're owner (permission class already checks), optionally check deadline
        if hasattr(user, "student") and instance.student_id == user.student.id:
            # optional deadline check: disallow student edits after assignment due_date
            due = getattr(instance.assignment, "due_date", None)
            if due:
                now = timezone.now()
                # if due is timezone-aware and not comparable, adjust; assuming both timezone-aware
                if now > due:
                    raise PermissionDenied({"detail": "Cannot modify submission after the assignment due date."})
            # proceed normally (serializer will prevent grade changes)
            return super().update(request, *args, **kwargs)

        # If user is teacher of this course:
        if hasattr(user, "teacher") and instance.assignment.course.instructor_id == user.teacher.id:
            # allow teacher editing (it will use Teacher serializer which permits grade writes)
            return super().update(request, *args, **kwargs)

        # Allow superuser
        if user.is_superuser:
            return super().update(request, *args, **kwargs)

        # Otherwise deny
        raise PermissionDenied({"detail": "You do not have permission to modify this submission."})

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsCourseOwnerOrReadOnly]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Lesson.objects.filter(workspace=workspace)

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
    permission_classes = [IsAuthenticated, HasWorkspace,IsUserInWorkspace, DjangoModelPermissions, IsOwnProgressOrCourseTeacher]

    def get_queryset(self):
        # Priority 1: API key workspace
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return Progress.objects.filter(workspace=workspace)

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
