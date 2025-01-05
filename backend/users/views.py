from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from core.models import Subscription
from .serializers import (UserSerializer, UserCreateSerializer,
                         PasswordChangeSerializer, AvatarSerializer,
                         SubscriptionSerializer)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate

User = get_user_model()

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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
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

    @action(detail=False, methods=['put', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        if request.method == 'DELETE':
            if hasattr(request.user, 'profile'):
                request.user.profile.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = AvatarSerializer(request.user.profile,
                                    data=request.data,
                                    partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user).select_related(
            'author', 'author__profile').prefetch_related('author__recipes')
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
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
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=request.user,
                author=author
            ).first()
            
            if not subscription:
                return Response(
                    {'errors': 'You are not subscribed to this author'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        if 'logout' in request.path:
            if request.user.is_authenticated:
                request.user.auth_token.delete()
                return Response({'status': 'Logged out successfully'}, status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=400)

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

    