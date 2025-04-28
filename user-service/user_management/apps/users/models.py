import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
import datetime
import secrets
from django.utils import timezone 
from user_management.apps.base.models import BaseModel
from cloudinary.models import CloudinaryField
from pytz import all_timezones


class Users(AbstractUser, BaseModel):
    """
    Custom user model extending AbstractUser and BaseModel.
    """

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    referral_code = models.CharField(max_length=50, null=True, blank=True, unique=True)
    referred_by = models.CharField(max_length=50, null=True, blank=True)
    profile_photo = CloudinaryField(null=True, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    activation_code = models.CharField(max_length=6, null=True, blank=True)
    activation_code_expiry = models.DateTimeField(null=True, blank=True)
    blocked_user = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="owneet_users_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="owneet_users_permissions",
        related_query_name="user",
    )

    def save(self, *args, **kwargs):
        """
        Generate a unique referral code if not already set.
        """
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def generate_activation_code(self):
        self.activation_code = secrets.token_hex(3).upper() # Generates a 6 character code.
        self.activation_code_expiry = timezone.now() + datetime.timedelta(minutes=5)
        self.save()

    def is_activation_code_valid(self, code):
        if self.activation_code == code and timezone.now() < self.activation_code_expiry:
            return True
        return False

    def block_user(self):
        self.blocked_user = True
        self.save()

    def unblock_user(self):
        self.blocked_user = False
        self.save()

    def __str__(self):
        """
        Return the username as the string representation.
        """
        return self.username


class ShippingAddress(BaseModel):
    """
    Model representing a user's shipping address.
    """

    TIMEZONE_CHOICES = [(tz, tz) for tz in all_timezones]

    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    postal_code = models.IntegerField()
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default='UTC')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )

    def __str__(self):
        """
        Return a formatted string representation of the shipping address.
        """
        return f"{self.street}, {self.city}, {self.state}, {self.country} - {self.postal_code} (Timezone: {self.timezone})"


class Notification(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
