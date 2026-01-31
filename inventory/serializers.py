from rest_framework import serializers
from .models import Product, AuditLog

class ProductSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()
    profit_margin = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'purchase_price', 
                  'selling_price', 'quantity', 'min_stock_level', 
                  'is_active', 'created_at', 'is_low_stock', 'profit_margin']

        read_only_fields = ['id', 'created_at']
    
    def get_is_low_stock(self, obj):
        return obj.quantity < obj.min_stock_level
    
    def get_profit_margin(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'role') and request.user.role == 'manager':
            return float(obj.selling_price - obj.purchase_price)
        return None


class ProductListSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'selling_price', 'quantity', 'is_low_stock', 'is_active']
    
    def get_is_low_stock(self, obj):
        return obj.quantity < obj.min_stock_level


class AuditLogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'product', 'product_name', 'action', 'changed_by', 'changed_by_username', 'created_at']
        read_only_fields = ['id', 'created_at']