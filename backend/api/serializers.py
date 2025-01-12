import logging
from django.db import transaction
from rest_framework import serializers
from core.models import (Recipe, Ingredient, RecipeIngredient,
                         UserProfile, Subscription)
from core.serializers import Base64ImageField
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class AvatarMixin:
    def get_avatar(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('avatar',)


class UserSerializer(serializers.ModelSerializer, AvatarMixin):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def validate_email(self, value):
        """Ensure the email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.')
        return value

    def validate_password(self, value):
        """Ensure the password meets strength requirements."""
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Ensure the password meets strength requirements."""
        validate_password(value)
        return value


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = UserProfile
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'ingredient' in data:
            # from {'ingredient': {'id': 2}, 'amount': 2}
            # to {'id': 2, 'amount': 2}
            ingredient_id = data['ingredient'].get('id')
            return {
                'ingredient': {'id': ingredient_id},
                'amount': data['amount']
            }
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time')

    def validate(self, data):
        ingredients = data.get('recipe_ingredients', [])

        if not ingredients:
            raise serializers.ValidationError(
                "At least one ingredient is required.")

        ingredient_ids = {ingredient.get('id') for ingredient in ingredients}
        logging.getLogger("django").info(ingredients)
        logging.getLogger("django").info(ingredient_ids)
        if None in ingredient_ids:
            raise serializers.ValidationError(
                "Each ingredient must have a valid 'id'."
            )

        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        logging.getLogger("django").info(Ingredient.objects.all())
        logging.getLogger("django").info(f"Found existing ingredients: {
            list(existing_ingredients.values())}")
        if len(existing_ingredients) != len(ingredient_ids):
            missing_ids = ingredient_ids - \
                set(existing_ingredients.values_list('id', flat=True))
            raise serializers.ValidationError(
                f"Ingredients with ids {missing_ids} do not exist."
            )

        if len(ingredient_ids) != len(ingredients):
            raise serializers.ValidationError(
                "Duplicate ingredients are not allowed."
            )

        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by_users.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_carts_of_users.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])

        recipe = super().create(
            validated_data
        )
        self.create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        instance.recipe_ingredients.all().delete()

        with transaction.atomic():
            ingredient_ids = {ingredient['id']
                              for ingredient in ingredients_data}
            existing_ingredients = Ingredient.objects.filter(
                id__in=ingredient_ids)

            if len(existing_ingredients) != len(ingredient_ids):
                raise serializers.ValidationError(
                    "Some ingredients do not exist in the database."
                )

            instance.recipe_ingredients.all().delete()

            # Add new ingredients
            self.create_recipe_ingredients(instance, ingredients_data)

            # Update the main instance
            return super().update(instance, validated_data)

    def create_recipe_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )
