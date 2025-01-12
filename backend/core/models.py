from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profiles',
        verbose_name='User'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Name'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Measurement Unit'
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Author'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Name'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Image'
    )
    text = models.TextField(
        verbose_name='Description'
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cooking Time (minutes)'
    )
    date_published = models.DateTimeField(
        default=now,
        verbose_name='Date Published'
    )

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-date_published']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Ingredient'
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Amount'
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Recipe Ingredient'
        verbose_name_plural = 'Recipe Ingredients'

    def __str__(self):
        return f'{self.amount} {self.ingredient.name} in {self.recipe.name}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Recipe'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'

    def __str__(self):
        return f'{self.user.username} favors {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping_carts',
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_carts',
        on_delete=models.CASCADE,
        verbose_name='Recipe'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'

    def __str__(self):
        return f'{self.user.username} has {self.recipe.name} in cart'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    author = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Author'
    )
    recipes_count = models.IntegerField(
        default=0,
        verbose_name='Number of Recipes'
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['id']

    def __str__(self):
        return f'{self.user.username} subscribes to {self.author.username}'
