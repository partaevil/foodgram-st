from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from core.models import Recipe, Ingredient, ShoppingCart, Favorite, RecipeIngredient
from .serializers import RecipeSerializer, IngredientSerializer
from core.serializers import RecipeShortSerializer
from django.shortcuts import get_object_or_404
import hashlib
import csv
from django.db.models import Sum
from django.http import HttpResponse

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Ingredient.objects.all().order_by('name')
        name = self.request.query_params.get('name', None)
        if name:
            # Case-insensitive search by ingredient name
            queryset = queryset.filter(name__icontains=name)
        return queryset

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Recipe.objects.all().order_by('id')
        params = self.request.query_params

        if self.request.user.is_authenticated:
            # Filter by shopping cart
            is_in_shopping_cart = params.get('is_in_shopping_cart')
            if is_in_shopping_cart is not None:
                if is_in_shopping_cart == '1':
                    queryset = queryset.filter(in_carts_of__user=self.request.user)
                elif is_in_shopping_cart == '0':
                    queryset = queryset.exclude(in_carts_of__user=self.request.user)

            # Filter by favorites
            is_favorited = params.get('is_favorited')
            if is_favorited is not None:
                if is_favorited == '1':
                    queryset = queryset.filter(favorited_by__user=self.request.user)
                elif is_favorited == '0':
                    queryset = queryset.exclude(favorited_by__user=self.request.user)

        return queryset.distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        hash_object = hashlib.md5(str(recipe.id).encode())
        short_hash = hash_object.hexdigest()[:3]
        short_link = f"https://localhost/s/{short_hash}"
        return Response({'short-link': short_link})

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Recipe already in shopping cart'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            shopping_cart = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            )
            if shopping_cart.exists():
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Recipe not in shopping cart'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Recipe already in favorites'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Recipe not in favorites'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_carts_of__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Amount', 'Unit'])
        
        for item in ingredients:
            writer.writerow([
                item['ingredient__name'],
                item['total_amount'],
                item['ingredient__measurement_unit']
            ])
        
        return response