from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Recipe, Ingredient, ShoppingCart, Favorite, RecipeIngredient, Subscription

User = get_user_model()

class RecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test ingredient
        self.ingredient = Ingredient.objects.create(
            name='Test Ingredient',
            measurement_unit='g'
        )
        
        # Create test recipe
        self.recipe = Recipe.objects.create(
            author=self.user,
            name='Test Recipe',
            text='Test description',
            cooking_time=30
        )
        
        # Create recipe ingredient
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=100
        )

        # Create test image
        self.image_content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==')
        self.image = SimpleUploadedFile(
            "test.png",
            self.image_content,
            content_type="image/png"
        )

    def test_recipe_list(self):
        """Test getting list of recipes"""
        url = reverse('recipe-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertTrue('count' in response.data)
        
    def test_recipe_detail(self):
        """Test getting single recipe details"""
        url = reverse('recipe-detail', args=[self.recipe.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Recipe')
        
    def test_create_recipe(self):
        """Test creating a new recipe"""
        url = reverse('recipe-list')
        payload = {
            'name': 'New Recipe',
            'text': 'New description',
            'cooking_time': 45,
            'ingredients': [{'id': self.ingredient.id, 'amount': 200}],
            'image': f"data:image/png;base64,{base64.b64encode(self.image_content).decode()}"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Recipe')
        
    def test_update_recipe(self):
        """Test updating a recipe"""
        url = reverse('recipe-detail', args=[self.recipe.id])
        payload = {
            'name': 'Updated Recipe',
            'text': 'Updated description',
            'cooking_time': 60,
            'ingredients': [{'id': self.ingredient.id, 'amount': 150}]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Recipe')
        
    def test_delete_recipe(self):
        """Test deleting a recipe"""
        url = reverse('recipe-detail', args=[self.recipe.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
    def test_favorite_recipe(self):
        """Test adding and removing recipe from favorites"""
        # Add to favorites
        url = reverse('recipe-favorite', args=[self.recipe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if it's in favorites
        list_url = reverse('recipe-list')
        response = self.client.get(list_url)
        self.assertTrue(response.data['results'][0]['is_favorited'])
        
        # Remove from favorites
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
    def test_shopping_cart(self):
        """Test adding and removing recipe from shopping cart"""
        # Add to shopping cart
        url = reverse('recipe-shopping-cart', args=[self.recipe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if it's in shopping cart
        list_url = reverse('recipe-list')
        response = self.client.get(list_url)
        self.assertTrue(response.data['results'][0]['is_in_shopping_cart'])
        
        # Download shopping cart
        download_url = reverse('recipe-download-shopping-cart')
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        
        # Remove from shopping cart
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_recipe_link(self):
        """Test getting short link for recipe"""
        url = reverse('recipe-get-link', args=[self.recipe.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('short-link' in response.data)


class IngredientAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ingredient = Ingredient.objects.create(
            name='Test Ingredient',
            measurement_unit='g'
        )
        
    def test_ingredient_list(self):
        """Test getting list of ingredients"""
        url = reverse('ingredient-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
    def test_ingredient_detail(self):
        """Test getting single ingredient details"""
        url = reverse('ingredient-detail', args=[self.ingredient.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Ingredient')
        
    def test_ingredient_search(self):
        """Test searching ingredients by name"""
        url = reverse('ingredient-list')
        Ingredient.objects.create(name='Another Ingredient', measurement_unit='ml')
        response = self.client.get(url, {'name': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Ingredient')

class RecipeSecurityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create two test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        
        # Create test ingredient
        self.ingredient = Ingredient.objects.create(
            name='Test Ingredient',
            measurement_unit='g'
        )
        
        # Create test image
        self.image_content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==')
        self.image = SimpleUploadedFile(
            "test.png",
            self.image_content,
            content_type="image/png"
        )

        # Create recipe for user1
        self.recipe1 = Recipe.objects.create(
            author=self.user1,
            name='User1 Recipe',
            text='Test description',
            cooking_time=30,
            image=self.image
        )
        
        RecipeIngredient.objects.create(
            recipe=self.recipe1,
            ingredient=self.ingredient,
            amount=100
        )

    def test_unauthorized_user_cannot_create_recipe(self):
        """Test that unauthorized users cannot create recipes"""
        self.client.logout()
        url = reverse('recipe-list')
        payload = {
            'name': 'Unauthorized Recipe',
            'text': 'Description',
            'cooking_time': 30,
            'ingredients': [{'id': self.ingredient.id, 'amount': 100}],
            'image': f"data:image/png;base64,{base64.b64encode(self.image_content).decode()}"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_edit_others_recipe(self):
        """Test that a user cannot edit another user's recipe"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-detail', args=[self.recipe1.id])
        payload = {
            'name': 'Modified Recipe',
            'text': 'Modified description',
            'cooking_time': 45,
            'ingredients': [{'id': self.ingredient.id, 'amount': 150}]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify recipe wasn't changed
        self.recipe1.refresh_from_db()
        self.assertEqual(self.recipe1.name, 'User1 Recipe')

    def test_user_cannot_delete_others_recipe(self):
        """Test that a user cannot delete another user's recipe"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-detail', args=[self.recipe1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify recipe still exists
        self.assertTrue(Recipe.objects.filter(id=self.recipe1.id).exists())

    def test_invalid_recipe_creation(self):
        """Test validation errors during recipe creation"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('recipe-list')
        
        # Test missing required fields
        payload = {
            'name': 'Invalid Recipe'
            # Missing other required fields
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid cooking time
        payload = {
            'name': 'Invalid Recipe',
            'text': 'Description',
            'cooking_time': -1,  # Invalid value
            'ingredients': [{'id': self.ingredient.id, 'amount': 100}],
            'image': f"data:image/png;base64,{base64.b64encode(self.image_content).decode()}"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_favorite(self):
        """Test adding the same recipe to favorites twice"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-favorite', args=[self.recipe1.id])
        
        # First addition should succeed
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second addition should fail
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_shopping_cart(self):
        """Test adding the same recipe to shopping cart twice"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-shopping-cart', args=[self.recipe1.id])
        
        # First addition should succeed
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second addition should fail
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_nonexistent_favorite(self):
        """Test removing a recipe from favorites that wasn't added"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-favorite', args=[self.recipe1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_nonexistent_shopping_cart(self):
        """Test removing a recipe from shopping cart that wasn't added"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('recipe-shopping-cart', args=[self.recipe1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_author(self):
        """Test filtering recipes by author"""
        # Create additional recipe for user2
        Recipe.objects.create(
            author=self.user2,
            name='User2 Recipe',
            text='Test description',
            cooking_time=45,
            image=self.image
        )
        
        url = reverse('recipe-list')
        response = self.client.get(url, {'author': self.user1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'User1 Recipe')

    def test_invalid_ingredient_amount(self):
        """Test creating recipe with invalid ingredient amount"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('recipe-list')
        payload = {
            'name': 'Invalid Recipe',
            'text': 'Description',
            'cooking_time': 30,
            'ingredients': [{'id': self.ingredient.id, 'amount': -1}],  # Invalid amount
            'image': f"data:image/png;base64,{base64.b64encode(self.image_content).decode()}"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)