from django.core.management.base import BaseCommand
from chess_app.models import Opening, OpeningLesson, LessonMove, AlternativeMove
import chess
import chess.pgn
import io

class Command(BaseCommand):
    help = 'Populates the database with Ruy Lopez opening and variations'

    def handle(self, *args, **kwargs):
        # Create the main Ruy Lopez opening
        ruy_lopez, created = Opening.objects.get_or_create(
            name="Ruy Lopez",
            eco_code="C60",
            defaults={
                'description': "The Ruy Lopez is one of the oldest and most popular chess openings, named after the Spanish priest Ruy López de Segura. It begins with 1.e4 e5 2.Nf3 Nc6 3.Bb5, attacking the knight that defends the e5-pawn.",
                'pgn_moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5",
                'is_popular': True,
                'for_white': True,
                'category': "Open Game"
            }
        )

        # Create the main lesson for Ruy Lopez
        main_lesson = OpeningLesson.objects.get_or_create(
            opening=ruy_lopez,
            name="Ruy Lopez - Main Line",
            description="Learn the main line of the Ruy Lopez opening, one of the most popular and theoretically sound openings in chess.",
            difficulty=1,
            order=1
        )[0]

        # Create variations and their lessons
        variations = [
            {
                'name': "Berlin Defense",
                'moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6",
                'description': "A solid defense that leads to an endgame-oriented position. Popular at the highest levels.",
                'explanation': "The Berlin Defense is known for its solid and drawish nature. Black immediately challenges White's center with the knight."
            },
            {
                'name': "Morphy Defense",
                'moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6",
                'description': "The most common response to the Ruy Lopez, named after Paul Morphy. Black questions White's bishop placement.",
                'explanation': "The most popular response to the Ruy Lopez. Black immediately questions White's bishop and prepares ...b5."
            },
            {
                'name': "Classical Defense",
                'moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5 Bc5",
                'description': "A direct approach where Black develops the bishop to its most active square.",
                'explanation': "The Classical Defense develops the bishop to its most active square, but can leave Black's center slightly weak."
            },
            {
                'name': "Steinitz Defense",
                'moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5 d6",
                'description': "A solid but passive setup named after the first world champion Wilhelm Steinitz.",
                'explanation': "The Steinitz Defense reinforces the e5-pawn but is somewhat passive. Black plans a solid but cramped position."
            },
            {
                'name': "Schliemann Defense",
                'moves': "1. e4 e5 2. Nf3 Nc6 3. Bb5 f5",
                'description': "An aggressive counter-attacking variation where Black immediately fights for the center.",
                'explanation': "The Schliemann is a sharp counter-attacking try. Black immediately fights for the center but weakens the kingside."
            }
        ]

        for var_data in variations:
            # Create variation lesson
            lesson = OpeningLesson.objects.get_or_create(
                opening=ruy_lopez,
                name=f"Ruy Lopez - {var_data['name']}",
                description=var_data['description'],
                difficulty=2,
                order=len(variations) + 1
            )[0]

            # Parse the PGN
            game = chess.pgn.read_game(io.StringIO(var_data['moves']))
            board = chess.Board()
            move_number = 1

            # Create moves for the variation
            node = game
            while node.variations:
                next_node = node.variation(0)
                move = next_node.move
                
                if move:
                    move_san = board.san(move)
                    position_before = board.fen()
                    board.push(move)
                    position_after = board.fen()

                    lesson_move = LessonMove.objects.create(
                        lesson=lesson,
                        move_number=move_number,
                        move_uci=move.uci(),
                        move_san=move_san,
                        position_before=position_before,
                        position_after=position_after,
                        explanation=var_data['explanation'],
                        is_critical=(move_number <= 3)  # First 3 moves are critical
                    )

                    # Add some alternative moves
                    if move_number == 3:  # On the third move
                        for alt_move in board.legal_moves:
                            if alt_move != move:  # If it's not the main move
                                alt_san = board.san(alt_move)
                                AlternativeMove.objects.create(
                                    main_move=lesson_move,
                                    move_uci=alt_move.uci(),
                                    move_san=alt_san,
                                    explanation=f"This move is playable but not as strong as {move_san}.",
                                    evaluation="inaccuracy"
                                )

                    move_number += 1
                node = next_node

        self.stdout.write(self.style.SUCCESS('Successfully populated Ruy Lopez opening data')) 