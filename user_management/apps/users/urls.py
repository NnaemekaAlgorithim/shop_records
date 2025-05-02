from django.urls import path
from .views.login_registration import (
    ActivateUserView,
    LoginView,
    UserRegistrationViewSet
)
from .views.password_management import (
    ResetPasswordView,
    ForgotPasswordRequestView
)
from .views.users_management import (
    AdminBlockUserView,
    AdminToggleStaffStatusView,
    CreateShippingAddressView,
    DeleteAccountView,
    DeleteShippingAddressView,
    ProfileUpdateView,
    ReadShippingAddressView,
    UpdateShippingAddressView,
    UserProfileView,
    AdminUserListView,
    NotificationListView,
    AdminNotificationListView,
    AdminSendNotificationView
)


urlpatterns = [
    path('register/', UserRegistrationViewSet.as_view({'post': 'create'}), name='user-register'),
    path('activate/', ActivateUserView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot/password/', ForgotPasswordRequestView.as_view(), name='forgot-password-request'),
    path('password/reset/', ResetPasswordView.as_view(), name='reset-password'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/view/', AdminUserListView.as_view(), name='admin-users-view'),
    path('admin/block/', AdminBlockUserView.as_view(), name='admin-block-user'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('account/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('create/shipping/address/', CreateShippingAddressView.as_view(), name='create-shipping-address'),
    path('view/shipping/address/', ReadShippingAddressView.as_view(), name='read_shipping_address'),
    path('shipping/address/update/', UpdateShippingAddressView.as_view(), name='update_shipping_address'),
    path('shipping/address/delete/', DeleteShippingAddressView.as_view(), name='delete_shipping_address'),
    path('admin/make/staff/', AdminToggleStaffStatusView.as_view(), name='admin-make-staff'),
    path('view/notifications/', NotificationListView.as_view(), name='user-view-notifications'),
    path('admin/view/notifications/', AdminNotificationListView.as_view(), name='admin-view-notifications'),
    path('admin/send/shop/notifications/', AdminSendNotificationView.as_view(), name='admin-shop-notifications'),
]
