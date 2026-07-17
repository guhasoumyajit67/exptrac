from django.core.management.base import BaseCommand
from django.core import serializers
import json
from expenses.models import Item

class Command(BaseCommand):
    help = 'Export global items to JSON with category names'

    def handle(self, *args, **options):
        # Get all global items (user=None)
        global_items = Item.objects.filter(user__isnull=True).select_related('category')
        
        # Build export data with category names
        export_data = []
        for item in global_items:
            export_data.append({
                'model': 'expenses.item',
                'pk': item.pk,
                'fields': {
                    'user': None,
                    'name': item.name,
                    'category_name': item.category.name,  # Use name instead of ID
                    'unit': item.unit
                }
            })
        
        # Save to file
        with open('global_items.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Exported {len(export_data)} global items with category names')
        )