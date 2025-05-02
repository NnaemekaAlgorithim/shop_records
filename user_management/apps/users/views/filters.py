from user_management.apps.users.models import Users
from django_filters import rest_framework as filters


class UserFilter(filters.FilterSet):
    created_at = filters.DateFilter(field_name="date_joined", lookup_expr='exact')
    created_at__range = filters.DateFromToRangeFilter(field_name="date_joined")
    
    class Meta:
        model = Users
        fields = ['is_staff', 'is_superuser', 'is_active', 'created_at', 'created_at__range', 'blocked_user']
