from rest_framework import serializers
from .models import Order, OrderItem
from inventory.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']
        read_only_fields = ['id', 'price']  # Price set automatically from product


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Nested serializer for multiple products
    
    class Meta:
        model = Order
        fields = ['customer', 'payment_status', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')  # Extract nested items
        
        # Create order
        order = Order.objects.create(
            customer=validated_data['customer'],
            payment_status=validated_data['payment_status'],
            created_by=self.context['request'].user  # Get user from request
        )
        
        total = 0
        
        # Create order items and update inventory
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Check stock availability
            if product.quantity < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.quantity}"
                )
            
            # Create order item with current selling price
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.selling_price  # Lock in current price
            )
            
            # Decrease inventory
            product.quantity -= quantity
            product.save()
            
            # Calculate total
            total += order_item.price * order_item.quantity
        
        # Update order total
        order.total_amount = total
        order.save()
        
        return order


class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'invoice_id', 'customer', 'customer_name', 
            'customer_phone', 'payment_status', 'total_amount', 
            'items_count', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    profit = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'invoice_id', 'customer', 'payment_status', 
            'total_amount', 'items', 'created_by', 'created_by_username',
            'created_at', 'profit'
        ]
    
    def get_customer(self, obj):
        return {
            'id': obj.customer.id,
            'name': obj.customer.name,
            'phone': obj.customer.phone,
            'email': obj.customer.email
        }
    
    def get_profit(self, obj):
        """Calculate total profit - only for managers"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'role') and request.user.role == 'manager':
            profit = 0
            for item in obj.items.all():
                profit += (item.price - item.product.purchase_price) * item.quantity
            return float(profit)
        return None