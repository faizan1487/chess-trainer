from django.contrib import admin
from .models import (
    Opening, Game, Move, UserProfile, 
    OpeningPosition, UserProgress, Challenge, UserChallenge
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'elo_rating', 'games_played', 'games_won')
    search_fields = ('user__username',)

@admin.register(Opening)
class OpeningAdmin(admin.ModelAdmin):
    list_display = ('name', 'eco_code', 'difficulty')
    search_fields = ('name', 'eco_code')
    list_filter = ('difficulty',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('user', 'opening', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'user_color')
    search_fields = ('user__username', 'opening__name')
    date_hierarchy = 'created_at'

@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('game', 'move_number', 'move_san', 'player', 'is_mistake', 'created_at')
    list_filter = ('player', 'is_mistake')
    search_fields = ('game__user__username', 'move_san')
    date_hierarchy = 'created_at'

# Register your models with the admin site
admin.site.register(OpeningPosition)
admin.site.register(UserProgress)
admin.site.register(Challenge)
admin.site.register(UserChallenge)
