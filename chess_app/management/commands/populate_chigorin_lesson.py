from django.core.management.base import BaseCommand
from chess_app.models import Opening, OpeningLesson, LessonMove
import chess


class Command(BaseCommand):
    help = 'Populates the Chigorin Defense opening and an interactive lesson.'

    def handle(self, *args, **kwargs):
        # Try to find the London System opening to set as parent
        try:
            london = Opening.objects.get(name="London System")
        except Opening.DoesNotExist:
            london = None

        # Add Chigorin Defense as a variation of London System if possible
        chigorin, _ = Opening.objects.get_or_create(
            name="Chigorin Defense",
            eco_code="D07",
            defaults={
                'description': (
                    "The Chigorin Defense (1.d4 d5 2.Nf3 Nc6) is a dynamic response to "
                    "1.d4. Black develops the queen's knight early to challenge the "
                    "center with pieces rather than pawns. This opening leads to "
                    "active play and can catch unprepared opponents off guard."
                ),
                'pgn_moves': "1. d4 d5 2. Nf3 Nc6",
                'difficulty': 2,
                'is_popular': False,
                'for_white': False,
                'category': "Queen's Pawn Game",
                'parent_opening': london
            }
        )
        # If Chigorin already exists but has no parent, set it
        if london and chigorin.parent_opening != london:
            chigorin.parent_opening = london
            chigorin.save()

        # Create lesson for Chigorin Defense
        lesson, _ = OpeningLesson.objects.get_or_create(
            opening=chigorin,
            name="Chigorin Defense: Introduction & Key Lines",
            description=(
                "Learn the fundamentals of the Chigorin Defense, including main "
                "ideas, common plans, and key variations. This lesson is designed "
                "for players rated below 1500 and will guide you move-by-move with "
                "explanations.\n\n"
                "Learning Objectives:\n"
                "- Understand how Black challenges the center with pieces rather "
                "than pawns.\n"
                "- Recognize common traps and pitfalls for both sides.\n"
                "- Identify strategic ideas behind delaying or playing ...Nf6.\n\n"
                "Summary: The Chigorin Defense is an active, piece-based approach "
                "for Black. It can lead to dynamic play and offers practical "
                "chances for both sides. Practice these lines and review model "
                "games to deepen your understanding!"
            ),
            difficulty=1,
            order=1
        )

        # Main line moves and explanations
        moves = [
            {'move_san': 'd4',
             'explanation': (
                 'White claims the center with the d-pawn, a classical and solid start.'
             )},
            {'move_san': 'd5',
             'explanation': (
                 'Black immediately contests the center, leading to symmetrical pawn '
                 'structure.'
             )},
            {'move_san': 'Nf3',
             'explanation': (
                 'White develops the kingside knight, supporting d4 and preparing to '
                 'castle.'
             )},
            {'move_san': 'Nc6',
             'explanation': (
                 "Black plays Nc6, the hallmark of the Chigorin Defense. Instead of the "
                 "usual ...Nf6, Black develops the queen's knight early to challenge the "
                 "center and keep options open. This can lead to active piece play and "
                 "unbalanced positions."
             )},
            {'move_san': 'c4',
             'explanation': (
                 'White grabs more space in the center. Black can now consider ...Bg4, '
                 '...Nf6, or ...e6.'
             )},
            {'move_san': 'Bg4',
             'explanation': (
                 'Black pins the knight on f3, increasing pressure on d4 and preparing to '
                 'develop the kingside.'
             )},
            {'move_san': 'Nc3',
             'explanation': (
                 'White develops another piece, defending d4 and preparing to support the '
                 'center.'
             )},
            {'move_san': 'e6',
             'explanation': (
                 'Black supports the d5 pawn and prepares to develop the kingside pieces.'
             )},
        ]

        board = chess.Board()
        for idx, move in enumerate(moves):
            move_number = idx + 1
            position_before = board.fen()
            move_obj = board.parse_san(move['move_san'])
            move_uci = move_obj.uci()
            board.push(move_obj)
            position_after = board.fen()
            LessonMove.objects.get_or_create(
                lesson=lesson,
                move_number=move_number,
                defaults={
                    'move_uci': move_uci,
                    'move_san': move['move_san'],
                    'position_before': position_before,
                    'position_after': position_after,
                    'explanation': move['explanation'],
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully populated Chigorin Defense and lesson with programmatically '
                'generated FENs.'
            )
        )