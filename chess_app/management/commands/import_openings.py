import json
import os
from django.core.management.base import BaseCommand, CommandError
from chess_app.models import Opening

class Command(BaseCommand):
    help = 'Imports chess openings from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='default',
            help='Source file path (use "default" for built-in data)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing openings before import',
        )

    def handle(self, *args, **options):
        source = options['source']
        clear = options['clear']
        
        if clear:
            if input("Are you sure you want to clear all existing openings? (y/n): ").lower() == 'y':
                Opening.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('All existing openings cleared.'))
            else:
                self.stdout.write(self.style.WARNING('Clear operation cancelled.'))
        
        # Load opening data
        if source == 'default':
            # Use built-in data file
            data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    'data', 'chess_openings.json')
            self.stdout.write(f"Using default data file at: {data_path}")
        else:
            # Use user-specified file
            data_path = source
            if not os.path.exists(data_path):
                raise CommandError(f"File not found: {data_path}")
        
        try:
            with open(data_path, 'r') as f:
                openings_data = json.load(f)
        except json.JSONDecodeError:
            raise CommandError(f"Invalid JSON format in {data_path}")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")
        
        self.stdout.write(f"Found {len(openings_data)} openings in file")
        
        # First pass - create all openings without parent references
        created_openings = {}
        parent_relationships = {}
        
        for idx, opening_data in enumerate(openings_data):
            # Store parent relationship if specified
            if 'parent_opening' in opening_data:
                parent_name = opening_data['parent_opening']
                parent_relationships[opening_data['name']] = parent_name
                # Remove parent_opening key for now to prevent errors
                opening_data = {k: v for k, v in opening_data.items() if k != 'parent_opening'}
            
            # Create or update opening
            opening, created = Opening.objects.update_or_create(
                name=opening_data['name'],
                defaults=opening_data
            )
            
            created_openings[opening.name] = opening
            
            if (idx + 1) % 5 == 0 or idx + 1 == len(openings_data):
                self.stdout.write(f"Processed {idx + 1}/{len(openings_data)} openings")
        
        # Second pass - update parent references
        for child_name, parent_name in parent_relationships.items():
            if parent_name in created_openings:
                child = created_openings[child_name]
                parent = created_openings[parent_name]
                child.parent_opening = parent
                child.save()
                self.stdout.write(f"Set parent '{parent_name}' for '{child_name}'")
            else:
                self.stdout.write(
                    self.style.WARNING(f"Parent opening '{parent_name}' not found for '{child_name}'")
                )
        
        total_count = Opening.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(openings_data)} openings. "
                f"Database now contains {total_count} openings."
            )
        ) 