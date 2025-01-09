from django.shortcuts import get_object_or_404, redirect
from .models import ShortLink
from django.http import Http404


def short_link_redirect(request, hash):
    try:
        short_link = get_object_or_404(ShortLink, hash=hash)
        return redirect(f'/recipes/{short_link.recipe.id}')
    except Http404:
        # Just send them into main page
        return redirect('/recipes')
