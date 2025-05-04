from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
import chess
import chess.pgn
import io
import logging
import random
import spacy
import openai
from openai import OpenAI
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

from .models import (
    Opening, Game, Move, UserProfile, UserProgress, Challenge, UserChallenge
)
from .services import (
    StockfishEngine, ChessNLP, FeedbackGenerator, OpeningExplorer
)  # noqa: E501

# Configure logging to output to the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
stockfish_engine = StockfishEngine()
chess_nlp = ChessNLP()
feedback_generator = FeedbackGenerator(stockfish_engine)

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# Set your OpenAI API key
openai.api_key = 'YOUR_API_KEY'  # noqa: E501

# Initialize OpenAI client with Gemini
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)  # noqa: E501

def home(request):
    """Home page view."""
    return render(request, 'chess_app/home.html')

def opening_selection(request):
    """View to select a chess opening to practice."""
    openings = Opening.objects.all().order_by('name')
    return render(
        request, 'chess_app/opening_selection.html', {'openings': openings}
    )  # noqa: E501

@login_required
def game(request, opening_id):
    """View to play a game with a specific opening."""
    opening = get_object_or_404(Opening, id=opening_id)
    
    # Create or get an existing game
    game, created = Game.objects.get_or_create(
        user=request.user,
        opening=opening,
        status='ONGOING',
        defaults={'user_color': 'white'}  # Default to white, could be randomized
    )
    
    # Get or create user progress for this opening
    progress, _ = UserProgress.objects.get_or_create(
        user=request.user,
        opening=opening
    )
    
    return render(request, 'chess_app/game.html', {
        'opening': opening,
        'game': game,
        'progress': progress
    })

@login_required
@require_POST
def make_move(request, game_id):
    """API endpoint to record a user's move and get feedback."""
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    
    # Get move data from request
    move_uci = request.POST.get('move_uci')  # Ensure this is a UCI move string
    position_before = request.POST.get('position_before')
    
    # Log the received move and board state
    logger.info(f"Received move: {move_uci} for game: {game_id}")
    logger.info(f"Board position before move: {position_before}")
    
    # Create a chess board from the position before the move
    board = chess.Board(position_before)
    move = chess.Move.from_uci(move_uci)
    logger.info(f"Checking legality of move {move_uci} on board: {board.fen()}")
    
    # Validate the move
    if move not in board.legal_moves:
        logger.warning(f"Illegal move attempted: {move_uci} on board: {board.fen()}")
        return JsonResponse({'status': 'error', 'message': 'Illegal move'}, status=400)
    
    # Analyze the move using Stockfish BEFORE pushing the move
    eval_score, classification, reason = stockfish_engine.analyze_move(
        position_before, move_uci
    )
    logger.info(f"Analysis result: eval_score={eval_score}, classification={classification}, reason={reason}")
    if classification == "illegal":
        logger.warning(f"Analysis found move illegal: {move_uci} on board: {position_before}")
        return JsonResponse({'status': 'error', 'message': reason}, status=400)
    
    # Now push the move
    board.push(move)
    logger.info(f"Board after move: {board.fen()}")
    
    # Generate detailed feedback using the board state BEFORE the move
    feedback = feedback_generator.generate_move_feedback(
        board_fen=position_before,
        move_uci=move_uci,
        classification=classification,
        opening=game_obj.opening
    )
    
    # Generate improvement suggestion if needed
    improvement = ""
    if classification not in ["best", "excellent", "good"]:
        improvement = feedback_generator.suggest_improvement(
            board.fen(), classification
        )
    
    # Save the move to the database
    Move.objects.create(
        game=game_obj,
        move_number=get_next_move_number(game_obj),
        move_uci=move_uci,
        move_san=move_uci,  # Assuming SAN is the same for simplicity
        position_before=position_before,
        position_after=board.fen(),
        player='user',
        eval_score=eval_score,
        is_mistake=classification in ["mistake", "blunder"],
        quality=classification,
        feedback=feedback,
        improvement_suggestion=improvement
    )
    
    # Update the game state
    game_obj.fen_position = board.fen()
    game_obj.save()
    
    # Update user progress
    update_user_progress(request.user, game_obj.opening, classification)
    
    response = {
        'status': 'success',
        'move': move_uci,
        'feedback': feedback,
        'improvement': improvement,
        'classification': classification
    }
    logger.info(f"Returning move analysis response: {response}")
    return JsonResponse(response)

@login_required
@require_GET
def get_ai_move(request, game_id):
    """API endpoint to get the AI's next move."""
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    
    # Create a chess board from the current position
    # Commenting out unused variables
    # board = chess.Board(game_obj.fen_position)
    
    # Generate AI move based on the opening or engine
    ai_move, san_move, evaluation = generate_ai_move(
        chess.Board(game_obj.fen_position),
        game_obj.opening,
        game_obj.ai_strength
    )  # noqa: E501
    
    if ai_move:
        # Apply the move to the board
        # Commenting out unused variables
        # board.push(ai_move)
        
        # Generate feedback for the AI move
        feedback = generate_ai_explanation(
            chess.Board(game_obj.fen_position),
            ai_move,
            game_obj.opening
        )  # noqa: E501
        
        # Save the move to the database
        move_obj = Move.objects.create(
            game=game_obj,
            move_number=get_next_move_number(game_obj),
            move_uci=ai_move.uci(),
            move_san=san_move,
            position_before=game_obj.fen_position,
            position_after=game_obj.fen_position,
            player='ai',
            eval_score=evaluation,
            quality='best',  # AI always plays best moves
            feedback=feedback
        )
        
        # Update the game state
        game_obj.fen_position = game_obj.fen_position
        game_obj.save()
        
        return JsonResponse({
            'status': 'success',
            'move': san_move,
            'move_uci': ai_move.uci(),
            'feedback': move_obj.feedback
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Could not generate AI move'
    }, status=400)

@login_required
@require_GET
def get_hint(request, game_id):
    """API endpoint to get a hint for the current position."""
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    
    # Create a chess board from the current position
    # Commenting out unused variables
    # board = chess.Board(game_obj.fen_position)
    
    # Use Stockfish to get top moves
    top_moves = stockfish_engine.get_top_moves(game_obj.fen_position, 1)
    
    if top_moves:
        best_move = top_moves[0]
        hint = (
            f"I recommend playing {best_move['san']}. This is currently the strongest move."
        )  # noqa: E501
        
        # Check if we're still in the opening book
        if game_obj.in_opening_book:
            pgn = game_obj.opening.pgn_moves
            game = chess.pgn.read_game(io.StringIO(pgn))
            
            node = game
            while node.variations and str(node.board()) != str(game_obj.opening):
                node = node.variations[0]
            
            # If we're still in the opening book
            if node.variations:
                next_move = node.variations[0].move
                san_move = game_obj.opening.san(next_move)
                
                # If the book move matches the engine move, mention it
                if san_move == best_move['san']:
                    hint = (
                        f"I recommend playing {san_move}. This is the main line of the {game_obj.opening.name}."
                    )  # noqa: E501
                else:
                    hint = (
                        f"The main line continues with {san_move}, but {best_move['san']} is also a strong alternative."
                    )  # noqa: E501
    else:
        hint = "Look for pieces that are undefended or could be developed to better squares."
    
    return JsonResponse({
        'status': 'success',
        'hint': hint
    })

@login_required
@require_POST
def chat(request, game_id):
    print("Chat request received")
    """API endpoint for chat interaction with the AI."""
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    
    # Robustly extract message and FEN from JSON or form POST
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            board_fen = data.get('fen', game_obj.fen_position)
            conversation_history = data.get('history', [])  # Get conversation history
            # print("fen in try", board_fen)
            # print("conversation history:", conversation_history)
        except Exception as e:
            print(f"Error parsing JSON body: {e}")
            message = ''
            board_fen = game_obj.fen_position
            conversation_history = []
            print("fen in except", board_fen)
    else:
        message = request.POST.get('message', '')
        board_fen = request.POST.get('fen', game_obj.fen_position)
        conversation_history = request.POST.get('history', [])
        print("fen in else", board_fen)

    # Add the new message to the conversation history
    conversation_history.append({"role": "user", "content": message})

    # Generate response with context
    response = analyze_question(message, board_fen, conversation_history)

    # Add the AI's response to the conversation history
    conversation_history.append({"role": "assistant", "content": response})

    return JsonResponse({
        'status': 'success',
        'response': response,
        'history': conversation_history  # Return updated history
    })

@login_required
@require_POST
def reset_game(request, game_id):
    """API endpoint to reset a game to the starting position."""
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    
    # Reset the game
    game_obj.fen_position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    game_obj.in_opening_book = True
    game_obj.save()
    
    # Delete all moves from this game
    Move.objects.filter(game=game_obj).delete()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Game has been reset'
    })

@login_required
def opening_explorer(request, opening_id=None):
    """View to explore chess openings and their variations."""
    if opening_id:
        opening = get_object_or_404(Opening, id=opening_id)
        positions = OpeningExplorer.get_opening_positions(opening.pgn_moves)
        
        # Get user progress for this opening if it exists
        progress = None
        if request.user.is_authenticated:
            progress = UserProgress.objects.filter(
                user=request.user, 
                opening=opening
            ).first()
        
        return render(request, 'chess_app/opening_explorer_detail.html', {
            'opening': opening,
            'positions': positions,
            'progress': progress
        })
    else:
        # List all openings
        openings = Opening.objects.all().order_by('name')
        categories = Opening.objects.values_list('category', flat=True).distinct()
        
        return render(request, 'chess_app/opening_explorer.html', {
            'openings': openings,
            'categories': categories
        })

@login_required
def user_profile(request):
    """View to display user profile and progress."""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user progress across all openings
    progress_list = UserProgress.objects.filter(user=request.user).order_by('-mastery_level')
    
    # Get recent games
    recent_games = Game.objects.filter(user=request.user).order_by('-updated_at')[:5]
    
    # Get unsolved challenges
    unsolved_challenges = UserChallenge.objects.filter(
        user=request.user, 
        is_solved=False
    ).select_related('challenge')[:5]
    
    return render(request, 'chess_app/user_profile.html', {
        'profile': user_profile,
        'progress_list': progress_list,
        'recent_games': recent_games,
        'unsolved_challenges': unsolved_challenges
    })

@login_required
def challenges(request):
    """View to see all available chess challenges."""
    challenges = Challenge.objects.all()
    
    # Get user-challenge associations for the current user
    user_challenges = {
        uc.challenge_id: uc for uc in 
        UserChallenge.objects.filter(user=request.user)
    }
    
    return render(request, 'chess_app/challenges.html', {
        'challenges': challenges,
        'user_challenges': user_challenges
    })

@login_required
def challenge_detail(request, challenge_id):
    """View for a specific chess challenge."""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # Get or create user challenge record
    user_challenge, created = UserChallenge.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )
    
    return render(request, 'chess_app/challenge_detail.html', {
        'challenge': challenge,
        'user_challenge': user_challenge
    })

@login_required
@require_POST
def verify_challenge_solution(request, challenge_id):
    """API endpoint to verify a user's solution to a challenge."""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    user_challenge, created = UserChallenge.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )
    
    # Get the moves from the request
    moves = request.POST.getlist('moves')
    
    # Increment attempt counter
    user_challenge.attempts += 1
    
    # Check if the solution is correct
    solution_pgn = challenge.solution_moves
    user_pgn = ' '.join(moves)
    
    # Simple string comparison for now - in a real app,
    # you'd want to compare actual moves more robustly
    is_correct = user_pgn.strip() == solution_pgn.strip()
    
    if is_correct:
        user_challenge.is_solved = True
        from django.utils import timezone
        user_challenge.solved_date = timezone.now()
    
    user_challenge.save()
    
    return JsonResponse({
        'status': 'success',
        'is_correct': is_correct,
        'attempts': user_challenge.attempts
    })

def analyze_question(question, board_fen=None, conversation_history=None):
    print("analyze_question method called")
    # logger.info(f"Received question: {question}")
    # logger.info(f"Board FEN: {board_fen}")
    # logger.info(f"Conversation history: {conversation_history}")
    
    try:
        # Prepare the conversation context
        context = ""
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                context += f"{role}: {msg['content']}\n"
            context += "\nCurrent question:\n"

        prompt = (
            f"You are a highly skilled chess expert with extensive knowledge of chess strategy, tactics, and board dynamics. "
            f"You are currently being used as a chat agent in the backend for an agentic chess application designed to help users improve their openings. "
            f"{context}"
            f"The user asks: '{question}'. Carefully analyze the user's question, considering the context and nuances, and respond with a clear and insightful answer. "
            "If the question is not related to the current board position or does not require a strategic recommendation, avoid referencing the FEN. "
            "However, if the user asks about what move to make next, what action to take, or what strategy to adopt based on the current position, do not mention the FEN directly. "
            "Focus on understanding the user's intent and providing a response that is not only accurate but also actionable. "
            "Provide guidance that could improve the user's chess game, whether it's through suggesting the best move, explaining a strategy, or offering advice on improving play. "
            "Your answer should be structured, well thought-out, and tailored to the user's level of experience, aiming to help them understand both the move and the reasoning behind it. "
            "If the question is open-ended or vague, ask for further clarification to ensure you provide the most relevant and helpful response. "
            f"This is the current board state: {board_fen}"
        )

        completion = client.chat.completions.create(
            extra_body={},
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        print("completion", completion)
        
        # Extract the final response from the completion
        raw_response = completion.choices[0].message.content

        return raw_response
    except Exception as e:
        logger.error(f"Error with Gemini API: {e}")
        return "Error processing your request. Please try again later."

@csrf_exempt
def ask_question(request):
    print(f"Received request: {request}")
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('message', '')
        board_fen = data.get('fen', '')
        response = analyze_question(question, board_fen)
        return JsonResponse({'response': response})

# Helper functions

def validate_move(board, move):
    """
    Validate if a move is legal in the current position.
    Returns a tuple of (is_valid, board_copy) where board_copy is in the correct position for the move.
    """
    board_copy = board.copy()
    
    # Log the current board state and move
    logger.info(f"Validating move: {move.uci()} on board: {board.fen()}")
    
    # First check if the move is already legal
    if move in board_copy.legal_moves:
        return True, board_copy
        
    # If not, try undoing moves until we find a position where it is legal
    while board_copy.move_stack:
        board_copy.pop()
        if move in board_copy.legal_moves:
            return True, board_copy
            
    # Log if the move is illegal
    logger.warning(f"Illegal move: {move.uci()} on board: {board.fen()}")
    return False, board_copy

def get_next_move_number(game):
    """Get the next move number for a game."""
    last_move = Move.objects.filter(game=game).order_by('-move_number').first()
    return 1 if last_move is None else last_move.move_number + 1

def generate_ai_move(board, opening, depth=15):
    """Generate a move for the AI based on the opening or engine."""
    opening_explorer = OpeningExplorer()
    
    # First check if we're in the opening book
    book_move = None
    if opening:
        # Try to get a move from opening theory
        book_move = opening_explorer.get_next_book_move(board, opening)
    
    if book_move:
        # We found a move in the opening book
        try:
            # First check if the move is legal in the current position
            if book_move in board.legal_moves:
                san_move = board.san(book_move)
                return book_move, san_move, 0  # Evaluation is not relevant for book moves
        except Exception as e:
            logger.error(
                f"Error converting book move to SAN: {e}"
            )  # noqa: E501
            # Continue to try engine move
    
    # If we're not in the opening book or there's no suitable book move,
    # fall back to the engine
    try:
        # Get a move from Stockfish
        engine_move = stockfish_engine.get_best_move(board.fen(), depth)
        if engine_move:
            # Handle both UCI string and Move object returns from get_best_move
            if isinstance(engine_move, str):
                ai_move = chess.Move.from_uci(engine_move)
            else:
                ai_move = engine_move
                
            # Check if the move is legal in the current position
            if ai_move in board.legal_moves:
                # Get the evaluation of the position
                evaluation = stockfish_engine.evaluate_position(board.fen())
                san_move = board.san(ai_move)
                return ai_move, san_move, evaluation
    except Exception as e:
        logger.error(f"Error generating AI move: {e}")
    
    # As a last resort, just make a random legal move
    legal_moves = list(board.legal_moves)
    if legal_moves:
        random_move = random.choice(legal_moves)
        try:
            san_move = board.san(random_move)
            return random_move, san_move, 0
        except Exception as e:
            logger.error(f"Error converting random move to SAN: {e}")
    
    # If we somehow have no legal moves, return None
    return None, None, 0

def generate_ai_explanation(board, move, opening):
    """Generate an explanation for the AI's move."""
    # Verify that we have valid inputs
    if not move or not isinstance(move, chess.Move):
        return "I couldn't generate a move for this position."
    
    if not isinstance(board, chess.Board):
        logger.error(f"Expected chess.Board object, got {type(board)}")
        return f"I played {move.uci()}, which is a strong move in this position."
        
    opening_explorer = OpeningExplorer()
    
    # Check if we're still in opening theory
    if opening and opening_explorer.is_position_in_opening(board, opening):
        return opening_explorer.generate_explanation(board, move, opening)
    
    try:
        # Validate the move and get the correct board position
        is_valid, board_copy = validate_move(board, move)
        if not is_valid:
            return f"I played {move.uci()}, but I'm having trouble explaining it in detail."
        
        # Get information about the move
        try:
            san_move = board_copy.san(move)
        except ValueError:
            # If we can't get SAN notation, use UCI
            san_move = move.uci()
        
        # Create a deep copy of the board for checking captures
        # We need to make sure the move hasn't been played yet
        pre_move_board = board_copy.copy()
        
        # Check if there's a piece at the destination square (for capture detection)
        target_piece = pre_move_board.piece_at(move.to_square)
        is_capture = target_piece is not None
        
        # Also check for en passant capture
        if move.to_square == pre_move_board.ep_square and pre_move_board.piece_at(move.from_square).piece_type == chess.PAWN:
            is_capture = True
            
        # Apply the move to analyze the resulting position
        board_copy.push(move)
        
        # Generate explanation based on the type of move
        if is_capture and target_piece:
            # Get the pieces involved in the capture
            capturing_piece = pre_move_board.piece_at(move.from_square)
            
            if capturing_piece:  # Make sure the capturing piece exists
                if target_piece.piece_type > capturing_piece.piece_type:
                    return f"I played {san_move}, capturing your {target_piece.symbol().upper()} with my {capturing_piece.symbol().upper()}, which is a favorable exchange for me."
                else:
                    return f"I played {san_move}, capturing your {target_piece.symbol().upper()} to simplify the position."
        else:
            return f"I played {san_move}, which is a strong move in this position according to my analysis."
        
        if board_copy.is_check():
            return f"I played {san_move}, which puts your king in check. This forces you to respond to the threat."
        
        # If it's a pawn move
        if pre_move_board.piece_at(move.from_square) and pre_move_board.piece_at(move.from_square).piece_type == chess.PAWN:
            # Check if it's an advanced pawn move
            if (pre_move_board.turn == chess.WHITE and move.to_square // 8 >= 5) or \
               (pre_move_board.turn == chess.BLACK and move.to_square // 8 <= 2):
                return f"I played {san_move}, advancing my pawn to control more space."
            else:
                return f"I played {san_move}, developing my pawn structure."
        
        # Check if it's a developing move for a piece from its starting position
        if pre_move_board.piece_at(move.from_square) and pre_move_board.piece_at(move.from_square).piece_type != chess.KING and \
           move.from_square in [chess.A1, chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1, 
                              chess.A8, chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8]:
            return f"I played {san_move}, developing a piece to a more active square."
        
        # Check if it's castling
        if pre_move_board.is_castling(move):
            return f"I played {san_move}, castling to safety and connecting my rooks."
        
        # Default explanation
        return f"I played {san_move}, which is a strong move in this position according to my analysis."
    except Exception as e:
        logger.error(f"Error generating move explanation: {e}")
        return "I made a move, but I'm having trouble explaining it in detail."

def update_user_progress(user, opening, move_quality):
    """Update the user's progress for an opening based on move quality."""
    progress, created = UserProgress.objects.get_or_create(
        user=user,
        opening=opening
    )
    # Increment games played if it's a new game
    if created:
        progress.games_played = 1
    # Calculate move quality as a percentage 
    quality_scores = {
        'best': 100,
        'excellent': 90,
        'good': 75,
        'inaccuracy': 50,
        'mistake': 25,
        'blunder': 0,
        'normal': 60
    }
    move_score = quality_scores.get(move_quality, 60)
    # Update average accuracy with a weighted approach to recent games
    if progress.avg_accuracy == 0:
        progress.avg_accuracy = move_score
    else:
        # Weight recent games more heavily (80% new, 20% old)
        progress.avg_accuracy = (0.8 * move_score) + (0.2 * progress.avg_accuracy)
    # Update best accuracy if this is better
    if move_score > progress.best_accuracy:
        progress.best_accuracy = move_score
    # Calculate mastery level based on accuracy and games played
    # More games played increases mastery, as does higher accuracy
    games_factor = min(progress.games_played / 10, 1.0)  # Caps at 10 games
    progress.mastery_level = int(progress.avg_accuracy * games_factor)
    progress.save()
    return progress

@login_required
@require_GET
def get_move_history(request, game_id):
    game_obj = get_object_or_404(Game, id=game_id, user=request.user)
    moves = Move.objects.filter(game=game_obj).order_by('move_number')
    move_list = [
        {
            'move_number': m.move_number,
            'move_san': m.move_san,
            'player': m.player
        }
        for m in moves
    ]
    return JsonResponse({'status': 'success', 'moves': move_list})

@csrf_protect
def register(request):
    """View to handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'chess_app/register.html', {'form': form})
