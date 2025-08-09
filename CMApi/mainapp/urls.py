from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, StudentViewSet, CourseViewSet, CourseMaterialViewSet, AssignmentViewSet, SubmissionViewSet, LessonViewSet, ProgressViewSet


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
    path('', include(router.urls))
    ]
