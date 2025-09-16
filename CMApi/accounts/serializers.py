from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from mainapp.models import Teacher, Student   

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username","email","password","first_name","last_name","role")

    def create(self, validated_data):
        role = validated_data.pop("role")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.role = role
        user.save()

        # assign group
        group_name = role.capitalize()
        try:
            grp = Group.objects.get(name=group_name)
            grp.user_set.add(user)
        except Group.DoesNotExist:
            pass

        # create profile if needed
        if role == "teacher":
            Teacher.objects.create(user=user, specialization="", experience=0)
        elif role == "student":
            Student.objects.create(user=user, age=0)
        return user
