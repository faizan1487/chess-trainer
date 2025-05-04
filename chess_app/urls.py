from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('openings/', views.opening_selection, name='opening_selection'),
    path('game/<int:opening_id>/', views.game, name='game'),
    
    # Authentication
    path('register/', views.register, name='register'),
    
    # API endpoints
    path('api/game/<int:game_id>/move/', views.make_move, name='make_move'),
    path('api/game/<int:game_id>/ai_move/', views.get_ai_move, name='get_ai_move'),
    path('api/game/<int:game_id>/hint/', views.get_hint, name='get_hint'),
    path('api/game/<int:game_id>/chat/', views.chat, name='chat'),
    path('api/game/<int:game_id>/reset/', views.reset_game, name='reset_game'),
    path('api/ask_question/', views.ask_question, name='ask_question'),
    path('api/game/<int:game_id>/move_history/', views.get_move_history, name='get_move_history'),
    
    # Opening Explorer
    path('explorer/', views.opening_explorer, name='opening_explorer'),
    path('explorer/<int:opening_id>/', views.opening_explorer, name='opening_explorer_detail'),
    
    # User Profile and Progress
    path('profile/', views.user_profile, name='user_profile'),
    
    # Challenges
    path('challenges/', views.challenges, name='challenges'),
    path('challenges/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('api/challenges/<int:challenge_id>/verify/', 
         views.verify_challenge_solution, name='verify_challenge_solution'),
] 