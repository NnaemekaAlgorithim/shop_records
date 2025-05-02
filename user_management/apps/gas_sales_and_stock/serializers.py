from rest_framework import serializers
from .models import GasStock, Sale

class GasStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = GasStock
        fields = ['total_kg']

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ['id', 'kg_sold', 'total_price', 'created_at']
