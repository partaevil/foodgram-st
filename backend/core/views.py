from django.shortcuts import redirect
from .models import Recipe
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import HttpResponseNotFound


@api_view(('GET',))
@permission_classes((AllowAny,))
def short_link_redirect(request, pk):
    if Recipe.objects.filter(id=pk).exists():
        return redirect(f'/recipes/{pk}')
    return HttpResponseNotFound(
        f'Recipe with id {pk} not found. \
            Recipe deleted or not yet created',
    )
