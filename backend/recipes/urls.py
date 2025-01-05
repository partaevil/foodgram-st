from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
]