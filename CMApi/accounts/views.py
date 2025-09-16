from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAdminUser
#from django.urls import reverse_lazy


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
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