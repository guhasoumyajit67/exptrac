from django.core.management.base import BaseCommand
from django.core import serializers
import json
from expenses.models import Item

class Command(BaseCommand):
    help = 'Export global items to JSON'

    def handle(self, *args, **options):
        # Get all global items (user=None)
        global_items = Item.objects.filter(user__isnull=True).select_related('category')
        
        # Serialize to JSON
        data = json.loads(serializers.serialize('json', global_items, indent=2))
        
        # Save to file
        with open('global_items.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Exported {len(data)} global items to global_items.json')
        )