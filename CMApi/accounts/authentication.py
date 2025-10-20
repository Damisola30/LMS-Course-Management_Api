from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from .models import ApiKey
from rest_framework import permissions


class APIKeyAuthentication(BaseAuthentication):
    """
    Looks for X-API-Key header and attaches request.workspace and request.api_key.
    IMPORTANT: This DOES NOT authenticate `request.user` — allow JWT to authenticate the user.
    """
    def authenticate(self, request):
        key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if not key:
            return None  # let other authenticators (JWT) run

        try:
            ak = ApiKey.objects.select_related("developer", "developer__username").get(key=key, is_active=True)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")
        if ak :
            print("API key found for developer:", ak.developer.username)

        # Attach workspace and api_key object to request for later use in views
        request.developer = ak.developer
        request.api_key = ak

        # Return None to allow other authenticators (JWT) to set request.user.
        # If you want the API key itself to act as the "user", return (ak.workspace.owner, ak)
        return None



class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)  # authenticates username/password -> sets self.user
        request = self.context["request"]
        developer = getattr(request, "developer", None)
        if not developer:
            raise AuthenticationFailed("Valid API key required.")

        user = self.user
        print("user loginng ",self.user)
        # Determine user's workspace membership (no need if you added user.workspace)
        user_developer_id = None
        if hasattr(user, "teacher"):
            user_ws_id = user.teacher.workspace_id
        elif hasattr(user, "student"):
            user_ws_id = user.student.workspace_id
        elif hasattr(user, "guest"):
            user_ws_id = user.guest.workspace_id
        elif hasattr(user, "workspace_id"):
            user_ws_id = user.workspace_id  # optional, if you added FK

        # Superusers: either allow any tenant or restrict as you wish
        if not user.is_superuser:
            if user_developer_id != developer.id:
                raise AuthenticationFailed("This user does not belong to this workspace.")

        # optional: embed workspace info in token claims for auditing
        data["developer_id"] = developer.id
        data["developer"] = developer.username
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # optionally include role in the token
        token["role"] = getattr(user, "role", None)
        return token


class TenantTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]  # Workspace is enforced by serializer via header
    serializer_class = TenantTokenObtainPairSerializer
