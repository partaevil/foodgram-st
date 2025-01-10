from rest_framework import serializers
from core.models import (Recipe, Ingredient, RecipeIngredient,
                         UserProfile)
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
            return obj.subscribers.filter(user=request.user).exists()
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
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.author.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context)
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(source='recipe_ingredients',
                                               many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time')

    def validate(self, data):
        ingredients = self.context.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                "At least one ingredient is required.")

        unique_ids = set()
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')

            if not ingredient_id or not isinstance(ingredient_id, int):
                raise serializers.ValidationError(
                    "Each ingredient must have a valid 'id'.")
            if ingredient_id in unique_ids:
                raise serializers.ValidationError(
                    "Duplicate ingredients are not allowed.")
            unique_ids.add(ingredient_id)

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
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = super.create(
            author=self.context['request'].user,
            **validated_data
        )

        self.create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        instance.recipe_ingredients.all().delete()

        self.create_recipe_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def create_recipe_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
