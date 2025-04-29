import ulid
from django.db import models


def generate_ulid_as_string():
    return str(ulid.new())


class BaseModel(models.Model):
    """
    Abstract base model with common fields and user tracking.
    """

    id = models.CharField(
        primary_key=True, default=generate_ulid_as_string, editable=False, max_length=26
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track user information generically
    created_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Identifier of the user who created the record",
    )
    updated_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Identifier of the user who last updated the record",
    )

    class Meta:
        abstract = True
