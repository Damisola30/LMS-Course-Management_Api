from django.urls import path
from .views import RegisterView, ChangeUserRoleView, DeveloperRegisterView, DeveloperLoginView, DeveloperProfileView, DeveloperApiKeyView, DeleteAPIKeyView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/register/", DeveloperRegisterView.as_view(), name="developer-register"),
    path("admin/login/", DeveloperLoginView.as_view(), name="developer-login"),
    path('admin/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("admin/info/", DeveloperProfileView.as_view(), name="developer-info"),
    path("admin/api-key/", DeveloperApiKeyView.as_view(), name="developer-api-key"),
    path("admin/api-key/delete/", DeleteAPIKeyView.as_view(), name="developer-api-key-delete"),
    path("register/", RegisterView.as_view(), name="register"),
    path("admin/change-role/<str:username>/", ChangeUserRoleView.as_view(), name="change_role"),
    #path("api-key/create/", CreateApiKeyView.as_view(), name="create_api_key"),
    #path("api-key/", GetApiKeyView.as_view(), name="get_api_key"),
]
