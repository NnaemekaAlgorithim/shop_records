from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.apps.users.models import Users
from django.utils import timezone 
import datetime
from user_management.apps.base.utils.response_structure import api_response
from rest_framework import exceptions
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import generics
from user_management.apps.users.emails import CustomActivationEmail
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.exceptions import Error as CloudinaryError
from drf_spectacular.utils import(
    extend_schema,
    OpenApiResponse,
    OpenApiExample
)
from user_management.apps.users.serializers import(
    ActivateUserSerializer,
    ErrorResponseSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer
)


class UserRegistrationViewSet(CreateModelMixin, GenericViewSet):
    queryset = Users.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="user_registration",
        summary="User Registration Endpoint",
        description="This endpoint allows users to register through standard form-based registration.",
        request=UserRegistrationSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="User registered successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Registration",
                        value={
                            "response_status": "success",
                            "response_description": "Registered successfully, kindly check your email for confirmation code.",
                            "response_data": {
                                "username": "new_user",
                                "email": "new_user@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "id": "01AKFHCNS33HDKS",
                            }
                        }
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation errors or other failures.",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "response_status": "failure",
                            "response_description": "User registration failed due to validation errors.",
                            "response_data": {
                                "email": ["This email is already in use."],
                                "username": ["This username is already taken."]
                            }
                        }
                    )
                ],
            )
        },
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            # Delegate user creation to the serializer
            user = serializer.save()

            # Generate and send activation code
            user.generate_activation_code()
            context = {
                "user": user,
                "activation_code": user.activation_code,
                "full_name": f'{user.first_name} {user.last_name}'
            }
            email = CustomActivationEmail(context)
            email.send([user.email])

            user_serializer = self.get_serializer(user)

            return api_response(
                response_status="success",
                response_description="User registered successfully, kindly check your email for confirmation code.",
                response_data=user_serializer.data,
            )
        except exceptions.ValidationError as e:
            return api_response(
                response_status="failure",
                response_description="User registration failed due to validation errors.",
                response_data=serializer.errors if hasattr(serializer, 'errors') else {'detail': str(e)},
            )
        except IntegrityError as e:
            return api_response(
                response_status="failure",
                response_description="User registration failed due to database integrity error.",
                response_data={'detail': str(e)},
            )
        except ValidationError as e:
            return api_response(
                response_status="failure",
                response_description="User registration failed due to model validation error.",
                response_data={'detail': str(e)},
            )
        except Exception as e:
            return api_response(
                response_status="failure",
                response_description="An unexpected error occurred during user registration.",
                response_data={'detail': str(e)},
            )


class ActivateUserView(generics.GenericAPIView):
    serializer_class = ActivateUserSerializer

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="activate_user",
        summary="Activate User Endpoint",
        description=(
            "This endpoint activates a user account using an activation code. "
            "It also supports resending the activation code via email."
        ),
        request=ActivateUserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="User activated successfully"
                "or activation code resent.",
                examples=[
                    OpenApiExample(
                        "Activation Successful",
                        value={
                            "response_status": "success",
                            "response_description": "User activated successfully",
                            "response_data": {
                                "user": {
                                    "id": "01AKFHCNS33HDKS",
                                    "email": "user@example.com",
                                    "first_name": "John",
                                    "last_name": "Doe"
                                },
                                "access_token": "access_token_here",
                                "refresh_token": "refresh_token_here",
                                "access_token_expiration": "2025-03-10T12:00:00Z",
                                "refresh_token_expiration": "2025-03-17T12:00:00Z",
                            }
                        },
                    ),
                    OpenApiExample(
                        "Code Resent",
                        value={
                            "response_status": "success",
                            "response_description": "A new activation code"
                            "has been sent to your email.",
                            "response_data": {}
                        }
                    ),
                ]
            ),
            400: OpenApiResponse(
                response=UserProfileSerializer,
                description="Invalid input or expired code.",
                examples=[
                    OpenApiExample(
                        "Invalid Code",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid or expired"
                            "activation code",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get('user_id')
        code = serializer.validated_data.get('code')
        resend_code = serializer.validated_data.get('resend_code', False)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return api_response(
                response_status='failure',
                response_description='Invalid User',
                response_data={}
            )

        if resend_code:
            # Generate a new activation code and send email
            user.generate_activation_code()
            context = {
                "user": user,
                "activation_code": user.activation_code,
                "full_name": f'{user.first_name} {user.last_name}'
            }
            email = CustomActivationEmail(context)
            email.send([user.email])
            return api_response(
                response_status='success',
                response_description='A new activation code '
                'has been sent to your email.',
                response_data={}
            )

        if user.is_activation_code_valid(code):
            # Activate user if the code is valid
            user.is_active = True
            user.activation_code = None
            user.activation_code_expiry = None
            user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            access_token_expiration = timezone.now() + datetime.timedelta(
                seconds=refresh.access_token.lifetime.total_seconds()
                )
            refresh_token_expiration = timezone.now() + datetime.timedelta(
                seconds=refresh.lifetime.total_seconds()
                )

            # Serialize user data
            user_data = UserProfileSerializer(user).data

            return api_response(
                response_status='success',
                response_description='User activated successfully',
                response_data={
                    "user": user_data,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "access_token_expiration": access_token_expiration.isoformat(),
                    "refresh_token_expiration": refresh_token_expiration.isoformat(),
                }
            )
        else:
            return api_response(
                response_status='failure',
                response_description='Invalid or expired activation code',
                response_data={}
            )


class LoginView(APIView):
    """
    Handle user login with email and password.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="user_login",
        summary="Login Endpoint",
        description="This endpoint handles user login with email and password.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Login successful.",
                examples=[
                    OpenApiExample(
                        "Standard Login Success",
                        value={
                            "response_status": "success",
                            "response_description": "Login successful.",
                            "response_data": {
                                "user": {
                                    "id": "01AKFHCNS33HDKS",
                                    "email": "user@example.com",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "shipping_address": {
                                        "country": "USA",
                                        "state": "California",
                                        "city": "Los Angeles",
                                        "street": "123 Main St",
                                        "postal_code": 90001,
                                        "timezone": "America/Los_Angeles"
                                    }
                                },
                                "access_token": "access_token_here",
                                "refresh_token": "refresh_token_here",
                                "access_token_expiration": "2025-03-10T12:00:00Z",
                                "refresh_token_expiration": "2025-03-17T12:00:00Z",
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=UserProfileSerializer,
                description="Invalid credentials or user not registered.",
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid email or password.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return api_response(
                response_status='failure',
                response_description='Invalid email or password.',
                response_data={},
            )

        if not user.check_password(password):
            return api_response(
                response_status='failure',
                response_description='Invalid email or password.',
                response_data={},
            )
        
        if user.blocked_user:
            return api_response(
                response_status='failure',
                response_description='You have been blocked, contact admin.',
                response_data={},
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Extract expiration times
        access_token_expiration = datetime.datetime.fromtimestamp(refresh.access_token.payload['exp'])
        refresh_token_expiration = datetime.datetime.fromtimestamp(refresh.payload['exp'])

        # Serialize user profile with shipping address
        user_data = UserProfileSerializer(user).data

        return api_response(
            response_status='success',
            response_description='Login successful.',
            response_data={
                "user": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "access_token_expiration": access_token_expiration.isoformat(),
                "refresh_token_expiration": refresh_token_expiration.isoformat(),
            },
        )
