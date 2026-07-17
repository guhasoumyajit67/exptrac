from django.core.management.base import BaseCommand
from expenses.models import Item, Category
import json

class Command(BaseCommand):
    help = 'Load global items from JSON file'

    def handle(self, *args, **options):
        try:
            with open('global_items.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('❌ global_items.json not found!'))
            self.stdout.write('Run: python manage.py export_global_items first')
            return

        count_created = 0
        count_skipped = 0
        
        # Get category name mapping
        category_map = {cat.name: cat for cat in Category.objects.all()}
        category_id_map = {cat.id: cat for cat in Category.objects.all()}

        for item_data in data:
            item_name = item_data['fields']['name']
            unit = item_data['fields']['unit']
            category_id = item_data['fields']['category']

            # Find category by ID first, then by name
            category = category_id_map.get(category_id)
            if not category:
                # Try to find by name (fallback)
                for cat_name, cat_obj in category_map.items():
                    if cat_name.lower() in item_data.get('category_name', '').lower():
                        category = cat_obj
                        break

            if not category:
                self.stdout.write(self.style.WARNING(f'⚠️ Skipping {item_name}: Category not found'))
                count_skipped += 1
                continue

            # Check if item already exists
            exists = Item.objects.filter(user=None, name=item_name).exists()
            
            if not exists:
                Item.objects.create(
                    user=None,
                    name=item_name,
                    category=category,
                    unit=unit
                )
                count_created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {item_name}'))
            else:
                count_skipped += 1
                self.stdout.write(self.style.WARNING(f'⏭️ Skipped: {item_name} (already exists)'))

        self.stdout.write(
            self.style.SUCCESS(f'''
🎉 Loading complete!
   ✅ Created: {count_created} items
   ⏭️ Skipped: {count_skipped} items
            ''')
        )