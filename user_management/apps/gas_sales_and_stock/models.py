from django.db import models
from user_management.apps.base.models import BaseModel


class SingletonModel(models.Model):
    """
    Abstract base model to enforce singleton behavior.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1  # Ensure only one instance exists
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """
        Get the single instance of this model, creating it if it doesn't exist.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# Singleton GasStock model
class GasStock(BaseModel):
    total_kg = models.FloatField(default=0)  # Tracks the total stock in kilograms

    @staticmethod
    def get_instance():
        """
        Ensures there is only one instance of GasStock in the database.
        Creates a new instance if none exists.
        """
        obj, created = GasStock.objects.get_or_create()  # No specific `id` needed
        return obj

    def add_stock(self, kilograms):
        """
        Add stock to total_kg.
        :param kilograms: Number of kilograms added to the stock.
        """
        self.total_kg += kilograms
        self.save()

    def sell_stock(self, kilograms):
        """
        Deduct stock from total_kg based on the kilograms sold.
        :param kilograms: Number of kilograms sold.
        """
        if kilograms > self.total_kg:
            raise ValueError("Not enough stock available to complete this sale.")
        self.total_kg -= kilograms
        self.save()

    def __str__(self):
        return f"Gas Stock: {self.total_kg} kg"


class Price(SingletonModel):
    price_per_kg = models.FloatField(default=100)  # Default price per kg

    def __str__(self):
        return f"Price per kg: {self.price_per_kg}"


class Sale(BaseModel):
    kg_sold = models.FloatField()  # Kilograms sold
    total_price = models.FloatField()  # Auto-calculated during save

    def save(self, *args, **kwargs):
        # Fetch the current price from the singleton
        price_instance = Price.get_instance()
        current_price_per_kg = price_instance.price_per_kg

        # Calculate total price
        self.total_price = self.kg_sold * current_price_per_kg
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.kg_sold} kg sold for {self.total_price}"
