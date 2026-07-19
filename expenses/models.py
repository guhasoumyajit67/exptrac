from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#FFFFFF", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    

class Item(models.Model):
    UNIT_CHOICES = [
        ('', '-'),
        ('Kg', 'Kg'),
        ('Pcs', 'Pcs'),
        ('Pkt', 'Pkt'),
        ('Ltr', 'Ltr'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    unit = models.CharField(
        max_length=5, 
        choices=UNIT_CHOICES, 
        default='', 
        blank=True
    )

    class Meta:
        unique_together = ("user", "name")
        indexes = [
            models.Index(fields=['user', 'name']),      # For item lookups by user
            models.Index(fields=['category']),          # For category filtering
        ]
    
    def __str__(self):
        if self.user is None:
            return f"{self.name} (Global)"
        return f"{self.name} (Custom)"
    
    

class Payer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#FFFFFF", blank=True, null=True)

    class Meta:
        unique_together = ("user", "name")
        indexes = [
            models.Index(fields=['user', 'name']),      # For payer lookups by user
        ]

    def __str__(self):
        return self.name




class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),      # For dashboard/analytics queries
            models.Index(fields=['user', 'item']),      # For item-based filtering
            models.Index(fields=['user', 'payer']),     # For payer-based filtering
        ]

    def __str__(self):
        # Get the unit from the item, default to empty string
        unit_str = self.item.unit if self.item.unit else ""
        
        # Build the quantity display
        if self.quantity is not None:
            if unit_str:
                qty_display = f" ({self.quantity} {unit_str})"
            else:
                qty_display = f" ({self.quantity})"
        else:
            qty_display = ""
        
        # Format price with 2 decimal places
        formatted_price = f"{self.price:.2f}"
        
        return f"{self.date} - {self.item.name}{qty_display} [₹{formatted_price}] paid by {self.payer.name}"
    
    

class StagingTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    row_idx = models.IntegerField()
    date = models.CharField(max_length=20)
    item_name = models.CharField(max_length=255, blank=True)
    item_id = models.IntegerField(null=True, blank=True)
    price = models.FloatField(default=0.0)
    quantity = models.FloatField(null=True, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    payer_id = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    error = models.CharField(max_length=255, blank=True)