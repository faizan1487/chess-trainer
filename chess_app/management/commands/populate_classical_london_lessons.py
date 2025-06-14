from django.core.management.base import BaseCommand
from chess_app.models import Opening, OpeningLesson, LessonMove

class Command(BaseCommand):
    help = 'Populates Chessable-style lessons for Classical London System and its sub-variations.'

    def handle(self, *args, **kwargs):
        # Find the Classical London System opening
        try:
            classical = Opening.objects.get(name="Classical London System")
        except Opening.DoesNotExist:
            self.stdout.write(self.style.ERROR('Classical London System not found.'))
            return

        # Main line for Classical London System
        main_line = [
            (1, 'd2d4', 'd4', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
             'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
             'White grabs central space with the d-pawn. This is the foundation of the London System.', True),
            (2, 'd7d5', 'd5', 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
             'rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2',
             'Black occupies the center as well.', False),
            (3, 'c1f4', 'Bf4', 'rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2',
             'rnbqkbnr/ppp1pppp/8/3p4/3P1B2/8/PPP1PPPP/RN1QKBNR b KQkq - 1 2',
             'The bishop develops outside the pawn chain, a key London System idea.', True),
            (4, 'g8f6', 'Nf6', 'rnbqkbnr/ppp1pppp/8/3p4/3P1B2/8/PPP1PPPP/RN1QKBNR b KQkq - 1 2',
             'rnbqkb1r/ppp1pppp/5n2/3p4/3P1B2/8/PPP1PPPP/RN1QKBNR w KQkq - 2 3',
             'Black develops a knight and prepares to contest the center.', False),
            (5, 'e2e3', 'e3', 'rnbqkb1r/ppp1pppp/5n2/3p4/3P1B2/8/PPP1PPPP/RN1QKBNR w KQkq - 2 3',
             'rnbqkb1r/ppp1pppp/5n2/3p4/3P1B2/4P3/PPP2PPP/RN1QKBNR b KQkq - 0 3',
             'White supports the d4 pawn and opens a path for the dark-squared bishop.', False),
            (6, 'c7c5', 'c5', 'rnbqkb1r/ppp1pppp/5n2/3p4/3P1B2/4P3/PPP2PPP/RN1QKBNR b KQkq - 0 3',
             'rnbqkb1r/pp2pppp/5n2/2pp4/3P1B2/4P3/PPP2PPP/RN1QKBNR w KQkq c6 0 4',
             "Black challenges the center and prepares to develop the queen's knight.", False),
            (7, 'c2c3', 'c3', 'rnbqkb1r/pp2pppp/5n2/2pp4/3P1B2/4P3/PPP2PPP/RN1QKBNR w KQkq c6 0 4',
             'rnbqkb1r/pp2pppp/5n2/2pp4/3P1B2/2P1P3/PP3PPP/RN1QKBNR b KQkq - 0 4',
             "White solidifies the center and prepares to develop the queen's knight.", False),
            (8, 'b8c6', 'Nc6', 'rnbqkb1r/pp2pppp/5n2/2pp4/3P1B2/2P1P3/PP3PPP/RN1QKBNR b KQkq - 0 4',
             'r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/2P1P3/PP3PPP/RN1QKBNR w KQkq - 1 5',
             "Black develops the queen's knight, increasing central pressure.", False),
            (9, 'g1f3', 'Nf3', 'r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/2P1P3/PP3PPP/RN1QKBNR w KQkq - 1 5',
             'r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/2P1PN2/PP3PPP/RN1QKB1R b KQkq - 2 5',
             'White develops the kingside knight, preparing to castle.', False),
            (10, 'e7e6', 'e6', 'r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/2P1PN2/PP3PPP/RN1QKB1R b KQkq - 2 5',
             'r1bqkb1r/pp2p1pp/2n1pn2/2pp4/3P1B2/2P1PN2/PP3PPP/RN1QKB1R w KQkq - 0 6',
             'Black supports the d5 pawn and opens a path for the dark-squared bishop.', False),
            (11, 'd1c2', 'Qc2', 'r1bqkb1r/pp2p1pp/2n1pn2/2pp4/3P1B2/2P1PN2/PP3PPP/RN1QKB1R w KQkq - 0 6',
             'r1bqkb1r/pp2p1pp/2n1pn2/2pp4/3P1B2/2P1PN2/PPQ2PPP/RN2KB1R b KQkq - 1 6',
             'White places the queen on c2, supporting the e4 push and eyeing the kingside.', True),
            (12, 'f8d6', 'Bd6', 'r1bqkb1r/pp2p1pp/2n1pn2/2pp4/3P1B2/2P1PN2/PPQ2PPP/RN2KB1R b KQkq - 1 6',
             'r1bqk2r/pp2p1pp/2nbpn2/2pp4/3P1B2/2P1PN2/PPQ2PPP/RN2KB1R w KQkq - 2 7',
             'Black develops the bishop and offers a trade. This is a common plan in the Classical London.', True)
        ]

        lesson, _ = OpeningLesson.objects.get_or_create(
            opening=classical,
            name="Classical London System - Main Ideas",
            description="Learn the main line and key plans in the Classical London System, with step-by-step explanations.",
            difficulty=1,
            order=1
        )

        for move in main_line:
            LessonMove.objects.get_or_create(
                lesson=lesson,
                move_number=move[0],
                defaults={
                    'move_uci': move[1],
                    'move_san': move[2],
                    'position_before': move[3],
                    'position_after': move[4],
                    'explanation': move[5],
                    'is_critical': move[6],
                }
            )

        # Sub-variations
        subvars = Opening.objects.filter(parent_opening=classical)
        for subvar in subvars:
            sub_lesson, _ = OpeningLesson.objects.get_or_create(
                opening=subvar,
                name=f"{subvar.name} - Main Ideas",
                description=f"Learn the main line and key plans in {subvar.name}, with step-by-step explanations.",
                difficulty=2,
                order=1
            )
            # For demo, add a placeholder move (customize as needed)
            LessonMove.objects.get_or_create(
                lesson=sub_lesson,
                move_number=1,
                defaults={
                    'move_uci': '',
                    'move_san': '',
                    'position_before': '',
                    'position_after': '',
                    'explanation': 'This is a placeholder for the main line of this sub-variation. Please update with real moves.',
                    'is_critical': True,
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated Chessable-style lessons for Classical London System and sub-variations.')) 