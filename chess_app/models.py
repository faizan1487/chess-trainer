from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    elo_rating = models.IntegerField(default=1200)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username

class Opening(models.Model):
    name = models.CharField(max_length=100)
    eco_code = models.CharField(max_length=10, blank=True, null=True)
    pgn_moves = models.TextField()
    description = models.TextField()
    difficulty = models.IntegerField(default=1)  # 1-5 scale
    
    # New fields for enhanced Opening model
    is_popular = models.BooleanField(default=False)
    for_white = models.BooleanField(default=True)  # True for White, False for Black
    category = models.CharField(max_length=50, blank=True, null=True) # e.g., "Open Game", "Semi-Open", etc.
    main_line = models.TextField(blank=True, null=True)  # Optional field for the main line PGN
    parent_opening = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='variations')
    
    def __str__(self):
        return self.name

class OpeningPosition(models.Model):
    """
    Model to store important positions within an opening with annotations.
    """
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE, related_name='positions')
    fen_position = models.CharField(max_length=100)
    move_san = models.CharField(max_length=10, blank=True, null=True)  # SAN notation of the move that led to this position
    move_number = models.IntegerField()
    annotation = models.TextField(blank=True, null=True)  # Explanation of the position
    is_critical = models.BooleanField(default=False)  # Whether this is a key position
    
    def __str__(self):
        return f"{self.opening.name} - Move {self.move_number}: {self.move_san or 'Initial'}"
    
    class Meta:
        ordering = ['opening', 'move_number']
        unique_together = ['opening', 'fen_position']

class Game(models.Model):
    GAME_STATUS_CHOICES = [
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=GAME_STATUS_CHOICES, default='ONGOING')
    fen_position = models.CharField(max_length=100, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    user_color = models.CharField(max_length=5, default='white')
    
    # New fields
    ai_strength = models.IntegerField(default=15)  # Stockfish depth
    in_opening_book = models.BooleanField(default=True)  # Whether we're still in the opening book
    result = models.CharField(max_length=10, blank=True, null=True)  # "1-0", "0-1", "1/2-1/2"
    
    def __str__(self):
        return f"{self.user.username} - {self.opening.name} ({self.created_at.strftime('%Y-%m-%d')})"

class Move(models.Model):
    MOVE_QUALITY_CHOICES = [
        ('best', 'Best Move'),
        ('excellent', 'Excellent Move'),
        ('good', 'Good Move'),
        ('inaccuracy', 'Inaccuracy'),
        ('mistake', 'Mistake'),
        ('blunder', 'Blunder'),
        ('normal', 'Normal')
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')
    move_number = models.IntegerField()
    move_uci = models.CharField(max_length=10)
    move_san = models.CharField(max_length=10)
    position_before = models.CharField(max_length=100)
    position_after = models.CharField(max_length=100)
    player = models.CharField(max_length=10)  # 'user' or 'ai'
    eval_score = models.FloatField(null=True, blank=True)
    
    # Updated fields
    is_mistake = models.BooleanField(default=False)
    quality = models.CharField(max_length=10, choices=MOVE_QUALITY_CHOICES, default='normal')
    feedback = models.TextField(blank=True, null=True)
    improvement_suggestion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['move_number']
        
    def __str__(self):
        return f"{self.game} - Move {self.move_number}: {self.move_san}"

class UserProgress(models.Model):
    """
    Model to track user's progress in learning each opening.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE)
    games_played = models.IntegerField(default=0)
    mastery_level = models.IntegerField(default=0)  # 0-100 scale
    last_played = models.DateTimeField(auto_now=True)
    
    # Statistics
    avg_accuracy = models.FloatField(default=0.0)  # Average move accuracy 0-100
    best_accuracy = models.FloatField(default=0.0)  # Best game accuracy 0-100
    common_mistakes = models.TextField(blank=True, null=True)  # JSON field to store common mistake positions
    
    class Meta:
        unique_together = ['user', 'opening']
        
    def __str__(self):
        return f"{self.user.username} - {self.opening.name} (Mastery: {self.mastery_level}%)"

class Challenge(models.Model):
    """
    Model for specific chess position challenges.
    """
    DIFFICULTY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Easy'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert')
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    fen_position = models.CharField(max_length=100)
    solution_moves = models.TextField()  # PGN of solution moves
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE, related_name='challenges')
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class UserChallenge(models.Model):
    """
    Model to track user progress on challenges.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    is_solved = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    solved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'challenge']
        
    def __str__(self):
        status = "Solved" if self.is_solved else "Unsolved"
        return f"{self.user.username} - {self.challenge.title} ({status})"
