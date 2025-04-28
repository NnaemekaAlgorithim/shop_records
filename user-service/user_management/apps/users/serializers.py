from rest_framework import serializers
from .models import Notification, ShippingAddress, Users
from django.contrib.auth import get_user_model
import random
import string


Users = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(required=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Optional. Leave blank if no password is set."
    )

    class Meta:
        model = Users
        fields = (
            'email', 'first_name', 'last_name', 'password', 
            'referred_by', 'id', 'phone_number', 'country_code', 'profile_photo'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def generate_unique_username(self):
        """Generate a unique 6-character username."""
        while True:
            username = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            if not Users.objects.filter(username=username).exists():
                return username

    def create(self, validated_data):
        # Extract and handle password
        password = validated_data.pop('password', None)

        # Generate a unique username
        username = self.generate_unique_username()

        # Create the user instance without setting a password yet
        user = Users.objects.create(
            email=validated_data.get('email'),
            username=username,
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            referred_by=validated_data.get('referred_by'),
            phone_number=validated_data.get('phone_number'),
            country_code=validated_data.get('country_code'),
            profile_photo=validated_data.get('profile_photo'),
        )

        # If a password is provided, set it; otherwise, leave it unset
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'profile_photo', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'referral_code', 'blocked_user'
        )


class ShippingAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShippingAddress
        fields = ["id", "country", "state", "city", "street", "postal_code", "timezone"]


class UserProfileSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(required=False)
    shipping_address = ShippingAddressSerializer(source="shipping_addresses", read_only=True)

    class Meta:
        model = Users
        exclude = ['password']

class ActivateUserSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    code = serializers.CharField(required=False)
    resend_code = serializers.BooleanField(default=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ErrorResponseSerializer(serializers.Serializer):
    response_status = serializers.CharField()
    response_description = serializers.CharField()
    response_data = serializers.DictField(child=serializers.ListField(child=serializers.CharField()), required=False)


class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            'first_name', 'last_name', 'password',
            'profile_photo', 'email', 'phone_number', 'country_code'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # Password is write-only and optional
        }

    def validate(self, attrs):
        """
        Ensure at least one field is provided for the update.
        """
        if not attrs:
            raise serializers.ValidationError("At least one field must be provided for the update.")
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'is_read',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]


class AdminAnnouncementSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=255, help_text="The announcement message to send to all shop owners.")
