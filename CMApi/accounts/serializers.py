from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from mainapp.models import Teacher, Student, Guest   
from django.db import transaction, IntegrityError

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username","email","password","first_name","last_name","role")

    def create(self, validated_data):
        request = self.context["request"]
        developer = getattr(request, "developer", None)

        if developer is None:
            raise serializers.ValidationError("API key header required.")

        role = validated_data.pop("role")
        raw_password = validated_data.pop("password")

        try:
            with transaction.atomic():
                # create user
                user = User(**validated_data)
                user.set_password(raw_password)
                user.role = role
                user.save()

                # assign group (best-effort)
                group_name = role.capitalize()
                try:
                    Group.objects.get(name=group_name).user_set.add(user)
                except Group.DoesNotExist:
                    pass

                # create tenant-bound profile
                if role == "teacher":
                    Teacher.objects.create(
                        user=user, developer=developer, specialization="", experience=0
                    )
                elif role == "student":
                    Student.objects.create(
                        user=user, developer=developer,  age=0
                    )
                elif role == "guest":
                    Guest.objects.create(
                        user=user, developer=developer, 
                    )

                return user

        except IntegrityError as e:
            # bubble up a clean API error
            raise serializers.ValidationError({"detail": "Could not register user", "error": str(e)})