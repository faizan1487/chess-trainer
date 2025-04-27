from django.core.management.base import BaseCommand
from chess_app.models import Opening

class Command(BaseCommand):
    help = 'Loads sample chess openings data'

    def handle(self, *args, **kwargs):
        openings = [
            {
                'name': 'Ruy Lopez (Spanish Opening)',
                'eco_code': 'C60-C99',
                'pgn_moves': '1. e4 e5 2. Nf3 Nc6 3. Bb5',
                'description': 'One of the oldest and most classic chess openings. The Ruy Lopez aims to pressure Black\'s e5 pawn while developing pieces toward castling. White places the bishop on b5 to attack the knight that defends the e5 pawn.',
                'difficulty': 3,
            },
            {
                'name': 'Sicilian Defense',
                'eco_code': 'B20-B99',
                'pgn_moves': '1. e4 c5',
                'description': 'The most popular response to White\'s e4. Black immediately fights for the center in an asymmetrical way, leading to complex and dynamic positions with rich strategic and tactical possibilities.',
                'difficulty': 4,
            },
            {
                'name': 'Queen\'s Gambit',
                'eco_code': 'D06-D69',
                'pgn_moves': '1. d4 d5 2. c4',
                'description': 'A fundamental opening for d4 players. White offers a pawn to divert Black\'s d-pawn and gain central control. This opening typically leads to positional struggles with solid pawn structures.',
                'difficulty': 3,
            },
            {
                'name': 'Italian Game',
                'eco_code': 'C50-C59',
                'pgn_moves': '1. e4 e5 2. Nf3 Nc6 3. Bc4',
                'description': 'A classic opening that aims for quick development and targets the f7 square. Solid and straightforward, it offers easier learning for beginners but contains plenty of tactical depth.',
                'difficulty': 2,
            },
            {
                'name': 'French Defense',
                'eco_code': 'C00-C19',
                'pgn_moves': '1. e4 e6',
                'description': 'A solid choice for Black where they prepare to challenge White\'s center with d5. The French Defense often leads to closed positions with distinctive pawn chains and piece maneuvers.',
                'difficulty': 3,
            },
            {
                'name': 'King\'s Indian Defense',
                'eco_code': 'E60-E99',
                'pgn_moves': '1. d4 Nf6 2. c4 g6',
                'description': 'A hypermodern opening where Black allows White to build a center only to challenge it later with piece pressure and timely pawn breaks. Known for its complex and double-edged positions.',
                'difficulty': 5,
            },
            {
                'name': 'Scandinavian Defense',
                'eco_code': 'B01',
                'pgn_moves': '1. e4 d5',
                'description': 'A direct challenge to White\'s e4 pawn. Black immediately counters in the center, often leading to early queen development after exchanges. Straightforward to learn but with many strategic subtleties.',
                'difficulty': 1,
            },
            {
                'name': 'English Opening',
                'eco_code': 'A10-A39',
                'pgn_moves': '1. c4',
                'description': 'A flexible flank opening that often transposes to other openings. White controls the d5 square and can develop in various ways, making it a versatile choice against different Black setups.',
                'difficulty': 4,
            },
        ]

        # Create openings if they don't exist
        created_count = 0
        for opening_data in openings:
            opening, created = Opening.objects.get_or_create(
                name=opening_data['name'],
                defaults={
                    'eco_code': opening_data['eco_code'],
                    'pgn_moves': opening_data['pgn_moves'],
                    'description': opening_data['description'],
                    'difficulty': opening_data['difficulty'],
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {created_count} new openings (total: {Opening.objects.count()})')) 