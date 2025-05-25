from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('game/<int:opening_id>/', views.game, name='game'),
    path('openings/', views.opening_selection, name='opening_selection'),
    path('opening/<int:opening_id>/', views.opening_explorer, name='opening_explorer_detail'),
    path('challenges/', views.challenges, name='challenges'),
    path('challenge/<int:challenge_id>/', 
         views.challenge_detail, name='challenge_detail'),
    path('upload-pgn/', views.upload_pgn, name='upload_pgn'),
    
    # API endpoints
    path('api/game/<int:game_id>/move/', 
         views.make_move, name='make_move'),
    path('api/game/<int:game_id>/ai_move/', 
         views.get_ai_move, name='get_ai_move'),
    path('api/game/<int:game_id>/move_history/', 
         views.get_move_history, name='get_move_history'),
    path('api/game/<int:game_id>/hint/', 
         views.get_hint, name='get_hint'),
    path('api/game/<int:game_id>/reset/', 
         views.reset_game, name='reset_game'),
    path('api/challenges/<int:challenge_id>/verify/', 
         views.verify_challenge_solution, name='verify_challenge_solution'),
    
    # Game Analysis and Opening Recommendations
    path('analyze/', views.analyze_games_view, name='analyze_games'),
    path('api/analyze-games/', 
         views.analyze_games, name='api_analyze_games'),
    path('api/analysis-history/', 
         views.get_analysis_history, name='api_analysis_history'),
] 