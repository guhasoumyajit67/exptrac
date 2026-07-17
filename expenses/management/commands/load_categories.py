from django.core.management.base import BaseCommand
from expenses.models import Category

class Command(BaseCommand):
    help = 'Load global categories into the database'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Cereals & Products', 'color': '#B45309'},      # Warm Brown
            {'name': 'Clothing', 'color': '#4F46E5'},                # Indigo
            {'name': 'Education', 'color': '#0284C7'},               # Sky Blue
            {'name': 'Eggs', 'color': '#FCD34D'},                     # Golden Yellow
            {'name': 'Footwear', 'color': '#6D28D9'},                # Purple
            {'name': 'Fruits', 'color': '#E11D48'},                  # Rose/Red
            {'name': 'Fuel & Light', 'color': '#EA580C'},            # Orange
            {'name': 'Health', 'color': '#059669'},                  # Emerald Green
            {'name': 'Household Goods & Services', 'color': '#0F766E'}, # Teal
            {'name': 'Housing', 'color': '#8B5CF6'},                 # Violet
            {'name': 'Meat & Fish', 'color': '#991B1B'},             # Deep Red
            {'name': 'Milk & Products', 'color': '#7C3AED'},         # Royal Purple
            {'name': 'Non-Alcoholic Beverages', 'color': '#0891B2'}, # Cyan
            {'name': 'Oils & Fats', 'color': '#F59E0B'},             # Amber
            {'name': 'Pan, Tobacco & intoxicants', 'color': '#92400E'}, # Dark Brown
            {'name': 'Personal Care & Effects', 'color': '#D946EF'}, # Pink/Magenta
            {'name': 'Prepared Meals, Snacks, Sweets etc.', 'color': '#F43F5E'}, # Bright Rose
            {'name': 'Pulses & Products', 'color': '#84CC16'},       # Lime Green
            {'name': 'Recreation & Amusement', 'color': '#06B6D4'},  # Bright Cyan
            {'name': 'Spices', 'color': '#D97706'},                  # Dark Golden
            {'name': 'Sugar & Confectionery', 'color': '#EC4899'},   # Hot Pink
            {'name': 'Transport & Communication', 'color': '#2563EB'}, # Royal Blue
            {'name': 'Vegetables', 'color': '#22C55E'},              # Bright Green
        ]

        count = 0
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'color': cat_data['color']}
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⏭️ Category already exists: {category.name}'))

        self.stdout.write(
            self.style.SUCCESS(f'🎉 Successfully loaded {count} new categories!')
        )