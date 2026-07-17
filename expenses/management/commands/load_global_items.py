from django.core.management.base import BaseCommand
from expenses.models import Item, Category
import json

class Command(BaseCommand):
    help = 'Load global items from JSON file using category names'

    def handle(self, *args, **options):
        try:
            with open('global_items.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('❌ global_items.json not found!'))
            return

        # Create category name lookup
        category_lookup = {cat.name: cat for cat in Category.objects.all()}

        count_created = 0
        count_skipped = 0
        count_category_missing = 0

        for item_data in data:
            item_name = item_data['fields']['name']
            unit = item_data['fields']['unit']
            category_name = item_data['fields'].get('category_name')
            
            if not category_name:
                self.stdout.write(self.style.ERROR(f'❌ No category_name for: {item_name}'))
                count_skipped += 1
                continue

            # Find category by name
            category = category_lookup.get(category_name)
            
            if not category:
                self.stdout.write(self.style.WARNING(f'⚠️ Skipping {item_name}: Category "{category_name}" not found'))
                count_category_missing += 1
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
   ⚠️ Missing categories: {count_category_missing}
            ''')
        )