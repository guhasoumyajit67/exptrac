from django.core.management.base import BaseCommand
from django.core import management
from pathlib import Path

class Command(BaseCommand):
    help = 'Restore database using Django loaddata'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to backup file (JSON)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            self.stdout.write(self.style.ERROR(f'❌ Backup file {backup_file} not found!'))
            return
        
        size = backup_file.stat().st_size / (1024 * 1024)
        
        if not options.get('force'):
            self.stdout.write(self.style.WARNING('⚠️  WARNING: This will OVERWRITE existing data!'))
            self.stdout.write(f'📁 Backup: {backup_file}')
            self.stdout.write(f'📊 Size: {size:.2f} MB')
            confirm = input('Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('❌ Operation cancelled.'))
                return
        
        self.stdout.write('📥 Restoring data from backup...')
        
        try:
            management.call_command('loaddata', str(backup_file))
            self.stdout.write(self.style.SUCCESS('🎉 Data restored successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))