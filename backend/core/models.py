from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"

class Recipe(models.Model):
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField()
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='ingredient_recipes', on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.amount} {self.ingredient.measurement_unit} of {self.ingredient.name} in {self.recipe.name}"

class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorites', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='favorited_by', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} favors {self.recipe.name}"

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, related_name='shopping_carts', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='in_carts_of', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} has {self.recipe.name} in cart"

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='subscribers', on_delete=models.CASCADE)
    recipes_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'author')

    def __str__(self):
        return f"{self.user.username} subscribes to {self.author.username}"