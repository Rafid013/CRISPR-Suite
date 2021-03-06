from rest_framework import serializers
from django.contrib.auth.models import User


class UserSignUpSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User(username=validated_data['username'],
                    email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()
        return user

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# class PasswordResetSerializer(serializers.ModelSerializer):


