from django.shortcuts import redirect
from .models import Recipe
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from django.http import HttpResponseNotFound


@api_view(('GET',))
@permission_classes((AllowAny,))
def short_link_redirect(request, pk):
    # get_object_or_404(Recipe, pk=pk)
    if Recipe.objects.filter(id=pk).exists():
        return redirect(f'/recipes/{pk}')
    return HttpResponseNotFound(
        'Recipe with this id not found.',
    )
