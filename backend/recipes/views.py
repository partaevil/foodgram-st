from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from core.models import Recipe 
from .serializers import RecipeSerializer
from django.shortcuts import get_object_or_404
import hashlib

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