from django.urls import path
from .views import RegisterView, ChangeUserRoleView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("admin/change-role/<str:username>/", ChangeUserRoleView.as_view(), name="change_role"),
]
