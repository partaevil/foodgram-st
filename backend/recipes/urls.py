from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]