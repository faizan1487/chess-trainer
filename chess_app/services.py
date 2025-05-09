import chess
import chess.engine
import chess.pgn
from functools import lru_cache
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import logging
from django.conf import settings
import re

# Configure logging
logger = logging.getLogger(__name__)

class StockfishEngine:
    """
    Service class to handle Stockfish engine communication.
    Uses singleton pattern to ensure only one engine instance.
    """
    _instance = None
    _engine = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockfishEngine, cls).__new__(cls)
            cls._instance._initialize_engine()
        return cls._instance
    
    def _initialize_engine(self):
        """Initialize or reinitialize the Stockfish engine."""
        # First close any existing engine
        if self._engine:
            try:
                self._engine.quit()
            except Exception as e:
                logger.error(f"Error quitting Stockfish: {e}")
            self._engine = None
            
        try:
            # Try to find Stockfish in the system path
            self._engine = chess.engine.SimpleEngine.popen_uci("stockfish")
            logger.info("Stockfish engine initialized")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize Stockfish: {e}")
            logger.warning("Running without Stockfish support. Some features may be limited.")
            self._engine = None
            return False
    
    def __del__(self):
        if self._engine:
            try:
                self._engine.quit()
            except Exception as e:
                logger.error(f"Error quitting Stockfish: {e}")
    
    def _ensure_engine_running(self):
        """Check if engine is running, restart if needed."""
        if not self._engine:
            return self._initialize_engine()
            
        # Test if engine is responsive
        try:
            # Ping the engine with a simple command
            test_board = chess.Board()
            self._engine.analyse(test_board, chess.engine.Limit(depth=1, time=0.1))
            return True
        except Exception as e:
            logger.error(f"Engine check failed: {e}")
            logger.info("Attempting to restart Stockfish engine")
            return self._initialize_engine()
    
    @lru_cache(maxsize=1024)
    def evaluate_position(self, fen, depth=15):
        """
        Evaluate a position and return the score from white's perspective.
        Uses LRU cache to avoid redundant evaluations.
        """
        if not self._ensure_engine_running():
            return 0.0  # Fallback to neutral evaluation
        
        try:
            board = chess.Board(fen)
            
            # Get info from engine
            info = self._engine.analyse(board, chess.engine.Limit(depth=depth))
            
            # Convert score to a numerical value
            score = info["score"].white().score(mate_score=10000)
            if score is not None:
                # Convert to pawn units (centipawns to pawns)
                return score / 100.0
            return 0.0
        except Exception as e:
            logger.error(f"Error evaluating position: {e}")
            # Try to restart the engine on failure
            self._initialize_engine()
            return 0.0
    
    def get_best_move(self, fen, depth=15):
        """Get the best move for a position."""
        if not self._ensure_engine_running():
            # If Stockfish is not available, make a basic move using Python-chess
            try:
                board = chess.Board(fen)
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    # Simple heuristic: capture if possible, otherwise random move
                    captures = [move for move in legal_moves if board.is_capture(move)]
                    if captures:
                        import random
                        return random.choice(captures)
                    else:
                        import random
                        return random.choice(legal_moves)
                return None
            except Exception as e:
                logger.error(f"Error getting basic move: {e}")
                return None
        
        try:
            board = chess.Board(fen)
            
            # Check if game is over
            if board.is_game_over():
                return None
            
            # Get best move from engine
            result = self._engine.play(board, chess.engine.Limit(depth=depth))
            
            return result.move
        except Exception as e:
            logger.error(f"Error getting best move: {e}")
            # Try to restart the engine on failure
            self._initialize_engine()
            
            # Fall back to basic move selection
            try:
                board = chess.Board(fen)
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    import random
                    return random.choice(legal_moves)
            except Exception as e:
                logger.error(f"Error selecting fallback move: {e}")
            
            return None
    
    def get_top_moves(self, fen, num_moves=3, depth=15):
        """Get the top N moves for a position with evaluations."""
        if not self._engine:
            # Simplified fallback if Stockfish is not available
            try:
                board = chess.Board(fen)
                legal_moves = list(board.legal_moves)
                if not legal_moves:
                    return []
                
                # Return up to num_moves legal moves
                import random
                selected_moves = random.sample(legal_moves, min(num_moves, len(legal_moves)))
                return [{"move": move, "san": board.san(move), "score": 0.0} for move in selected_moves]
            except Exception as e:
                logger.error(f"Error getting basic moves: {e}")
                return []
        
        try:
            board = chess.Board(fen)
            
            # Check if game is over
            if board.is_game_over():
                return []
            
            # Get multiple lines from engine
            multipv_results = []
            
            # Use a separate Stockfish instance for multipv analysis
            try:
                with chess.engine.SimpleEngine.popen_uci("stockfish") as temp_engine:
                    analysis = temp_engine.analyse(
                        board, 
                        chess.engine.Limit(depth=depth),
                        multipv=num_moves
                    )
                    for result in analysis:
                        move = result["pv"][0]
                        score = result["score"].white().score(mate_score=10000) / 100.0
                        multipv_results.append({
                            "move": move,
                            "san": board.san(move),
                            "score": score
                        })
            except Exception as e:
                logger.error(f"Error with temporary engine: {e}")
                # Fallback to the main engine if temp engine fails
                if self._engine:
                    best_move = self.get_best_move(fen, depth)
                    if best_move:
                        multipv_results.append({
                            "move": best_move,
                            "san": board.san(best_move),
                            "score": 0.0
                        })
            
            return multipv_results
        except Exception as e:
            logger.error(f"Error getting top moves: {e}")
            return []
    
    def analyze_move(self, fen, move_uci, depth=15):
        print("analyze_move method called")
        print(f"FEN: {fen}")
        print(f"Move UCI: {move_uci}")
        """
        Analyze a specific move compared to the best move.
        Returns evaluation, classification and reason.
        """
        if not self._ensure_engine_running():
            return 0.0, "normal", "No engine available for detailed analysis."
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                logger.warning(f"Illegal move {move_uci} for FEN {fen}")
                return None, "illegal", "This move is not legal in the given position."
            # Special handling for standard opening moves
            if self._is_standard_opening_move(board, move):
                return 0.0, "good", "This is a standard opening move."
            eval_before = self.evaluate_position(fen, depth)
            best_move = self.get_best_move(fen, depth)
            if best_move:
                best_board = chess.Board(fen)
                best_board.push(best_move)
                eval_best = self.evaluate_position(best_board.fen(), depth)
            else:
                eval_best = eval_before
            board.push(move)
            eval_after = self.evaluate_position(board.fen(), depth)
            move_loss = eval_best - eval_after
            classification, reason = self._classify_move(move_loss, board.turn)
            return eval_after, classification, reason
        except Exception as e:
            logger.error(f"Error analyzing move: {e}")
            return 0.0, "normal", "Error during analysis."
    
    def _is_standard_opening_move(self, board, move):
        """
        Check if a move is a standard opening move that should never be classified as a mistake.
        """
        # If we're past move 10, don't use this special handling
        if len(board.move_stack) >= 20:  # 10 full moves
            return False
        
        # Board is in starting position
        if board.fen() == chess.STARTING_FEN:
            # Standard first moves (e4, d4, c4, Nf3)
            if move.uci() in ["e2e4", "d2d4", "c2c4", "g1f3"]:
                return True
            
        # After 1.e4
        if board.fen() == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1":
            # Standard responses (e5, c5, e6, c6)
            if move.uci() in ["e7e5", "c7c5", "e7e6", "c7c6"]:
                return True
            
        # After 1.d4
        if board.fen() == "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1":
            # Standard responses (d5, Nf6, e6, g6)
            if move.uci() in ["d7d5", "g8f6", "e7e6", "g7g6"]:
                return True
            
        # After 1.c4
        if board.fen() == "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1":
            # Standard responses (e5, c5, Nf6)
            if move.uci() in ["e7e5", "c7c5", "g8f6"]:
                return True
            
        # After 1.Nf3
        if board.fen() == "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 0 1":
            # Standard responses (d5, Nf6, c5)
            if move.uci() in ["d7d5", "g8f6", "c7c5"]:
                return True
        
        # After 1.e4 e5
        if board.fen() == "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2":
            # Standard second moves (Nf3, Nc3, Bc4)
            if move.uci() in ["g1f3", "b1c3", "f1c4"]:
                return True
        
        # After 1.e4 e5 2.Nf3
        if board.fen() == "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2":
            # Standard responses (Nc6, Nf6)
            if move.uci() in ["b8c6", "g8f6"]:
                return True
        
        # Ruy Lopez specific moves
        # After 1.e4 e5 2.Nf3 Nc6
        if board.fen() == "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3":
            # 3.Bb5 (Ruy Lopez)
            if move.uci() == "f1b5":
                return True
        
        # Berlin Defense
        # After 1.e4 e5 2.Nf3 Nc6 3.Bb5
        if board.fen() == "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3":
            # 3...Nf6 (Berlin Defense)
            if move.uci() == "g8f6":
                return True
                
        return False
    
    def _classify_move(self, move_loss, player_color):
        """
        Classify a move based on its evaluation loss.
        Adjusts thresholds based on player color.
        """
        # Adjust the loss for black's perspective
        if player_color == chess.BLACK:
            move_loss = -move_loss
        
        # Classification thresholds
        if move_loss <= 0.1:
            return "best", "This is the best move in this position."
        elif move_loss <= 0.2:
            return "excellent", "This is an excellent move, very close to the best."
        elif move_loss <= 0.5:
            return "good", "This is a good move that maintains your advantage."
        elif move_loss <= 1.0:
            return "inaccuracy", "This is a slight inaccuracy that gives up some advantage."
        elif move_loss <= 2.0:
            return "mistake", "This move is a mistake that significantly weakens your position."
        else:
            return "blunder", "This move is a blunder that could cost you the game."

class ChessNLP:
    """
    Natural Language Processing service for chess-related conversations.
    """
    def __init__(self):
        # Download necessary NLTK packages if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        self.chess_keywords = {
            'opening': ['opening', 'variant', 'line', 'theory', 'book'],
            'tactic': ['tactic', 'fork', 'pin', 'skewer', 'discovered', 'attack', 'sacrifice'],
            'strategy': ['strategy', 'plan', 'position', 'advantage', 'control', 'space'],
            'endgame': ['endgame', 'ending', 'king', 'pawn', 'promotion'],
            'help': ['help', 'hint', 'suggestion', 'advice', 'recommend', 'should'],
            'evaluation': ['evaluation', 'eval', 'score', 'advantage', 'winning', 'losing', 'better', 'worse'],
            'why': ['why', 'reason', 'explanation', 'explain', 'understand'],
            'piece': ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king'],
            'time': ['time', 'clock', 'seconds', 'minutes'],
            'greeting': ['hello', 'hi', 'hey', 'greetings']
        }
    
    def analyze_message(self, message, board_fen=None, opening=None):
        print("analyze message called")
        # Compose a prompt for Gemini
        prompt = (
            "Classify the user's intent as one of: opening_info, move_analysis, general, greeting, hint, or other.\n"
            f"User message: '{message}'\n"
            "Return only the intent."
        )
        try:
            from django.conf import settings
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=getattr(settings, 'OPENAI_API_KEY', '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')
            )
            completion = client.chat.completions.create(
                extra_body={},
                model="google/gemini-2.0-flash-001",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            intent = completion.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"Gemini intent detection failed: {e}")
            intent = "general"

        # Extract move UCI using multiple patterns
        move_uci = None
        # Try to find UCI format (e2e4, g1f3, etc.)
        uci_match = re.search(r'([a-h][1-8][a-h][1-8][qrbn]?)', message.lower())
        if uci_match:
            move_uci = uci_match.group(1)
        else:
            # Try to find SAN format (e4, Nf3, O-O, etc.)
            san_match = re.search(r'\b([KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?|O-O(?:-O)?)\b', message)
            if san_match and board_fen:
                try:
                    board = chess.Board(board_fen)
                    move = board.parse_san(san_match.group(1))
                    move_uci = move.uci()
                except ValueError:
                    pass

        print("move", move_uci)
        if intent == "move_analysis" and move_uci:
            return {'intent': 'move_analysis', 'move_uci': move_uci}
        elif intent == "opening_info":
            return {'intent': 'opening_info'}
        print("returning intent")
        return {'intent': intent}
    
    def _determine_intent(self, message, topics, tokens):
        """Determine the primary intent of the message."""
        # Check for questions
        if '?' in message or any(q in tokens for q in ['what', 'why', 'how', 'when', 'where', 'which']):
            if 'why' in topics:
                return 'explanation'
            if 'opening' in topics:
                return 'opening_info'
            if 'evaluation' in topics:
                return 'position_evaluation'
            if any(piece in ''.join(tokens) for piece in self.chess_keywords['piece']):
                return 'piece_info'
            return 'general_question'
        
        # Check for requests
        if 'help' in topics:
            return 'request_hint'
        
        if 'greeting' in topics:
            return 'greeting'
            
        # Default intent
        return 'general_chat'
    
    def generate_response(self, analysis, stockfish_engine=None, game=None):
        print(f"Generating response for analysis: {analysis}")
        """
        Generate a response based on message analysis.
        Uses game state and Stockfish if available.
        """
        intent = analysis['intent']
        
        if intent == 'greeting':
            return "Hello! I'm your chess trainer. How can I help you with your opening preparation today?"
        
        elif intent == 'request_hint':
            if not stockfish_engine or not analysis['board_fen']:
                return "I'd recommend developing your pieces toward the center and ensuring your king's safety."
            
            # Get a hint from Stockfish
            board = chess.Board(analysis['board_fen'])
            top_moves = stockfish_engine.get_top_moves(analysis['board_fen'], 1)
            
            if top_moves:
                best_move = top_moves[0]['san']
                return f"I recommend playing {best_move}. This is currently the strongest move in this position."
            else:
                return "I'd recommend developing your pieces toward the center and ensuring your king's safety."
        
        elif intent == 'explanation':
            if not game:
                return "I need more context about the game to explain that."
                
            from chess_app.models import Move
            # Find the last AI move to explain
            last_ai_move = Move.objects.filter(game=game, player='ai').order_by('-move_number').first()
            if last_ai_move:
                return f"I played {last_ai_move.move_san} because {last_ai_move.feedback}"
            else:
                return "I haven't made a move yet in this game."
        
        elif intent == 'opening_info':
            if not analysis['opening']:
                return "We're not currently following a specific opening. Would you like me to suggest one?"
            
            return f"We're playing the {analysis['opening'].name}. {analysis['opening'].description}"
        
        elif intent == 'position_evaluation':
            if not stockfish_engine or not analysis['board_fen']:
                return "I don't have enough information to evaluate the current position."
            
            eval_score = stockfish_engine.evaluate_position(analysis['board_fen'])
            
            if eval_score > 3:
                return f"White has a winning advantage (+ {abs(eval_score):.1f})."
            elif eval_score > 1.5:
                return f"White has a significant advantage (+ {abs(eval_score):.1f})."
            elif eval_score > 0.5:
                return f"White has a slight advantage (+ {abs(eval_score):.1f})."
            elif eval_score > -0.5:
                return f"The position is approximately equal ({eval_score:.1f})."
            elif eval_score > -1.5:
                return f"Black has a slight advantage (- {abs(eval_score):.1f})."
            elif eval_score > -3:
                return f"Black has a significant advantage (- {abs(eval_score):.1f})."
            else:
                return f"Black has a winning advantage (- {abs(eval_score):.1f})."
        
        # Default response
        return "I'm your chess trainer. Ask me about the opening, the current position, or for a hint on what to play next."

    def generate_conversational_response(self, message, board_fen=None, opening=None):
        lowered = message.lower()
        if "favorite opening" in lowered:
            return "I really enjoy the Ruy Lopez! Do you have a favorite chess opening?"
        elif "how are you" in lowered:
            return "I'm just a chess AI, but I'm always ready to play or chat!"
        elif "joke" in lowered:
            return "Why did the chess player bring a ladder? To reach the next level!"
        elif "improve" in lowered:
            return "Practice, review your games, and study classic openings! Want tips for your current position?"
        elif "weather" in lowered:
            return "I'm not sure, but it's always a good day for chess!"
        elif "hello" in lowered or "hi" in lowered:
            return "Hello! Ready to talk chess or just chat?"
        elif "thank" in lowered:
            return "You're welcome! Let me know if you want to discuss strategy, analyze a move, or just chat."
        else:
            return "That's interesting! Let me know if you want to discuss strategy, analyze a move, or just chat about chess (or anything else)."

class OpeningExplorer:
    """Service for exploring chess openings and generating moves based on opening theory."""
    
    def __init__(self):
        self.stockfish = StockfishEngine()
    
    def get_next_book_move(self, board, opening):
        """
        Get the next move according to opening theory.
        
        Args:
            board: A chess.Board object with the current position
            opening: An Opening model instance
        
        Returns:
            A chess.Move object if a book move is found, None otherwise
        """
        # Ensure board is a chess.Board object
        if not isinstance(board, chess.Board):
            logger.error(f"Expected chess.Board object, got {type(board)}")
            return None
        
        if not opening or not opening.main_line:
            return None
        
        # First check if we're still in opening theory by comparing the current position
        if not self.is_position_in_opening(board, opening):
            logger.info(f"Position {board.fen()} is no longer in opening theory")
            return None
        
        # Parse the main line, filtering out move numbers (entries ending with '.')
        main_line_parts = opening.main_line.split()
        main_line_moves = [move for move in main_line_parts if not move.endswith('.')]
        
        # Get the move number we're at 
        # This should correspond to the index in the filtered moves list
        move_count = len(board.move_stack)
        # Fix: Use a fresh board for SAN conversion
        san_moves = []
        temp_board = chess.Board()  # Always start from the initial position
        for m in board.move_stack:
            san_moves.append(temp_board.san(m))
            temp_board.push(m)

        # Check if we're still within the opening book
        if move_count < len(main_line_moves):
            try:
                # Try to parse the book move
                book_move_san = main_line_moves[move_count]
                logger.info(f"Trying book move: {book_move_san} at position {move_count}")
                book_move = board.parse_san(book_move_san)
                
                # Validate that this is a legal move
                if book_move in board.legal_moves:
                    return book_move
            except Exception as e:
                # If there's any error parsing, fall back to engine
                logger.error(f"Error parsing book move: {e}")
                pass
            
        return None
        
    def is_position_in_opening(self, board, opening):
        """Check if the current position still follows the opening theory."""
        # Ensure board is a chess.Board object
        if not isinstance(board, chess.Board):
            logger.error(f"Expected chess.Board object, got {type(board)}")
            return False
        
        if not opening or not opening.pgn_moves:
            return False
        
        # If we're past move 10, consider it out of opening theory
        if len(board.move_stack) > 20:  # 10 full moves = 20 half-moves
            logger.info(f"Move count {len(board.move_stack)} exceeds opening phase")
            return False
        
        # Create a new board and apply the opening moves
        theory_board = chess.Board()
        
        # Filter out move numbers (entries ending with '.')
        pgn_parts = opening.pgn_moves.split()
        pgn_moves = [move for move in pgn_parts if not move.endswith('.')]
        
        # Apply moves from the opening
        for san_move in pgn_moves:
            try:
                move = theory_board.parse_san(san_move)
                theory_board.push(move)
            except ValueError as e:
                logger.error(f"Error parsing opening move: {e}")
                break
        
        # Check if our position matches one of the positions in the opening theory
        # We need to find if our current board state is reachable in the opening
        test_board = chess.Board()
        for san_move in pgn_moves:
            try:
                move = test_board.parse_san(san_move)
                test_board.push(move)
                
                # Compare positions (ignoring move counters)
                current_fen_parts = board.fen().split(' ')
                test_fen_parts = test_board.fen().split(' ')
                
                # If positions match, we're still in opening theory
                if current_fen_parts[:4] == test_fen_parts[:4]:
                    return True
            except ValueError:
                continue
            
        # If we get here, we didn't find a match
        logger.info(f"Current position {board.fen()} not found in opening theory")
        return False
    
    def generate_explanation(self, board, move, opening):
        """Generate an explanation for why a particular move was chosen in opening theory."""
        # Ensure board is a chess.Board object
        if not isinstance(board, chess.Board):
            logger.error(f"Expected chess.Board object, got {type(board)}")
            return f"This move follows opening principles."
        
        # Ensure move is a chess.Move object
        if not isinstance(move, chess.Move):
            logger.error(f"Expected chess.Move object, got {type(move)}")
            return f"This move follows opening principles."
        
        # Create a copy of the board before the move
        board_copy = board.copy()
        # Go back one move if the move has already been played
        if len(board_copy.move_stack) > 0:
            board_copy.pop()
        # Now we can safely get the SAN notation
        try:
            move_san = board_copy.san(move)
        except (AssertionError, ValueError):
            # If we can't get the SAN notation, just use UCI notation
            move_san = move.uci()
        
        # If we're in a named opening, provide context
        if opening:
            # Find key positions and explanations from our database
            return f"The move {move_san} is part of the standard theory in the {opening.name}. This move helps to establish control of the center and develop pieces efficiently."
        
        # Generic explanation
        return f"The move {move_san} follows sound opening principles by developing pieces and controlling the center."

class FeedbackGenerator:
    """
    Service to generate chess feedback based on move quality and position context.
    """
    def __init__(self, stockfish_engine=None):
        self.engine = stockfish_engine if stockfish_engine else StockfishEngine()
        self.opening_explorer = OpeningExplorer()
    
    def generate_move_feedback(self, board_fen, move_uci, classification, opening=None):
        """
        Generate detailed feedback for a move based on its classification and position.
        """
        try:
            # Create board from FEN string if it's not already a Board object
            board = board_fen if isinstance(board_fen, chess.Board) else chess.Board(board_fen)
            move = chess.Move.from_uci(move_uci)
            
            # Create a copy of the board for analysis
            board_copy = board.copy()
            
            # Get basic move information
            piece_moved = board.piece_at(move.from_square)
            is_capture = board.is_capture(move)
            
            # Check if the move is legal before checking if it gives check
            gives_check = False
            if move in board_copy.legal_moves:
                gives_check = board_copy.gives_check(move)
            else:
                logger.warning(f"Move {move_uci} is not legal in position {board.fen()}")
            
            # Apply the move to the original board to see the resulting position
            # Only if it's legal
            if move in board.legal_moves:
                board.push(move)
            else:
                # If the move is not legal (e.g., castling when no longer allowed), 
                # we still want to provide feedback but won't update the board
                logger.warning(f"Skipping board update for illegal move {move_uci}")
            
            # Classification-based feedback
            if classification == "best":
                feedback = "Excellent move! "
            elif classification == "excellent":
                feedback = "Very good move! "
            elif classification == "good":
                feedback = "Good move. "
            elif classification == "inaccuracy":
                feedback = "Slight inaccuracy. "
            elif classification == "mistake":
                feedback = "This is a mistake. "
            else:  # blunder
                feedback = "This is a serious mistake (blunder). "
            
            # Make sure we have a piece_moved before accessing its properties
            if not piece_moved:
                logger.warning(f"No piece found at {move.from_square} for move {move_uci}")
                return feedback + "This move doesn't follow standard principles."
            
            # Add context based on the piece moved
            if piece_moved.piece_type == chess.PAWN:
                if move.to_square in [i for i in range(8)] or move.to_square in [i for i in range(56, 64)]:
                    feedback += "Promoting your pawn is a strong move."
                elif is_capture:
                    feedback += "This pawn capture changes the pawn structure."
                else:
                    feedback += "This pawn advance affects the center control and future pawn structure."
                    
            elif piece_moved.piece_type == chess.KNIGHT:
                if is_capture:
                    feedback += "Your knight captures a piece, changing the material balance."
                else:
                    # Check if knight moves to outpost
                    is_outpost = False
                    if piece_moved.color == chess.WHITE and move.to_square // 8 >= 4:
                        is_outpost = True
                    elif piece_moved.color == chess.BLACK and move.to_square // 8 <= 3:
                        is_outpost = True
                    
                    if is_outpost:
                        feedback += "Your knight moves to an advanced outpost."
                    else:
                        feedback += "Knight repositioning can open up new tactical possibilities."
                        
            elif piece_moved.piece_type == chess.BISHOP:
                if is_capture:
                    feedback += "Your bishop captures a piece, changing the material balance."
                else:
                    feedback += "This bishop move affects the control of the diagonals."
                    
            elif piece_moved.piece_type == chess.ROOK:
                if move.from_square % 8 == move.to_square % 8:
                    feedback += "Your rook moves along a file, potentially increasing its control."
                elif move.from_square // 8 == move.to_square // 8:
                    feedback += "Your rook moves along a rank, potentially increasing its control."
                
            elif piece_moved.piece_type == chess.QUEEN:
                if is_capture:
                    feedback += "Your queen captures a piece, changing the material balance."
                else:
                    feedback += "Queen repositioning can create new attacking possibilities."
                    
            elif piece_moved.piece_type == chess.KING:
                # Special handling for castling moves
                is_castling_attempt = (
                    (move.from_square == chess.E1 and move.to_square in [chess.G1, chess.C1]) or
                    (move.from_square == chess.E8 and move.to_square in [chess.G8, chess.C8])
                )
                
                if is_castling_attempt:
                    if move in board_copy.legal_moves:
                        # Legal castling
                        if move.to_square in [chess.G1, chess.G8]:
                            feedback += "Castling kingside improves king safety and connects your rooks."
                        else:
                            feedback += "Castling queenside can be more aggressive but may expose your king."
                    else:
                        # Attempted castling that's not legal
                        feedback += "You attempted to castle, but it's not legal in this position. King movements should prioritize safety."
                else:
                    feedback += "King movements should generally prioritize safety."
            
            # Add check information
            if gives_check:
                feedback += " Your move gives check to the opponent's king."
            
            # Add opening-specific feedback if available
            if opening and board.fullmove_number <= 10:
                try:
                    opening_feedback = self.opening_explorer.generate_explanation(board, move, opening)
                    feedback += f" {opening_feedback}"
                except Exception as e:
                    logger.error(f"Error generating opening feedback: {e}")
            
            return feedback
        except Exception as e:
            logger.error(f"Error generating move feedback: {e}")
            return f"Move analysis: {classification.capitalize()}. Consider analyzing the position carefully."

    def suggest_improvement(self, board_fen, classification):
        """
        Suggest improvement based on position and move classification.
        """
        if classification in ["best", "excellent"]:
            return "Keep up the good work!"
            
        board = chess.Board(board_fen)
        
        # Get Stockfish suggestions
        top_moves = self.engine.get_top_moves(board_fen, 1)
        
        if not top_moves:
            return "Consider analyzing the position more carefully before making your move."
            
        best_move = top_moves[0]
        
        if classification == "good":
            return f"A good alternative would be {best_move['san']}."
        elif classification == "inaccuracy":
            return f"A stronger move would be {best_move['san']}, which would give you better chances."
        elif classification == "mistake":
            return f"Instead, {best_move['san']} would be much stronger and maintain your advantage."
        else:  # blunder
            return f"{best_move['san']} would be much stronger. Always check for tactics before making your move." 