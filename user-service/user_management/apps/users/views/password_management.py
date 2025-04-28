from user_management.apps.users.models import Users
from user_management.apps.base.utils.response_structure import api_response
from rest_framework import generics
from user_management.apps.users.emails import CustomActivationEmail
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import(
    extend_schema,
    OpenApiResponse,
    OpenApiExample
)
from user_management.apps.users.serializers import(
    ForgotPasswordRequestSerializer,
    ResetPasswordSerializer
)


class ForgotPasswordRequestView(generics.GenericAPIView):
    serializer_class = ForgotPasswordRequestSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="forgot_password_request",
        summary="Forgot Password Request Endpoint",
        description=(
            "This endpoint sends a password reset activation code to the user's email."
        ),
        request=ForgotPasswordRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=ForgotPasswordRequestSerializer,
                description="Reset code sent to email.",
                examples=[
                    OpenApiExample(
                        "Code Sent",
                        value={
                            "response_status": "success",
                            "response_description": "A reset code has been sent to your email.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ForgotPasswordRequestSerializer,
                description="Invalid email.",
                examples=[
                    OpenApiExample(
                        "Invalid Email",
                        value={
                            "response_status": "failure",
                            "response_description": "Email not associated with any account.",
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
        email = serializer.validated_data.get('email')

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return api_response(
                response_status='failure',
                response_description='Email not associated with any account.',
                response_data={}
            )

        # Generate activation code and send email
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
            response_description='A reset code has been sent to your email.',
            response_data={}
        )


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="reset_password",
        summary="Reset Password Endpoint",
        description=(
            "This endpoint resets the user's password using the email, reset code, "
            "new password, and confirm password."
        ),
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=ResetPasswordSerializer,
                description="Password reset successfully.",
                examples=[
                    OpenApiExample(
                        "Password Reset Successful",
                        value={
                            "response_status": "success",
                            "response_description": "Password reset successfully.",
                            "response_data": {}
                        },
                    ),
                ]
            ),
            400: OpenApiResponse(
                response=ResetPasswordSerializer,
                description="Invalid input or expired code.",
                examples=[
                    OpenApiExample(
                        "Invalid Code",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid or expired reset code.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "Passwords Do Not Match",
                        value={
                            "response_status": "failure",
                            "response_description": "New password and confirm password do not match.",
                            "response_data": {}
                        }
                    ),
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        code = serializer.validated_data.get('code')
        new_password = serializer.validated_data.get('new_password')
        confirm_password = serializer.validated_data.get('confirm_password')

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return api_response(
                response_status='failure',
                response_description='Invalid email.',
                response_data={}
            )

        if not user.is_activation_code_valid(code):
            return api_response(
                response_status='failure',
                response_description='Invalid or expired reset code.',
                response_data={}
            )

        if new_password != confirm_password:
            return api_response(
                response_status='failure',
                response_description='New password and confirm password do not match.',
                response_data={}
            )

        # Reset password
        user.set_password(new_password)
        user.activation_code = None
        user.activation_code_expiry = None
        user.save()

        return api_response(
            response_status='success',
            response_description='Password reset successfully.',
            response_data={}
        )
