from django.contrib import admin
from .models import (
    Category,
    Item,
    Payer,
    Transaction,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    ordering = ('name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit')
    list_filter = ('category',)
    ordering = ('name',)
    search_fields = ('name',)

    def get_queryset(self, request):
        """
        Superusers see the global records + their own custom items.
        Normal staff users only see their own custom items.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(user__isnull=True) | qs.filter(user=request.user)
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.user is None:
            return request.user.is_superuser
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.user is None:
            return request.user.is_superuser
        return super().has_delete_permission(request, obj)


@admin.register(Payer)
class PayerAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]  # Kept concise
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user=request.user)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "item",
        'price',
        'quantity',
        "payer",
        'comment',
    ]
    list_filter = [
        "date",
        "payer",
        "item__category",
    ]
    date_hierarchy = "date"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user=request.user)