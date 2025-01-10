from django.shortcuts import get_object_or_404, redirect
from .models import Recipe
from django.http import Http404


def short_link_redirect(request, pk):
    try:
        recipe = get_object_or_404(Recipe, pk=pk)
        return redirect(f'/recipes/{recipe.id}')
    except Http404:
        # Just send them into main page
        return redirect('/recipes')
