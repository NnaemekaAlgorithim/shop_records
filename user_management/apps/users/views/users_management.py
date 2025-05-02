from user_management.apps.base.utils.response_structure import api_response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from user_management.apps.users.models import Notification, ShippingAddress, Users
from user_management.apps.users.views.filters import UserFilter
from user_management.apps.base.utils.pagination import CustomPagination
from user_management.apps.base.utils.permissions import IsStaffOrSuperUser
from cloudinary.uploader import upload as cloudinary_upload, destroy as cloudinary_destroy
from django.db import transaction
from rest_framework import generics
from user_management.apps.users.emails import(
    BlockedUserEmail,
    UnblockedUserEmail
)
from drf_spectacular.utils import(
    extend_schema,
    OpenApiResponse,
    OpenApiExample
)
from user_management.apps.users.serializers import(
    AdminAnnouncementSerializer,
    ProfileUpdateSerializer,
    ShippingAddressSerializer,
    UserListSerializer,
    UserProfileSerializer,
    NotificationSerializer
)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="user_profile",
        summary="Retrieve User Profile",
        description="This endpoint retrieves the authenticated user's profile details.",
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="User profile retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Response",
                        value={
                            "response_status": "success",
                            "response_description": "User profile retrieved successfully.",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS",
                                "email": "user@example.com",
                                "username": "john_doe",
                                "first_name": "John",
                                "last_name": "Doe",
                                "is_verified": True,
                                "date_joined": "2023-03-01T12:00:00Z",
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                response=UserProfileSerializer,
                description="Unauthorized request.",
                examples=[
                    OpenApiExample(
                        "Unauthorized Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Authentication credentials were not provided or are invalid.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileSerializer(user)

        if not user.is_active:
            return api_response(
                response_status='failure',
                response_description='Account is not active. Please activate your account.',
                response_data={},
            )
        
        if user.blocked_user:
            return api_response(
                response_status='failure',
                response_description='Account is blocked. Please contact admin to activate your account.',
                response_data={},
            )

        return api_response(
            response_status="success",
            response_description="User profile retrieved successfully.",
            response_data=serializer.data,
        )


class AdminUserListView(ListAPIView):
    permission_classes = [IsStaffOrSuperUser]
    queryset = Users.objects.all()
    serializer_class = UserListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'referral_code']
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="admin_user_list",
        summary="List Users with Filtering and Pagination",
        description="Retrieve a paginated list of admin, superuser, and staff users with filters and search capabilities. If a specific user_id is provided, the detailed user information including shipping address will be returned.",
        responses={
            200: OpenApiResponse(
                response=UserListSerializer,
                description="User list retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Response",
                        value={
                            "response_status": "success",
                            "response_description": "Users retrieved successfully.",
                            "response_data": {
                                "count": 2,
                                "next": None,
                                "previous": None,
                                "result": [
                                    {
                                        "id": "01AKFHCNS33HDKS",
                                        "email": "admin@example.com",
                                        "username": "admin_user",
                                        "first_name": "Admin",
                                        "last_name": "User",
                                        "is_staff": True,
                                        "is_superuser": True,
                                        "is_active": True,
                                        "date_joined": "2023-03-01T12:00:00Z",
                                        "referral_code": "REF12345",
                                        "shipping_address": {
                                            "country": "USA",
                                            "state": "California",
                                            "city": "Los Angeles",
                                            "street": "123 Main St",
                                            "postal_code": 90001
                                        }
                                    },
                                    {
                                        "id": "01AKFHCNS33HDKS2",
                                        "email": "staff@example.com",
                                        "username": "staff_user",
                                        "first_name": "Staff",
                                        "last_name": "User",
                                        "is_staff": True,
                                        "is_superuser": False,
                                        "is_active": True,
                                        "date_joined": "2023-05-01T12:00:00Z",
                                        "referral_code": "REF12345",
                                        "shipping_address": {}
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                response=UserListSerializer,
                description="Unauthorized request.",
                examples=[
                    OpenApiExample(
                        "Unauthorized Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Authentication credentials were not provided or are invalid.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        # Check if specific user ID is being filtered
        user_id = request.query_params.get('id', None)
        if user_id:
            try:
                user = Users.objects.get(id=user_id)
                user_data = UserProfileSerializer(user).data

                return api_response(
                    response_status="success",
                    response_description="User details retrieved successfully.",
                    response_data=user_data,
                )
            except Users.DoesNotExist:
                return api_response(
                    response_status="failure",
                    response_description="User not found.",
                    response_data={},
                )

        # Otherwise, list all users with pagination and filters
        return super().get(request, *args, **kwargs)


class AdminBlockUserView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="block_user",
        summary="Block or Unblock User",
        description="This endpoint allows an admin to block or unblock a user.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "example": "01AKFHCNS33HDKS"},
                    "block": {"type": "boolean", "example": True}
                },
                "required": ["user_id", "block"]
            }
        },
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="User blocked or unblocked successfully.",
                examples=[
                    OpenApiExample(
                        "User Blocked",
                        value={
                            "response_status": "success",
                            "response_description": "User has been blocked successfully.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "User Unblocked",
                        value={
                            "response_status": "success",
                            "response_description": "User has been unblocked successfully.",
                            "response_data": {}
                        }
                    ),
                ]
            ),
            400: OpenApiResponse(
                response=UserProfileSerializer,
                description="Invalid input or user state.",
                examples=[
                    OpenApiExample(
                        "Already Blocked",
                        value={
                            "response_status": "failure",
                            "response_description": "User is already blocked.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "Already Unblocked",
                        value={
                            "response_status": "failure",
                            "response_description": "User is already unblocked.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        block = request.data.get('block', True)  # Default to blocking the user

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return api_response(
                response_status="failure",
                response_description="Invalid user ID.",
                response_data={}
            )

        # Check if the user is already in the desired state
        if block and user.blocked_user:
            return api_response(
                response_status="failure",
                response_description="User is already blocked.",
                response_data={}
            )
        elif not block and not user.blocked_user:
            return api_response(
                response_status="failure",
                response_description="User is already unblocked.",
                response_data={}
            )

        # Update user state and send email
        context = {
            "full_name": f"{user.first_name} {user.last_name}"
        }

        if block:
            user.block_user()
            email = BlockedUserEmail(context)
            email.send([user.email])
            return api_response(
                response_status="success",
                response_description="User has been blocked successfully.",
                response_data={}
            )
        else:
            user.unblock_user()
            email = UnblockedUserEmail(context)
            email.send([user.email])
            return api_response(
                response_status="success",
                response_description="User has been unblocked successfully.",
                response_data={}
            )


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="update_profile",
        summary="Update User Profile",
        description=(
            "This endpoint allows users to update their profile. "
            "To update only password, include the `password_update=true` parameter "
            "and pass in only password in the body of the request."
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=ProfileUpdateSerializer,
                description="Profile or password updated successfully.",
                examples=[
                    OpenApiExample(
                        "Profile Updated",
                        value={
                            "response_status": "success",
                            "response_description": "Profile updated successfully.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "Password Updated",
                        value={
                            "response_status": "success",
                            "response_description": "Password updated successfully.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ProfileUpdateSerializer,
                description="Invalid input or bad request.",
                examples=[
                    OpenApiExample(
                        "Invalid Input",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid data provided.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def put(self, request, *args, **kwargs):
        password_update = request.query_params.get('password_update', 'false').lower() == 'true'
        user = request.user
        serializer = ProfileUpdateSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if password_update:
            # Ensure password is present for password updates
            new_password = serializer.validated_data.get('password')
            if not new_password:
                return api_response(
                    response_status="failure",
                    response_description="Password is required to update.",
                    response_data={}
                )
            user.set_password(new_password)
            user.save()
            return api_response(
                response_status="success",
                response_description="Password updated successfully.",
                response_data={}
            )
        elif 'password' in serializer.validated_data:
            # Reject password updates without password_update=true
            return api_response(
                response_status="failure",
                response_description="Password cannot be updated without setting password_update=true.",
                response_data={}
            )
        else:
            # Handle profile photo update with Cloudinary
            profile_photo = request.FILES.get('profile_photo')
            if profile_photo:
                # Delete the old photo if it exists
                if user.profile_photo and user.profile_photo.public_id:
                    cloudinary_destroy(user.profile_photo.public_id)

                # Upload the new photo to Cloudinary
                cloudinary_response = cloudinary_upload(
                    profile_photo,
                    folder="user_profiles",  # Optional: Specify a folder in Cloudinary
                )
                user.profile_photo = cloudinary_response['secure_url']

            serializer.save()
            return api_response(
                response_status="success",
                response_description="Profile updated successfully.",
                response_data={}
            )


class CreateShippingAddressView(generics.GenericAPIView):
    """
    Endpoint for creating a shipping address for authenticated users.
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="create_shipping_address",
        summary="Create Shipping Address Endpoint",
        description="This endpoint allows authenticated users to create a shipping address. Each user can only have one shipping address.",
        request=ShippingAddressSerializer,
        responses={
            201: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address created successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "response_status": "success",
                            "response_description": "Shipping address created successfully",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS",
                                "country": "USA",
                                "state": "California",
                                "city": "Los Angeles",
                                "street": "123 Main St",
                                "postal_code": 90001,
                                "user": {
                                    "id": "01AKFHCNS33HDKS",
                                    "email": "admin@example.com",
                                    "username": "admin_user",
                                    "first_name": "Admin",
                                    "last_name": "User",
                                    "is_staff": True,
                                    "is_superuser": True,
                                    "is_active": True,
                                    "date_joined": "2023-03-01T12:00:00Z",
                                    "referral_code": "REF12345"
                                }
                            }
                        },
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Validation error or duplicate entry.",
                examples=[
                    OpenApiExample(
                        "Duplicate Entry",
                        value={
                            "response_status": "failure",
                            "response_description": "User already has a shipping address.",
                            "response_data": {}
                        },
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Attempt to save the shipping address
            shipping_address = serializer.save(user=request.user)

            return api_response(
                response_status="success",
                response_description="Shipping address created successfully",
                response_data=serializer.data
            )
        except IntegrityError:
            return api_response(
                response_status="failure",
                response_description="User already has a shipping address.",
                response_data={}
            )
        except Exception as e:
            return api_response(
                response_status="failure",
                response_description="An error occurred while processing the request.",
                response_data={"detail": str(e)}
            )


class ReadShippingAddressView(generics.GenericAPIView):
    """
    Endpoint for retrieving the shipping address of the authenticated user.
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="read_shipping_address",
        summary="Read Shipping Address Endpoint",
        description="This endpoint allows authenticated users to retrieve their shipping address.",
        responses={
            200: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "response_status": "success",
                            "response_description": "Shipping address retrieved successfully",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS",
                                "country": "USA",
                                "state": "California",
                                "city": "Los Angeles",
                                "street": "123 Main St",
                                "postal_code": 90001,
                                "user": {
                                    "id": "01AKFHCNS33HDKS",
                                    "email": "admin@example.com",
                                    "username": "admin_user",
                                    "first_name": "Admin",
                                    "last_name": "User",
                                    "is_staff": True,
                                    "is_superuser": True,
                                    "is_active": True,
                                    "date_joined": "2023-03-01T12:00:00Z",
                                    "referral_code": "REF12345"
                                }
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address not found.",
                examples=[
                    OpenApiExample(
                        "Not Found",
                        value={
                            "response_status": "failure",
                            "response_description": "Shipping address not found.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
            serializer = self.get_serializer(shipping_address)
            return api_response(
                response_status="success",
                response_description="Shipping address retrieved successfully",
                response_data=serializer.data
            )
        except ShippingAddress.DoesNotExist:
            return api_response(
                response_status="failure",
                response_description="Shipping address not found.",
                response_data={}
            )


class UpdateShippingAddressView(generics.GenericAPIView):
    """
    Endpoint for updating the shipping address of the authenticated user.
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="update_shipping_address",
        summary="Update Shipping Address Endpoint",
        description="This endpoint allows authenticated users to update their shipping address.",
        request=ShippingAddressSerializer,
        responses={
            200: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address updated successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "response_status": "success",
                            "response_description": "Shipping address updated successfully",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS",
                                "country": "USA",
                                "state": "California",
                                "city": "Los Angeles",
                                "street": "456 Elm St",
                                "postal_code": 90002,
                                "user": {
                                    "id": "01AKFHCNS33HDKS",
                                    "email": "admin@example.com",
                                    "username": "admin_user",
                                    "first_name": "Admin",
                                    "last_name": "User",
                                    "is_staff": True,
                                    "is_superuser": True,
                                    "is_active": True,
                                    "date_joined": "2023-03-01T12:00:00Z",
                                    "referral_code": "REF12345"
                                }
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Validation error.",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid data provided.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def put(self, request, *args, **kwargs):
        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
            serializer = self.get_serializer(shipping_address, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return api_response(
                response_status="success",
                response_description="Shipping address updated successfully",
                response_data=serializer.data
            )
        except ShippingAddress.DoesNotExist:
            return api_response(
                response_status="failure",
                response_description="Shipping address not found.",
                response_data={}
            )


class DeleteShippingAddressView(generics.GenericAPIView):
    """
    Endpoint for deleting the shipping address of the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="delete_shipping_address",
        summary="Delete Shipping Address Endpoint",
        description="This endpoint allows authenticated users to delete their shipping address.",
        responses={
            204: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address deleted successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "response_status": "success",
                            "response_description": "Shipping address deleted successfully.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ShippingAddressSerializer,
                description="Shipping address not found.",
                examples=[
                    OpenApiExample(
                        "Not Found",
                        value={
                            "response_status": "failure",
                            "response_description": "Shipping address not found.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
            shipping_address.delete()
            return api_response(
                response_status="success",
                response_description="Shipping address deleted successfully.",
                response_data={}
            )
        except ShippingAddress.DoesNotExist:
            return api_response(
                response_status="failure",
                response_description="Shipping address not found.",
                response_data={}
            )


class AdminToggleStaffStatusView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="toggle_staff_status",
        summary="Toggle User Staff Status",
        description="This endpoint allows an admin to make a user a staff member or remove their staff privileges.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "example": "01AKFHCNS33HDKS"},
                    "is_staff": {"type": "boolean", "example": True}
                },
                "required": ["user_id", "is_staff"]
            }
        },
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="User staff status updated successfully.",
                examples=[
                    OpenApiExample(
                        "Staff Added",
                        value={
                            "response_status": "success",
                            "response_description": "User has been granted staff privileges successfully.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "Staff Removed",
                        value={
                            "response_status": "success",
                            "response_description": "User's staff privileges have been removed successfully.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=UserProfileSerializer,
                description="Invalid input or user state.",
                examples=[
                    OpenApiExample(
                        "Already Staff",
                        value={
                            "response_status": "failure",
                            "response_description": "User is already a staff member.",
                            "response_data": {}
                        }
                    ),
                    OpenApiExample(
                        "Already Not Staff",
                        value={
                            "response_status": "failure",
                            "response_description": "User is already not a staff member.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        is_staff = request.data.get('is_staff')

        if is_staff is None:
            return api_response(
                response_status="failure",
                response_description="The 'is_staff' field is required.",
                response_data={}
            )

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return api_response(
                response_status="failure",
                response_description="Invalid user ID.",
                response_data={}
            )

        # Check if the user's staff status matches the desired state
        if is_staff and user.is_staff:
            return api_response(
                response_status="failure",
                response_description="User is already a staff member.",
                response_data={}
            )
        elif not is_staff and not user.is_staff:
            return api_response(
                response_status="failure",
                response_description="User is already not a staff member.",
                response_data={}
            )

        # Update user staff status and send notification
        notification_messages = {
            True: (
                f"Dear {user.first_name} {user.last_name},\n"
                f"You have been granted staff privileges. Welcome to the team!\n\n"
                f"Best regards,\nThe Admin Team"
            ),
            False: (
                f"Dear {user.first_name} {user.last_name},\n"
                f"Your staff privileges have been revoked. If you have any questions, please contact the admin team.\n\n"
                f"Best regards,\nThe Admin Team"
            )
        }

        user.is_staff = is_staff
        user.save()

        # Create notification
        Notification.objects.create(
            user=user,
            title="Staff Privileges Updated",
            message=notification_messages[is_staff]
        )

        description = (
            "User has been granted staff privileges successfully."
            if is_staff else
            "User's staff privileges have been removed successfully."
        )

        return api_response(
            response_status="success",
            response_description=description,
            response_data={}
        )


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="delete_account",
        summary="Delete User Account",
        description=(
            "This endpoint allows users to delete their account along with "
            "any models or data related to them."
        ),
        responses={
            200: OpenApiResponse(
                response=ProfileUpdateSerializer,
                description="Account deleted successfully.",
                examples=[
                    OpenApiExample(
                        "Account Deleted",
                        value={
                            "response_status": "success",
                            "response_description": "User account deleted successfully.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ProfileUpdateSerializer,
                description="Bad request or error during deletion.",
                examples=[
                    OpenApiExample(
                        "Deletion Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Failed to delete user account.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user

        try:
            with transaction.atomic():
                # Explicitly delete related models if necessary
                # Example: If user has related "Shop" models or other dependencies
                if hasattr(user, 'shop'):
                    user.shop.delete()

                if hasattr(user, 'shipping_addresses'):
                    user.shipping_addresses.delete()

                # Add more explicit deletions here if required
                # e.g., user.orders.all().delete()

                # Delete the user account
                user.delete()

            return api_response(
                response_status="success",
                response_description="User account deleted successfully.",
                response_data={}
            )
        except Exception as e:
            return api_response(
                response_status="failure",
                response_description="Failed to delete user account.",
                response_data={"error": str(e)}
            )


class NotificationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id']
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="notification_list",
        summary="List Notifications with Filtering and Pagination",
        description="Retrieve a paginated list of notifications. If a specific notification ID is provided as a query parameter, the full details of that notification are returned and it is marked as read.",
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer,
                description="Notifications retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Response - All Notifications",
                        value={
                            "response_status": "success",
                            "response_description": "Notifications retrieved successfully.",
                            "response_data": {
                                "count": 2,
                                "next": None,
                                "previous": None,
                                "result": [
                                    {"id": "01AKFHCNS33HDKS2", "title": "Welcome Notification"},
                                    {"id": "01AKFHCNS33HDKS2", "title": "Reminder: Update Profile"},
                                ]
                            }
                        }
                    ),
                    OpenApiExample(
                        "Successful Response - Single Notification",
                        value={
                            "response_status": "success",
                            "response_description": "Notification details retrieved successfully.",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS2",
                                "title": "Welcome Notification",
                                "message": "Thank you for joining our platform.",
                                "is_read": True,
                                "created_at": "2024-03-20T10:00:00Z"
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                response=NotificationSerializer,
                description="Unauthorized request.",
                examples=[
                    OpenApiExample(
                        "Unauthorized Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Authentication credentials were not provided or are invalid.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        notification_id = request.query_params.get('id', None)

        if notification_id:
            # Retrieve and mark the notification as read
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()

                return api_response(
                    response_status="success",
                    response_description="Notification details retrieved successfully.",
                    response_data=NotificationSerializer(notification).data,
                )
            except Notification.DoesNotExist:
                return api_response(
                    response_status="failure",
                    response_description="Notification not found.",
                    response_data={},
                )

        # Use default pagination for listing notifications
        self.queryset = Notification.objects.filter(user=request.user).only('id', 'title').order_by('-created_at')
        return super().get(request, *args, **kwargs)


class AdminNotificationListView(ListAPIView):
    permission_classes = [IsStaffOrSuperUser]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id', 'user']
    search_fields = ['title', 'content']
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="admin_notification_list",
        summary="List All Notifications for Admin",
        description="Retrieve a paginated list of all notifications. Admins can filter notifications by ID or user.",
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer,
                description="Notifications retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Response - All Notifications",
                        value={
                            "response_status": "success",
                            "response_description": "Notifications retrieved successfully.",
                            "response_data": {
                                "count": 10,
                                "next": None,
                                "previous": None,
                                "result": [
                                    {
                                        "id": 1,
                                        "user": {
                                            "id": 1,
                                            "username": "john_doe",
                                            "email": "john@example.com"
                                        },
                                        "title": "Welcome Notification",
                                        "content": "Welcome to our platform!",
                                        "is_read": False,
                                        "created_at": "2023-08-15T12:00:00Z"
                                    },
                                    # More notifications...
                                ]
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                response=NotificationSerializer,
                description="Forbidden",
                examples=[
                    OpenApiExample(
                        "Forbidden Error",
                        value={
                            "response_status": "failure",
                            "response_description": "You do not have permission to perform this action.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminSendNotificationView(APIView):
    """
    Endpoint for admins to send notifications to all active users.
    """
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="admin_send_announcement",
        summary="Send Announcement to All Users",
        description=(
            "Allows administrators to send an announcement notification to all active users. "
            "The notification message must be provided in the request body."
        ),
        request=AdminAnnouncementSerializer,
        responses={
            200: OpenApiResponse(
                response=AdminAnnouncementSerializer,
                description="Announcement sent successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Response - Announcement Sent",
                        value={
                            "response_status": "success",
                            "response_description": "Announcement sent successfully to all users.",
                            "response_data": {
                                "message": "Notifications sent to all users."
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                response=AdminAnnouncementSerializer,
                description="Forbidden",
                examples=[
                    OpenApiExample(
                        "Forbidden Error",
                        value={
                            "response_status": "failure",
                            "response_description": "You do not have permission to perform this action.",
                            "response_data": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=AdminAnnouncementSerializer,
                description="Bad Request: Validation failed.",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Invalid input data.",
                            "response_data": {
                                "error": "Message is required."
                            }
                        }
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = AdminAnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        # Get all active users
        active_users = Users.objects.filter(is_active=True)

        # Create notifications for each active user
        notifications = [
            Notification(
                user=user,
                title="Announcement",
                content=message,
            )
            for user in active_users
        ]
        Notification.objects.bulk_create(notifications)

        return api_response(
            response_status="success",
            response_description="Announcement sent successfully to all users.",
            response_data={"message": "Notifications sent to all users."}
        )
