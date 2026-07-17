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
            return

        count_created = 0
        count_skipped = 0
        count_category_missing = 0
        
        # Get all categories for lookup
        categories = Category.objects.all()
        category_lookup = {cat.id: cat for cat in categories}
        category_name_lookup = {cat.name.lower(): cat for cat in categories}

        for item_data in data:
            item_name = item_data['fields']['name']
            unit = item_data['fields']['unit']
            category_id = item_data['fields']['category']
            
            # Find category by ID or name
            category = category_lookup.get(category_id)
            
            if not category:
                # Try to find by name (if we have category names in the data)
                # For now, check if the category exists by ID
                if not category_lookup:
                    # First run - collect all category IDs that exist
                    category = None
            
            if not category:
                # Try to find by category name from the item name mapping
                # You may need to manually map if categories don't exist
                self.stdout.write(self.style.WARNING(f'⚠️ Skipping {item_name}: Category not found (ID: {category_id})'))
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
        
        if count_category_missing > 0:
            self.stdout.write(
                self.style.ERROR(f'''
⚠️ {count_category_missing} items were skipped due to missing categories.
Please run: python manage.py load_categories to fix this.
Then re-run: python manage.py load_global_items
''')
            )