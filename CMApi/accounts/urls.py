from django.urls import path
from .views import RegisterView, ChangeUserRoleView, DeveloperRegisterView, DeveloperLoginView, DeveloperProfileView, DeveloperApiKeyView, DeleteApiKeyView

urlpatterns = [
    path("developer/register/", DeveloperRegisterView.as_view(), name="developer-register"),
    path("developer/login/", DeveloperLoginView.as_view(), name="developer-login"),
    path("developer/info/", DeveloperProfileView.as_view(), name="developer-info"),
    path("developer/api-key/", DeveloperApiKeyView.as_view(), name="developer-api-key"),
    path("developer/api-key/delete/", DeleteApiKeyView.as_view(), name="developer-api-key-delete"),
    path("register/", RegisterView.as_view(), name="register"),
    path("admin/change-role/<str:username>/", ChangeUserRoleView.as_view(), name="change_role"),
    #path("api-key/create/", CreateApiKeyView.as_view(), name="create_api_key"),
    #path("api-key/", GetApiKeyView.as_view(), name="get_api_key"),
]
