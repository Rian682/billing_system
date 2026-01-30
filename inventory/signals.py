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


@receiver(post_save, sender=Product)
def log_product_changes(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            product=instance,
            action=f"Product created with quantity {instance.quantity}",
            changed_by=None #We'll handle this in views
        )
    # If not created then it will change. so if it changes is the else statement
    else:
        old_values = _product_old_values.get(instance.pk, {})

        if old_values.get('purchase_price') != instance.purchase_price:
            AuditLog.objects.create(
                product=instance,
                action=f"Purchase price changed from ${old_values["purchanse_price"]} to ${instance.purchase_price}",
                changed_by=None
            )

        if old_values.get('selling_price') != instance.selling_price:
            AuditLog.objects.create(
                product=instance,
                action=f"Selling price changed from ${old_values['selling_price']} to ${instance.selling_price}",
                changed_by=None
            )
        
        if old_values.get('quantity') != instance.quantity:
            diff = instance.quantity - old_values['quantity']
            action = f"Stock {'increased' if diff > 0 else 'decreased'} by {abs(diff)} (from {old_values['quantity']} to {instance.quantity})"
            AuditLog.objects.create(
                product=instance,
                action=action,
                changed_by=None
            )
        
        # Clean up stored old values
        if instance.pk in _product_old_values:
            del _product_old_values[instance.pk]