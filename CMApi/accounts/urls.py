from django.urls import path
from .views import RegisterView, ChangeUserRoleView, CreateApiKeyView, GetApiKeyView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("admin/change-role/<str:username>/", ChangeUserRoleView.as_view(), name="change_role"),
    path("api-key/create/", CreateApiKeyView.as_view(), name="create_api_key"),
    path("api-key/", GetApiKeyView.as_view(), name="get_api_key"),
]
