from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("User")
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=_("Avatar")
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name=_("Name")
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name=_("Measurement Unit")
    )

    class Meta:
        verbose_name = _("Ingredient")
        verbose_name_plural = _("Ingredients")
    
    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"

class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name=_("Author")
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_("Name")
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name=_("Image")
    )
    text = models.TextField(
        verbose_name=_("Description")
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Cooking Time (minutes)")
    )
    date_published = models.DateTimeField(
        default=now, 
        verbose_name=_("Date Published")
    )

    class Meta:
        verbose_name = _("Recipe")
        verbose_name_plural = _("Recipes")
    
    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name=_("Recipe")
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_recipes',
        on_delete=models.CASCADE,
        verbose_name=_("Ingredient")
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Amount")
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = _("Recipe Ingredient")
        verbose_name_plural = _("Recipe Ingredients")
    
    def __str__(self):
        return f"{self.amount} {self.ingredient.measurement_unit} of {self.ingredient.name} in {self.recipe.name}"

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorited_by',
        on_delete=models.CASCADE,
        verbose_name=_("Recipe")
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")
    
    def __str__(self):
        return f"{self.user.username} favors {self.recipe.name}"

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping_carts',
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_carts_of',
        on_delete=models.CASCADE,
        verbose_name=_("Recipe")
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = _("Shopping Cart")
        verbose_name_plural = _("Shopping Carts")
    
    def __str__(self):
        return f"{self.user.username} has {self.recipe.name} in cart"

class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    author = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name=_("Author")
    )
    recipes_count = models.IntegerField(
        default=0,
        verbose_name=_("Number of Recipes")
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
    
    def __str__(self):
        return f"{self.user.username} subscribes to {self.author.username}"
