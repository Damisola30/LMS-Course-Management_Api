from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from mainapp.models import Teacher, Student, Guest
from django.db import transaction, IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


User = get_user_model()

class DeveloperRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(raw_password)
        user.role = "admin"  # You can rename to "developer" if you prefer
        user.save()
        return user


class DeveloperLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if user.role != "admin":  # or "developer"
            raise serializers.ValidationError("Only developers can log in here.")
        
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "role")

    def create(self, validated_data):
        request = self.context["request"]
        developer = getattr(request, "developer", None)

        if not developer:
            raise serializers.ValidationError("Valid API key header required.")

        role = validated_data.pop("role")
        raw_password = validated_data.pop("password")

        try:
            with transaction.atomic():
                # 1️⃣ Create base user
                user = User(**validated_data)
                user.set_password(raw_password)
                user.role = role
                user.save()

                # 2️⃣ Assign group automatically
                group_name = role.capitalize()
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

                # 3️⃣ Create tenant-bound role profile
                if role == "teacher":
                    Teacher.objects.create(
                        user=user, developer=developer,
                        specialization="Not set", experience=0
                    )
                elif role == "student":
                    Student.objects.create(user=user, developer=developer, age=0)
                elif role == "guest":
                    Guest.objects.create(user=user, developer=developer)

                return user

        except IntegrityError:
            raise serializers.ValidationError({"detail": "User creation failed due to data integrity issues."})
