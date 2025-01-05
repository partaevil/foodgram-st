from rest_framework import serializers
from core.models import Recipe, Ingredient, RecipeIngredient
from users.serializers import UserSerializer
from core.serializers import Base64ImageField

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

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
                 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_carts_of.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        ingredients_data = self.context.get('ingredients', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
            
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = self.context.get('ingredients', [])
        instance.recipe_ingredients.all().delete()
        
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            
        return super().update(instance, validated_data)

