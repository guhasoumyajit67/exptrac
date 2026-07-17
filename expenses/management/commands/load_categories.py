from django.core.management.base import BaseCommand
from expenses.models import Category

class Command(BaseCommand):
    help = 'Load global categories into the database'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Cereals & Products', 'color': '#B45309'},
            {'name': 'Clothing', 'color': '#4F46E5'},
            {'name': 'Education', 'color': '#0284C7'},
            {'name': 'Eggs', 'color': '#D97706'},
            {'name': 'Footwear', 'color': '#6D28D9'},
            {'name': 'Fruits', 'color': '#E11D48'},
            {'name': 'Fuel & Light', 'color': '#EA580C'},
            {'name': 'Health', 'color': '#059669'},
            {'name': 'Household Goods & Services', 'color': '#0F766E'},
            {'name': 'Meat & Fish', 'color': '#991B1B'},
            {'name': 'Milk & Products', 'color': '#7C3AED'},
            {'name': 'Non-Alcoholic Beverages', 'color': '#0891B2'},
            {'name': 'Personal Care & Effects', 'color': '#D946EF'},
            {'name': 'Transport & Communication', 'color': '#2563EB'},
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