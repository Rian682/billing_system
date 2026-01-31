from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from .models import Product, AuditLog
from .serializers import ProductSerializer, ProductListSerializer, AuditLogSerializer
from .permissions import IsStaffOrManager, IsManager, ManagerCanEditDeleteOnly 

# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ManagerCanEditDeleteOnly]
    queryset = Product.objects.filter(is_active=True).order_by('-created_at')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_serializer_class(self):
        if self.request.user.role == 'staff':
            return ProductListSerializer
        return ProductSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"message": "Product deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.filter(
            product=instance,
            changed_by=None
        ).update(changed_by=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.filter(
            product=instance,
            changed_by=None
        ).update(changed_by=self.request.user)
    
    
    @action(detail=False, methods=['get'], permission_classes=[IsStaffOrManager])
    def low_stock(self, request):
        low_stock_products = Product.objects.filter(
            is_active=True,
            quantity__lt=F('min_stock_level')
        )
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsManager]
    queryset = AuditLog.objects.all().order_by('-created_at')
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product']
    search_fields = ['action', 'product__name']

