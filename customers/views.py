from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer
from .serializers import CustomerListSerializer, CustomerSerializer
from inventory.permissions import IsStaffOrManager

# Create your views here.
class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrManager]
    queryset = Customer.objects.filter(is_active=True).order_by('-created_at')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email']

    def get_serializer_class(self):
        #For list of customers (light)
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer
    
    def destroy(self, request, *args, **kwargs):
        #The soft delete (making the customers deactivate)
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"message": "Customer deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

