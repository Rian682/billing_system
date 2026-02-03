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
    queryset = Product.objects.order_by('-created_at')
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
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(is_active=True))
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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

    #Get all the deleted products list
    @action(detail=False, methods=['get'], permission_classes=[IsManager], url_path='deleted')
    def deleted_products(self, request):
        deleted = Product.objects.filter(is_active=False).order_by('-created_at')
        serializer = self.get_serializer(deleted, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManager], url_path='restore')
    def restore_product(self, request, pk=None):
        product = self.get_object()

        if product.is_active:
            return Response(
                {"error": "Product is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.is_active = True
        product.save()

        AuditLog.objects.create(
            product=product,
            action="Product restored from deleted state",
            changed_by=request.user
        )
        return Response(
            {"message": f"Product {product.name} restored successfully"},
            status=status.HTTP_200_OK
        )

    
    
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

