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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

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
    UNIT_CHOICES = [
        ('kg', 'Kg'),
        ('ltr', 'Ltr'),
        ('pcs', 'Pcs'),
        ('pkt', 'Pkt'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, blank=True, null=True)
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        qty_label = f" ({self.quantity} {self.unit})" if self.quantity else ""
        return f"{self.date} - {self.item.name}{qty_label} [₹{self.price}] paid by {self.payer.name}"