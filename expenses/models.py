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
    # 🚨 Updated to show a dash for the blank option
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

    def __str__(self):
        return self.name




class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    
    # Solid database foreign key relation. Unit is tracked through this link dynamically.
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        # Traverses the foreign key to inspect the parent item's unit dynamically
        unit_str = self.item.unit if self.item.unit else ""
        qty_label = f" ({self.quantity} {unit_str})".strip() if self.quantity else ""
        
        # Clean spacing if qty_label ends up being empty
        qty_display = f" {qty_label}" if qty_label else ""
        return f"{self.date} - {self.item.name}{qty_display} [₹{self.price}] paid by {self.payer.name}"