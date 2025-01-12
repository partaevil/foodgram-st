from django.shortcuts import get_object_or_404, redirect
from .models import Recipe
from django.http import Http404


def short_link_redirect(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{pk}')
