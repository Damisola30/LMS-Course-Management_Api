# mainapp/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCourseOwnerOrReadOnly(BasePermission):
    """
    Allow read to any authenticated user with 'view' perm.
    Allow edit only if the requesting user is the course instructor.
    """
    def has_object_permission(self, request, view, obj):
        print("Checking IsCourseOwnerOrReadOnly for user:", request.user)#debug
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
        print("Checking IsOwnSubmissionOrCourseTeacher for user:", request.user)#debug
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
        print("Checking IsOwnProgressOrCourseTeacher for user:", request.user)#debug
        if request.user and request.user.is_superuser:
            return True
        teacher = getattr(request.user, "teacher", None)
        if teacher and obj.lesson.course.instructor_id == teacher.id:
            return True
        student = getattr(request.user, "student", None)
        if student and obj.student_id == student.id:
            return True
        return False

class IsOwnProfileOrAdmin(BasePermission):
    """
    Allow access to the object if the user is the owner (user==obj.user)
    or if the user is superuser/staff.
    READ is allowed to authenticated users (or change as you prefer).
    """
    def has_object_permission(self, request, view, obj):
        print("Checking IsOwnProfileOrAdmin for user:", request.user)
        # superuser or staff bypass
        if request.user and request.user.is_superuser:
            return True

        # read methods allowed if you want (or restrict)
        if request.method in SAFE_METHODS:
            return True

        # obj is either Teacher or Student instance with .user relation
        owner = getattr(obj, "user", None)
        return owner is not None and owner == request.user


class HasWorkspace(BasePermission):
    message = "Valid API key required (missing/expired)."

    def has_permission(self, request, view):
        # Allow superusers to bypass if you want:
        #if request.user and request.user.is_superuser:
            #return True
        print("Workspace in request:", hasattr(request, "workspace"))#debug
        return hasattr(request, "workspace")


class IsUserInWorkspace(BasePermission):
    message = "Your account does not belong to this workspace."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            print("User not authenticated")
            return False
        ws = getattr(request, "workspace", None)
        if not ws:
            print("No workspace in request")
            return False
        if request.user.is_superuser:
            print("User is superuser, bypassing workspace check")
            return True
        # derive user's workspace
        user_ws_id = None

        if hasattr(request.user, "teacher"):
            teacher = getattr(request.user, "teacher", None)
            if teacher:
                user_ws_id = teacher.workspace_id

        if user_ws_id is None and hasattr(request.user, "student"):
            student = getattr(request.user, "student", None)
            if student:
                user_ws_id = student.workspace_id

        if user_ws_id is None and hasattr(request.user, "guest"):
            guest = getattr(request.user, "guest", None)
            if guest:
                user_ws_id = guest.workspace_id

        return user_ws_id == ws.id