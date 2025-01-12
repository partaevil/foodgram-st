from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied
from core.models import (Recipe, Ingredient, Subscription, UserProfile,
                         ShoppingCart, Favorite, RecipeIngredient)
import csv
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model, authenticate
from .serializers import (RecipeShortSerializer, UserSerializer,
                          UserCreateSerializer,
                          PasswordChangeSerializer, AvatarSerializer,
                          SubscriptionSerializer, RecipeSerializer,
                          IngredientSerializer)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

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
        queryset = Recipe.objects.all().order_by('-date_published')
        params = self.request.query_params

        # Filter by author
        author_id = params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        if self.request.user.is_authenticated:
            # Filter by shopping cart
            is_in_shopping_cart = params.get('is_in_shopping_cart')
            if is_in_shopping_cart is not None:
                if is_in_shopping_cart == '1':
                    queryset = queryset.filter(
                        shopping_carts__user=self.request.user)
                elif is_in_shopping_cart == '0':
                    queryset = queryset.exclude(
                        shopping_carts__user=self.request.user)

            # Filter by favorites
            is_favorited = params.get('is_favorited')
            if is_favorited is not None:
                if is_favorited == '1':
                    queryset = queryset.filter(
                        favorites__user=self.request.user)
                elif is_favorited == '0':
                    queryset = queryset.exclude(
                        favorites__user=self.request.user)

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context

    def perform_update(self, serializer):
        if self.get_object().author != self.request.user:
            raise PermissionDenied(
                "You do not have permission to edit this recipe.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                "You do not have permission to delete this recipe.")
        instance.delete()

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        if Recipe.objects.filter(id=pk).exists():
            short_link_url = request.build_absolute_uri(
                reverse('short-link', args=[pk])
            )
            return Response({'short-link': short_link_url})
        return Response(
            {'errors': 'Recipe with this id not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    def handle_add_or_remove(self, request, pk, model, error_message):
        """Function for adding or removing recipes"""
        recipe = self.get_object()

        if request.method == 'POST':
            instance, created = model.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                get_object_or_404(
                    model,
                    user=request.user,
                    recipe=recipe
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response(
                    {'errors': f'Recipe not in {model.__name__.lower()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        return self.handle_add_or_remove(
            request=request,
            pk=pk,
            model=ShoppingCart,
            error_message='Recipe already in shopping cart'
        )

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        return self.handle_add_or_remove(
            request=request,
            pk=pk,
            model=Favorite,
            error_message='Recipe already in favorites'
        )

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_cart.csv"'

        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Amount', 'Unit'])

        for item in ingredients:
            writer.writerow([
                item['ingredient__name'].capitalize(),
                item['total_amount'],
                item['ingredient__measurement_unit']
            ])

        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        # Allow list and retrieve actions for all users
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        # Require authentication for all other actions
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data['current_password']):
                user.set_password(serializer.data['new_password'])
                user.save()
                return Response({'status': 'password set'})
            return Response({'current_password': ['Wrong password']},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        if request.method == 'DELETE':
            if profile.avatar:
                profile.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'No avatar to delete'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AvatarSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.select_related(
            'author', 'author__profiles'
        ).prefetch_related('author__recipes')

        authors = [subscription.author for subscription in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'errors': 'You cannot subscribe to yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author,
                defaults={'recipes_count': author.recipes.count()}
            )

            if not created:
                return Response(
                    {'errors': 'You are already subscribed to this author'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=request.user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        if 'logout' in request.path:
            if request.user.is_authenticated:
                request.user.auth_token.delete()
                return Response(
                    {'status': 'Logged out successfully'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'User is not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No user found with this email address'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=user.username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key,
            'user_id': user.id,
            'email': user.email,
        })
