from django.db import models

# Create your models here.
class Order(models.Model):
    invoice_id = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    payment_status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_id
    
    # Generates an unique invoice
    def save(self, *args, **kwargs):
        if not self.invoice_id:
            from datetime import datetime
            year = datetime.now().year  #Current year
        #Django uses the pattern 'field_name__lookup_type'. here '__startswith' is a lookup condition
        #Here Django is saying filter where invoice_id is like 'INV-2024'
            last_order = Order.objects.filter(invoice_id__startswith=f'INV-{year}').order_by('invoice_id').last()
            if last_order:
                last_num = int(last_order.invoice_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.invoice_id = f'INV-{year}-{new_num:04d}'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"