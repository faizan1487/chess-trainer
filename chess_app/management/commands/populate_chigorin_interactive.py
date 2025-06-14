from django.core.management.base import BaseCommand
from chess_app.models import Opening, OpeningLesson, LessonMove

class Command(BaseCommand):
    help = 'Populates an interactive Chigorin Defense lesson for beginners.'

    def handle(self, *args, **kwargs):
        # Add Chigorin Defense as a root opening
        chigorin, _ = Opening.objects.get_or_create(
            name="Chigorin Defense",
            eco_code="D07",
            defaults={
                'description': (
                    "The Chigorin Defense (1.d4 d5 2.Nf3 Nc6) is a dynamic response to 1.d4. "
                    "Black develops the queen's knight early to challenge the center with pieces rather than pawns. "
                    "This opening leads to active play and can catch unprepared opponents off guard."
                ),
                'pgn_moves': "1. d4 d5 2. Nf3 Nc6",
                'difficulty': 2,
                'is_popular': False,
                'for_white': False,
                'category': "Queen's Pawn Game"
            }
        )

        # Create lesson for Chigorin Defense
        lesson, _ = OpeningLesson.objects.get_or_create(
            opening=chigorin,
            name="Chigorin Defense: Introduction & Key Lines (Interactive)",
            description=(
                "In this lesson, you will learn the most common opening for players under 1500 blitz rating. "
                "The Chigorin Defense is a popular choice, and in this lesson, we'll break down key lines for both situations: "
                "when Black plays ...Nf6 early and when Black delays ...Nf6.\n\n"
                "Learning Objectives:\n"
                "- Understand how Black challenges the center with pieces rather than pawns.\n"
                "- Recognize common traps and pitfalls for both sides.\n"
                "- Identify strategic ideas behind delaying or playing ...Nf6.\n\n"
                "Summary: The Chigorin Defense is an active, piece-based approach for Black. "
                "It can lead to dynamic play and offers practical chances for both sides. Practice these lines and review model games to deepen your understanding!"
            ),
            difficulty=1,
            order=1
        )

        # Interactive lesson steps (White's move prompted, Black's move automatic)
        steps = [
            {
                'move_number': 1,
                'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                'prompt': 'What should White play first?',
                'correct_move': 'd4',
                'black_reply': 'd5',
                'explanation': 'White controls the center with the pawn, preparing to develop pieces.',
                'quiz_choices': ['d4', 'e4', 'Nf3'],
                'quiz_feedback': {
                    'd4': 'Correct! This is the best way to start.',
                    'e4': 'Not quite. e4 is good, but for the Chigorin, start with d4.',
                    'Nf3': 'Not quite. Nf3 is good, but d4 is the main move here.'
                }
            },
            {
                'move_number': 2,
                'fen': 'rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2',
                'prompt': 'What should White play next?',
                'correct_move': 'Nf3',
                'black_reply': 'Nf6',
                'explanation': 'White develops a knight to support the center and prepares for kingside castling.',
                'quiz_choices': ['Nf3', 'Nc3', 'e3'],
                'quiz_feedback': {
                    'Nf3': 'Correct! This move develops and supports the center.',
                    'Nc3': 'Not quite. Nc3 is playable, but Nf3 is more flexible here.',
                    'e3': 'Not quite. e3 is solid, but Nf3 develops a piece and supports d4.'
                }
            },
            {
                'move_number': 3,
                'fen': 'rnbqkb1r/ppp1pppp/5n2/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 2 3',
                'prompt': 'What should White play now?',
                'correct_move': 'Bf4',
                'black_reply': 'Nc6',
                'explanation': 'White develops the bishop, eyeing the central e5 square and exerting pressure on the queenside.',
                'quiz_choices': ['Bf4', 'e3', 'Nc3'],
                'quiz_feedback': {
                    'Bf4': 'Correct! This is the main line and puts pressure on Black.',
                    'e3': 'Not quite. e3 is solid, but Bf4 develops the bishop more actively.',
                    'Nc3': 'Not quite. Nc3 is playable, but Bf4 is more active.'
                }
            },
            {
                'move_number': 4,
                'fen': 'r1bqkb1r/ppp1pppp/2n2n2/3p4/3P1B2/5N2/PPP1PPPP/RN1QKB1R w KQkq - 3 4',
                'prompt': 'What should White play?',
                'correct_move': 'e3',
                'black_reply': 'Bf5',
                'explanation': 'White prepares to solidify the center with the e3 pawn. Black develops the bishop outside the pawn chain, putting pressure on the center.',
                'quiz_choices': ['e3', 'Nc3', 'c4'],
                'quiz_feedback': {
                    'e3': 'Correct! This move supports the center and opens lines for the bishop.',
                    'Nc3': 'Not quite. Nc3 is playable, but e3 is more flexible here.',
                    'c4': 'Not quite. c4 is possible, but e3 is more solid.'
                }
            },
        ]

        for step in steps:
            LessonMove.objects.get_or_create(
                lesson=lesson,
                move_number=step['move_number'],
                defaults={
                    'move_uci': '',  # Not used for interactive quiz
                    'move_san': step['correct_move'],
                    'position_before': step['fen'],
                    'position_after': '',  # Can be filled in by frontend logic
                    'explanation': step['explanation'],
                    'quiz_choices': step['quiz_choices'],
                    'quiz_feedback': step['quiz_feedback'],
                    'prompt': step['prompt'],
                    'black_reply': step['black_reply'],
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated interactive Chigorin Defense lesson.')) 