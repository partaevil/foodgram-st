from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from core.models import Recipe, Ingredient
from .serializers import RecipeSerializer, IngredientSerializer
from django.shortcuts import get_object_or_404
import hashlib

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None  

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name', None)
        if name:
            # Case-insensitive search by ingredient name
            queryset = queryset.filter(name__icontains=name)
        return queryset

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        # Create a simple hash of the recipe ID
        hash_object = hashlib.md5(str(recipe.id).encode())
        short_hash = hash_object.hexdigest()[:3]
        short_link = f"https://localhost/s/{short_hash}"
        return Response({'short-link': short_link})