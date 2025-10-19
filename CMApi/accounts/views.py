#i gats clean up or declutter this part  
from rest_framework import generics, permissions
from .serializers import RegisterSerializer, DeveloperRegisterSerializer, DeveloperLoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAdminUser
from .models import  ApiKey
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from mainapp.permissions import HasDeveloper
#from django.urls import reverse_lazy


User = get_user_model()
class DeveloperRegisterView(generics.CreateAPIView):
    """
    Endpoint: POST /auth/developer/register/
    Creates a new developer (system owner)
    """
    serializer_class = DeveloperRegisterSerializer
    permission_classes = [permissions.AllowAny]


class DeveloperLoginView(APIView):
    """
    Endpoint: POST /auth/developer/login/
    Logs in developer and issues JWT tokens
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = DeveloperLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class DeveloperProfileView(APIView):
    """
    Endpoint: GET /auth/developer/info/
    Returns current developer account info
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
        })

class DeveloperApiKeyView(APIView):
    """
    Handles developer API key operations.
    
    POST  → create or return API key (no rotation)
    GET   → fetch API key info
    DELETE → delete API key (requires username & password confirmation)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create or return the existing API key for the developer."""
        developer = request.user
        existing_key = ApiKey.objects.filter(developer=developer).first()

        if existing_key:
            return Response({
                "message": "API key already exists.",
                "api_key": existing_key.HashedKey
            }, status=status.HTTP_200_OK)
        
        api_key_obj, raw_key = ApiKey.create_for_dev(developer)

        return Response({
            "message": "API key created successfully.",
            "api_key": raw_key
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        """Retrieve the current API key for the developer."""
        developer = request.user
        api_key = ApiKey.objects.filter(developer=developer).first()
        if not api_key:
            return Response({"error": "No API key found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "api_key": api_key.HashedKey,
            "created_at": api_key.created_at,
        }, status=status.HTTP_200_OK)


class DeleteAPIKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Confirm developer identity
        user = authenticate(username=username, password=password)
        if user is None or user != request.user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_403_FORBIDDEN)

        # Delete the API key if exists
        api_key = ApiKey.objects.filter(developer=user).first()
        if not api_key:
            return Response({"error": "No API key found"}, status=status.HTTP_404_NOT_FOUND)

        api_key.delete()
        return Response({"message": "API key deleted successfully"}, status=status.HTTP_200_OK)
    

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny, HasDeveloper,IsAdminUser]
    # success_url = reverse_lazy('token_obtain_pair')


class ChangeUserRoleView(APIView):
    permission_classes = [IsAdminUser]  # only admin/staff can change roles

    def post(self, request, username):
        """
        POST /api/admin/change-role/<username>/
        body: { "role": "teacher" }
        """
        role = request.data.get("role")
        if not role:
            return Response({"detail":"role is required."}, status=status.HTTP_400_BAD_REQUEST)

        role = role.lower()
        if role not in dict(User.ROLE_CHOICES):
            return Response({"detail":"invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"user not found."}, status=status.HTTP_404_NOT_FOUND)

        # remove user from other role groups (Teacher, Student, Guest, Admin)
        possible_groups = [g.capitalize() for g,_ in User.ROLE_CHOICES]
        for gname in possible_groups:
            try:
                grp = Group.objects.get(name=gname)
                grp.user_set.remove(user)
            except Group.DoesNotExist:
                pass

        # add to new group
        group_name = role.capitalize()
        try:
            group = Group.objects.get(name=group_name)
            group.user_set.add(user)
        except Group.DoesNotExist:
            # optional: create group on the fly
            group = Group.objects.create(name=group_name)
            group.user_set.add(user)

        # update user.role field
        user.role = role
        user.save()

        return Response({"detail": f"{user.username} set to role {role}"})



# def _parse_ttl_hours(request, default=24, min_h=1, max_h=24*30):
#     """
#     Read ttl_hours from request.data and clamp/validate.
#     Returns (ttl_hours:int, error:str|None).
#     """
#     raw = request.data.get("hours", default)
#     try:
#         ttl = int(raw)
#     except (TypeError, ValueError):
#         return None, "ttl_hours must be an integer number of hours"

#     if ttl < min_h or ttl > max_h:
#         return None, f"ttl_hours must be between {min_h} and {max_h} hours"
#     return ttl, None


class CreateApiKeyView(APIView):
    permission_classes = [HasDeveloper]  # consider [permissions.IsAuthenticated]

    def post(self, request):
        user = request.data.get("username")
        if not workspace_name:
            return Response({"error": "username is required"}, status=status.HTTP_400_BAD_REQUEST)

        ttl_hours, err = _parse_ttl_hours(request)
        if err:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

        force_rotate = str(request.data.get("force_rotate", "false")).lower() in ("1", "true", "yes")

        ws, _ = Workspace.objects.get_or_create(name=workspace_name)

        # OneToOne: either an object exists or it doesn't
        try:
            ak = ws.api_key
        except ObjectDoesNotExist:
            ak = None

        now = timezone.now()
        new_exp = now + timedelta(hours=ttl_hours)

        # If a key exists and is still active
        if ak and (ak.expires_at is None or ak.expires_at > now):
            if force_rotate:
                # rotate + apply requested ttl_hours
                ak.key = ApiKey.generate_key()
                ak.expires_at = new_exp
                ak.save(update_fields=["key", "expires_at"])
                return Response({
                    "message": "API key rotated",
                    "api_key": ak.key,                # plaintext shown only now
                    "expires_at": ak.expires_at,
                    "ttl_hours": ttl_hours,
                }, status=status.HTTP_200_OK)

            # otherwise, return existing without changing expiry
            return Response({
                "message": "API key already exists for this workspace",
                "api_key": ak.key,                      # best practice: don't re-show plaintext
                #"key_prefix": ak.key,
                "expires_at": ak.expires_at,
            }, status=status.HTTP_200_OK)

        # No key or expired: create/refresh with requested ttl_hours
        if ak:
            ak.key = ApiKey.generate_key()
            ak.expires_at = new_exp
            ak.save(update_fields=["key", "expires_at"])
        else:
            ak = ApiKey.objects.create(workspace=ws, key=ApiKey.generate_key(), expires_at=new_exp)

        return Response({
            "message": "API key created successfully" if not force_rotate else "API key rotated",
            "api_key": ak.key,                        # plaintext at creation/rotation
            "expires_at": ak.expires_at,
            "ttl_hours": ttl_hours,
        }, status=status.HTTP_201_CREATED)


class GetApiKeyView(APIView):
    permission_classes = []  # consider [permissions.IsAuthenticated]

    def post(self, request):
        workspace_name = request.data.get("username")
        if not workspace_name:
            return Response({"error": "username is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ws = Workspace.objects.get(name=workspace_name)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            ak = ws.api_key
        except ObjectDoesNotExist:
            return Response({"error": "No API key found for this workspace"}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        if ak.expires_at and ak.expires_at <= now:
            return Response({"error": "API key has expired"}, status=status.HTTP_403_FORBIDDEN)

        # don’t return plaintext here; only metadata
        ttl_remaining_h = None
        if ak.expires_at:
            ttl_remaining_h = max(0, int((ak.expires_at - now).total_seconds() // 3600))

        return Response({
            "api_key": ak.key,
            "Expires_at": ak.expires_at,
            "Hours remaining": ttl_remaining_h,
        }, status=status.HTTP_200_OK)