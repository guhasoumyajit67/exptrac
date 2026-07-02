from django.contrib import admin
from django.db import models
from django.forms import widgets
from .models import (
    Category,
    Item,
    Payer,
    Transaction,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=[
        "name",
        "color",
    ]

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "user",
    ]
    list_filter = [
        "category",
        "user",
    ]

@admin.register(Payer)
class PayerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "color",
    ]
    list_filter = [
        "user",
    ]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "item",
        'price',
        'quantity',
        'unit',
        "payer",
        'comment',
    ]
    list_filer = [
        "date",
        "payer",
    ]
    date_hierarchy = "date"