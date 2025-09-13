# mainapp/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCourseOwnerOrReadOnly(BasePermission):
    """
    Allow read to any authenticated user with 'view' perm.
    Allow edit only if the requesting user is the course instructor.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # superuser bypass
        if request.user and request.user.is_superuser:
            return True
        # check teacher profile
        teacher = getattr(request.user, "teacher", None)
        return teacher is not None and obj.instructor_id == teacher.id


class IsOwnSubmissionOrCourseTeacher(BasePermission):
    """
    Student can manage own submission; teacher of the course can view/change.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_superuser:
            return True

        teacher = getattr(request.user, "teacher", None)
        if teacher and obj.assignment.course.instructor_id == teacher.id:
            return True

        student = getattr(request.user, "student", None)
        if student and obj.student_id == student.id:
            # allow read & change for own submission; you can restrict change methods if needed
            return True

        return False


class IsOwnProgressOrCourseTeacher(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_superuser:
            return True
        teacher = getattr(request.user, "teacher", None)
        if teacher and obj.lesson.course.instructor_id == teacher.id:
            return True
        student = getattr(request.user, "student", None)
        if student and obj.student_id == student.id:
            return True
        return False
