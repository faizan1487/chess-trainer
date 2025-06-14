from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('openings/', views.opening_selection, name='opening_selection'),
    
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
    
    # Lesson System URLs
    path('lessons/', views.lesson_list, name='lesson_list'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/verify-move/', views.verify_move, name='verify_move'),
    path('lesson/<int:lesson_id>/start-test/', views.start_test, name='start_test'),
    path('test/<int:test_id>/submit-move/', views.submit_test_move, name='submit_test_move'),
    path('reviews/due/', views.get_due_reviews, name='get_due_reviews'),
]