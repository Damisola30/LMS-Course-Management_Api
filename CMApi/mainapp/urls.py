from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, StudentViewSet, CourseViewSet, CourseMaterialViewSet, AssignmentViewSet, SubmissionViewSet, LessonViewSet, ProgressViewSet,ListUsersViews
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.authentication import TenantTokenObtainPairView
from .views_seeds import SeedThisWorkspaceView


router = DefaultRouter()
router.register(r'teachers', TeacherViewSet)
router.register(r'students', StudentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'course-materials', CourseMaterialViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'submissions', SubmissionViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'progress', ProgressViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/login/', TenantTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/accounts/", include("accounts.urls")),
    path("api/dev/seed/", SeedThisWorkspaceView.as_view(), name="seed_this_workspace"),
    path("api/listusers/", ListUsersViews.as_view(), name ="List_Users")

]
