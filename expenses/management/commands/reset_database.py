from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from expenses.models import Transaction, Item, Payer, Category
from django.db import connection

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset all data in Supabase database'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Resetting Supabase database...')
        
        try:
            # Delete all transactions
            tx_count = Transaction.objects.count()
            Transaction.objects.all().delete()
            self.stdout.write(f'✅ Deleted {tx_count} transactions')
            
            # Delete all items
            item_count = Item.objects.count()
            Item.objects.all().delete()
            self.stdout.write(f'✅ Deleted {item_count} items')
            
            # Delete all payers
            payer_count = Payer.objects.count()
            Payer.objects.all().delete()
            self.stdout.write(f'✅ Deleted {payer_count} payers')
            
            # Delete all categories
            cat_count = Category.objects.count()
            Category.objects.all().delete()
            self.stdout.write(f'✅ Deleted {cat_count} categories')
            
            # Delete all non-superuser accounts
            user_count = User.objects.exclude(is_superuser=True).count()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(f'✅ Deleted {user_count} regular users')
            
            self.stdout.write(self.style.SUCCESS('🎉 All data reset successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))