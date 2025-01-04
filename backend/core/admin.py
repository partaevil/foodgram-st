from django.contrib import admin
from .models import (
    UserProfile, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription
)

# Register UserProfile
admin.site.register(UserProfile)

# Customize and register Ingredient
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')

admin.site.register(Ingredient, IngredientAdmin)

# Customize and register Recipe
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    list_filter = ('author', 'cooking_time')
    search_fields = ('name', 'text')

admin.site.register(Recipe, RecipeAdmin)

# Customize and register RecipeIngredient
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')

admin.site.register(RecipeIngredient, RecipeIngredientAdmin)

# Register Favorite
admin.site.register(Favorite)

# Register ShoppingCart
admin.site.register(ShoppingCart)

# Register Subscription
admin.site.register(Subscription)