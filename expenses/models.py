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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.item.name} (₹{self.amount}) paid by {self.payer.name}"