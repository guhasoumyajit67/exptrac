from django.core.management.base import BaseCommand
from django.core import management
from datetime import datetime
from pathlib import Path

class Command(BaseCommand):
    help = 'Backup database using Django dumpdata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: ~/exptrac_backups/backup_TIMESTAMP.json)'
        )

    def handle(self, *args, **options):
        backup_root = Path.home() / 'exptrac_backups'
        backup_root.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if options.get('output'):
            backup_file = Path(options['output'])
        else:
            backup_file = backup_root / f"backup_{timestamp}.json"
        
        self.stdout.write(f'📦 Creating backup at {backup_file}...')
        
        with open(backup_file, 'w') as f:
            management.call_command(
                'dumpdata',
                'expenses',
                'accounts',
                exclude=[
                    'auth.permission',
                    'contenttypes',
                    'admin.logentry',
                    'sessions.session'
                ],
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=f
            )
        
        size = backup_file.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'🎉 Backup created!\n'
            f'📁 Location: {backup_file}\n'
            f'📊 Size: {size:.2f} MB'
        ))