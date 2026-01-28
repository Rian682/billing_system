from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product, AuditLog

# Store old values before save
_product_old_values = {}


# This will run before Product is saved
# We save old values of the product here to compare later.
@receiver(pre_save, sender=Product)
def track_product_changes(sender, instance, created, **kwargs):
    if instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            _product_old_values[instance.pk] = {
                'purchase_price': old_product.purchase_price,
                'selling_price': old_product.selling_price,
                'quantity': old_product.quantity,
            }
        except Product.DoesNotExist:
            pass

