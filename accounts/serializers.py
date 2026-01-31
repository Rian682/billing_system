from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role']
        read_only_fields = ['id']

# Separate serializer for registration including password
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # user = User.objects.create(
        #     username=validated_data['username'],
        #     email=validated_data.get('email', ''),
        #     password = validated_data['password'],
        #     phone=validated_data.get('phone', ''),
        #     role=validated_data['role'],
        # )
        return user