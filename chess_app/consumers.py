import json
import chess
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .services import StockfishEngine, ChessNLP, FeedbackGenerator
import io
from .models import Game, Move

logger = logging.getLogger(__name__)

class ChessConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chess interactions.
    Provides move processing, chat, and engine analysis.
    """
    async def connect(self):
        """Handle websocket connection"""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'chess_game_{self.game_id}'
        self.user = self.scope['user']
        
        # Validate user and game
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has access to this game
        if not await self.user_has_game_access():
            await self.close()
            return
            
        # Join game group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current game state
        game_data = await self.get_game_data()
        await self.send(text_data=json.dumps(game_data))
    
    async def disconnect(self, close_code):
        """Handle websocket disconnection"""
        # Leave game group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'move':
                # Process player move
                await self.process_move(data)
            elif action == 'chat':
                # Process chat message
                await self.process_chat(data)
            elif action == 'request_hint':
                # Process hint request
                await self.process_hint_request()
            elif action == 'reset_game':
                # Reset the game
                await self.reset_game()
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not process your request'
            }))
    
    async def process_move(self, data):
        """Process a player's move"""
        try:
            move_uci = data.get('move_uci')  # Ensure this is a UCI move string
            move_san = data.get('move_san')
            position_before = data.get('position_before')
            position_after = data.get('position_after')
            
            # Validate and analyze the move
            print("Analyzing move using Stockfish 3")
            move_data = await database_sync_to_async(self.analyze_move)(
                position_before, move_uci, move_san, position_after
            )
            
            # Send move data to group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'chess_move',
                    'move': move_data,
                    'player': 'user'
                }
            )
            
            # Generate AI response after a short delay
            await self.generate_ai_move()
            
        except Exception as e:
            logger.error(f"Error processing move: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not process your move'
            }))
    
    async def process_chat(self, data):
        """Process a chat message from the player"""
        try:
            message = data.get('message')
            
            # Get game data for context
            game_obj = await database_sync_to_async(self.get_game_object)()
            
            # Process message and generate response
            response = await database_sync_to_async(
                self.generate_chat_response
            )(message, game_obj)
            
            # Send chat message to group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'chat_message',
                    'user_message': message,
                    'ai_response': response
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not process your message'
            }))
    
    async def process_hint_request(self):
        """Process a hint request from the player"""
        try:
            # Get game data
            game_obj = await database_sync_to_async(self.get_game_object)()
            
            # Generate hint
            hint = await database_sync_to_async(self.generate_hint)(game_obj)
            
            # Send hint to group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'hint_message',
                    'hint': hint
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not generate hint'
            }))
    
    async def reset_game(self):
        """Reset the game to the starting position"""
        try:
            # Reset game in database
            await database_sync_to_async(self.reset_game_in_db)()
            
            # Send reset event to group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_reset',
                    'message': 'Game has been reset'
                }
            )
            
        except Exception as e:
            logger.error(f"Error resetting game: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not reset the game'
            }))
    
    async def generate_ai_move(self):
        """Generate and send AI move"""
        try:
            # Get game data
            game_obj = await database_sync_to_async(self.get_game_object)()
            
            # Generate AI move
            ai_move_data = await database_sync_to_async(
                self.create_ai_move
            )(game_obj)
            
            if ai_move_data:
                # Send AI move to group
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'chess_move',
                        'move': ai_move_data,
                        'player': 'ai'
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating AI move: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Could not generate AI move'
            }))
    
    # Event handlers for channel layer
    
    async def chess_move(self, event):
        """Handler for chess move events"""
        await self.send(text_data=json.dumps({
            'type': 'move',
            'move': event['move'],
            'player': event['player']
        }))
    
    async def chat_message(self, event):
        """Handler for chat message events"""
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'user_message': event['user_message'],
            'ai_response': event['ai_response']
        }))
    
    async def hint_message(self, event):
        """Handler for hint message events"""
        await self.send(text_data=json.dumps({
            'type': 'hint',
            'hint': event['hint']
        }))
    
    async def game_reset(self, event):
        """Handler for game reset events"""
        await self.send(text_data=json.dumps({
            'type': 'reset',
            'message': event['message']
        }))
    
    # Synchronous methods for database operations
    
    @database_sync_to_async
    def user_has_game_access(self):
        """Check if user has access to this game"""
        try:
            return Game.objects.filter(
                id=self.game_id, 
                user=self.user
            ).exists()
        except Exception:
            return False
    
    def get_game_object(self):
        """Get the Game object from the database"""
        return Game.objects.get(id=self.game_id)
    
    def get_game_data(self):
        """Get the current game state data"""
        game = Game.objects.get(id=self.game_id)
        moves = Move.objects.filter(game=game).order_by('move_number')
        
        # Convert moves to a list of dictionaries
        moves_data = []
        for move in moves:
            moves_data.append({
                'number': move.move_number,
                'san': move.move_san,
                'uci': move.move_uci,
                'player': move.player,
                'eval': move.eval_score,
                'quality': move.quality,
                'feedback': move.feedback
            })
        
        return {
            'type': 'game_state',
            'position': game.fen_position,
            'moves': moves_data,
            'opening': {
                'id': game.opening.id,
                'name': game.opening.name,
                'eco_code': game.opening.eco_code
            }
        }
    
    def analyze_move(self, position_before, move_uci, move_san, position_after):
        """Analyze a user's move and save to database"""
        game = Game.objects.get(id=self.game_id)
        
        # Initialize analysis services
        stockfish = StockfishEngine()
        feedback_gen = FeedbackGenerator(stockfish)
        
        # Analyze the move
        print("Analyzing move using Stockfish 2")
        eval_score, classification, reason = stockfish.analyze_move(
            position_before, move_uci
        )
        
        # Generate detailed feedback
        feedback = feedback_gen.generate_move_feedback(
            position_before, move_uci, classification, game.opening
        )
        
        # Generate improvement suggestion if needed
        improvement = ""
        if classification not in ["best", "excellent", "good"]:
            improvement = feedback_gen.suggest_improvement(
                position_before, classification
            )
        
        # Save the move to database
        move_obj = Move.objects.create(
            game=game,
            move_number=self.get_next_move_number(game),
            move_uci=move_uci,
            move_san=move_san,
            position_before=position_before,
            position_after=position_after,
            player='user',
            eval_score=eval_score,
            is_mistake=classification in ["mistake", "blunder"],
            quality=classification,
            feedback=feedback,
            improvement_suggestion=improvement
        )
        
        # Update the game state
        game.fen_position = position_after
        game.save()
        
        # Prepare response data
        move_data = {
            'id': move_obj.id,
            'number': move_obj.move_number,
            'san': move_san,
            'uci': move_uci,
            'eval': eval_score,
            'classification': classification,
            'feedback': feedback,
            'improvement': improvement
        }
        
        return move_data
    
    def create_ai_move(self, game):
        """Create and save an AI move"""
        # Initialize the chess board
        board = chess.Board(game.fen_position)
        
        # Initialize services
        stockfish = StockfishEngine()
        feedback_gen = FeedbackGenerator(stockfish)
        
        # Check if game is over
        if board.is_game_over():
            return None
        
        from .views import generate_ai_move
        
        # Generate AI move
        ai_move, san_move, evaluation = generate_ai_move(
            board, game.opening, game.ai_strength
        )
        
        if not ai_move:
            return None
            
        # Apply the move to the board
        position_before = game.fen_position
        board.push(ai_move)
        position_after = board.fen()
        
        # Generate feedback for the AI move
        feedback = feedback_gen.generate_move_feedback(
            position_before, ai_move.uci(), "best", game.opening
        )
        
        # Save the move to database
        move_obj = Move.objects.create(
            game=game,
            move_number=self.get_next_move_number(game),
            move_uci=ai_move.uci(),
            move_san=san_move,
            position_before=position_before,
            position_after=position_after,
            player='ai',
            eval_score=evaluation,
            quality='best',  # AI always plays best moves
            feedback=feedback
        )
        
        # Update the game state
        game.fen_position = position_after
        game.save()
        
        # Prepare response data
        move_data = {
            'id': move_obj.id,
            'number': move_obj.move_number,
            'san': san_move,
            'uci': ai_move.uci(),
            'eval': evaluation,
            'classification': 'best',
            'feedback': feedback
        }
        
        return move_data
    
    def generate_chat_response(self, message, game):
        """Generate a response to a chat message"""
        # Initialize services
        nlp = ChessNLP()
        stockfish = StockfishEngine()
        
        # Analyze message and generate response
        analysis = nlp.analyze_message(
            message, 
            board_fen=game.fen_position, 
            opening=game.opening
        )
        
        response = nlp.generate_response(
            analysis, 
            stockfish_engine=stockfish,
            game=game
        )
        
        return response
    
    def generate_hint(self, game):
        """Generate a hint for the current position"""
        # Initialize services
        stockfish = StockfishEngine()
        
        # Get Stockfish suggestions
        top_moves = stockfish.get_top_moves(game.fen_position, 1)
        board = chess.Board(game.fen_position)
        
        if top_moves:
            best_move = top_moves[0]
            hint = (
                f"I recommend playing {best_move['san']}. This is currently the strongest move."
            )  # noqa: E501
            
            # Check if we're still in the opening book
            if game.in_opening_book:
                opening = game.opening
                pgn = opening.pgn_moves
                pgn_game = chess.pgn.read_game(io.StringIO(pgn))
                
                node = pgn_game
                while node.variations and str(node.board()) != str(board):
                    node = node.variations[0]
                
                # If we're still in the opening book
                if node.variations:
                    next_move = node.variations[0].move
                    san_move = board.san(next_move)
                    
                    # If the book move matches the engine move, mention it
                    if san_move == best_move['san']:
                        hint = (
                            f"I recommend playing {san_move}. This is the main line of the {opening.name}."
                        )  # noqa: E501
                    else:
                        hint = (
                            f"The main line continues with {san_move}, but {best_move['san']} is also a strong alternative."
                        )  # noqa: E501
        else:
            hint = "Look for pieces that are undefended or could be developed to better squares."
        
        return hint
    
    def reset_game_in_db(self):
        """Reset the game in the database"""
        game = Game.objects.get(id=self.game_id)
        
        # Reset game to starting position
        game.fen_position = (
            'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        )
        game.in_opening_book = True
        game.save()
        
        # Delete all moves
        Move.objects.filter(game=game).delete()
        
        return game
    
    def get_next_move_number(self, game):
        """Get the next move number for a game"""
        last_move = Move.objects.filter(
            game=game
        ).order_by('-move_number').first()
        return 1 if last_move is None else last_move.move_number + 1 