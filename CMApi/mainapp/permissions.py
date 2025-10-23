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


from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Allows access only to users whose role is set to 'admin'.
    """
    message = "Admin role required."   
    def has_permission(self, request, view):
        user = request.user
        #print("Checking IsAdminRole for user:", user)  # debug

        return bool(user and user.is_authenticated and getattr(user, "role", None) == "admin")

    

class HasDeveloper(BasePermission):
    message = "Valid API key required (missing/expired)."

    def has_permission(self, request, view):
        # Check if middleware has attached the developer
        print("Developer in request:", hasattr(request, "developer"))  # debug
        return hasattr(request, "developer")


class IsUserUnderDeveloper(BasePermission):
    message = "Your account does not belong to this developer."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            print("User not authenticated")
            return False

        dev = getattr(request, "developer", None)
        if not dev:
            print("No developer in request (API key missing or invalid)")
            return False

        # Allow superuser to bypass if needed
        if user.is_superuser:
            print("Superuser detected, bypassing developer check")
            return True

        user_dev_id = None

        # Check the developer associated with this user (actor)
        if hasattr(user, "teacher"):
            user_dev_id = user.teacher.developer_id

        elif hasattr(user, "student"):
            user_dev_id = user.student.developer_id

        elif hasattr(user, "guest"):
            user_dev_id = user.guest.developer_id

        # Finally, compare the developer IDs
        return user_dev_id == dev.id
