from rest_framework import serializers

from bitpin_task.users.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        # read_only_fields = ["id", "name", "email"]

        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"required": True},
            "name": {"required": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
