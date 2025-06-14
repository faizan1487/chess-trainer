from django.core.management.base import BaseCommand
from chess_app.models import Opening, OpeningLesson, LessonMove

class Command(BaseCommand):
    help = 'Populates the database with London System opening and variations'

    def handle(self, *args, **kwargs):
        # Create the main London System opening
        london_system, created = Opening.objects.get_or_create(
            name="London System",
            eco_code="D02",
            defaults={
                'description': (
                    "The London System is a solid and reliable opening system for White. "
                    "It begins with 1.d4 followed by Bf4, creating a strong pawn structure "
                    "and piece development. It's known for its simplicity and "
                    "effectiveness at all levels."
                ),
                'pgn_moves': "1. d4 d5 2. Bf4",
                'difficulty': 1,
                'is_popular': True,
                'for_white': True,
                'category': "Queen's Pawn Game"
            }
        )

        # Create variations
        variations = [
            {
                'name': "Classical London System",
                'eco_code': "D02",
                'pgn_moves': "1. d4 d5 2. Bf4 Nf6 3. e3 c5 4. c3 Nc6 5. Nd2",
                'description': (
                    "The main line of the London System, featuring solid development "
                    "and a strong pawn structure."
                ),
                'difficulty': 1,
                'is_popular': True,
                'for_white': True,
                'category': "Queen's Pawn Game"
            },
            {
                'name': "London System vs Kings Indian",
                'eco_code': "A48",
                'pgn_moves': "1. d4 Nf6 2. Bf4 g6 3. e3 Bg7 4. Nf3 O-O",
                'description': (
                    "A solid approach against the King's Indian Defense, maintaining "
                    "White's space advantage."
                ),
                'difficulty': 2,
                'is_popular': True,
                'for_white': True,
                'category': "Queen's Pawn Game"
            },
            {
                'name': "London System vs Dutch Defense",
                'eco_code': "A80",
                'pgn_moves': "1. d4 f5 2. Bf4 Nf6 3. e3 e6 4. Nf3",
                'description': (
                    "A reliable way to meet the Dutch Defense, keeping the position "
                    "solid and controlled."
                ),
                'difficulty': 2,
                'is_popular': True,
                'for_white': True,
                'category': "Queen's Pawn Game"
            },
            {
                'name': "London System vs Slav Defense",
                'eco_code': "D10",
                'pgn_moves': "1. d4 d5 2. Bf4 c6 3. e3 Nf6 4. Nf3",
                'description': (
                    "A solid approach against the Slav Defense, keeping the position "
                    "flexible and safe."
                ),
                'difficulty': 2,
                'is_popular': True,
                'for_white': True,
                'category': "Queen's Pawn Game"
            },
            {
                'name': "Chogirin Defense (London System)",
                'eco_code': "D02",
                'pgn_moves': "1. d4 d5 2. Bf4 Nc6 3. Nf3 Bg4 4. e3 e6 5. Nbd2 Nf6 6. c3 a6",
                'description': (
                    "The Chogirin Defense is a rare but interesting way for Black to meet the London System, involving early ...Nc6 and ...Bg4. It can lead to dynamic play and imbalanced pawn structures."
                ),
                'difficulty': 3,
                'is_popular': False,
                'for_white': True,
                'category': "Queen's Pawn Game"
            },
        ]

        # Create variations
        for var_data in variations:
            variation, created = Opening.objects.get_or_create(
                name=var_data['name'],
                defaults={
                    'eco_code': var_data['eco_code'],
                    'pgn_moves': var_data['pgn_moves'],
                    'description': var_data['description'],
                    'difficulty': var_data['difficulty'],
                    'is_popular': var_data['is_popular'],
                    'for_white': var_data['for_white'],
                    'category': var_data['category'],
                    'parent_opening': london_system
                }
            )

        # Create main lesson for London System
        main_lesson = OpeningLesson.objects.get_or_create(
            opening=london_system,
            name="London System - Basic Principles",
            description=(
                "Learn the fundamental ideas and plans in the London System, including "
                "piece development, pawn structure, and typical middlegame plans."
            ),
            difficulty=1,
            order=1
        )[0]

        # Create lesson moves
        lesson_moves = [
            {
                'move_number': 1,
                'move_uci': 'd2d4',
                'move_san': 'd4',
                'position_before': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                'position_after': 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
                'explanation': 'White establishes central control with the d-pawn.'
            },
            {
                'move_number': 2,
                'move_uci': 'c8f5',
                'move_san': 'Bf4',
                'position_before': 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
                'position_after': 'rnbqkbnr/pppppppp/8/8/3P1B2/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
                'explanation': (
                    'The key move of the London System. The bishop develops to f4, '
                    'supporting the center and preparing for kingside castling.'
                )
            }
        ]

        for move_data in lesson_moves:
            LessonMove.objects.get_or_create(
                lesson=main_lesson,
                move_number=move_data['move_number'],
                defaults={
                    'move_uci': move_data['move_uci'],
                    'move_san': move_data['move_san'],
                    'position_before': move_data['position_before'],
                    'position_after': move_data['position_after'],
                    'explanation': move_data['explanation']
                }
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated London System and variations')
        ) 