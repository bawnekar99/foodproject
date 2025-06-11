# users/views.py
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from bson import ObjectId
import random
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone 
from .models import Restaurant, User, RestaurantImage
from rest_framework import permissions
from django.shortcuts import get_object_or_404
# Keep all existing imports and add any missing ones

from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    UserOTPSerializer, UserOTPVerifySerializer, UserLocationSerializer, 
    UserProfileUpdateSerializer, RestaurantSerializer,
    RestaurantImageSerializer, RestaurantCreateSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone 
from rest_framework.parsers import MultiPartParser, FormParser
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404
import logging
logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SendUserOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = str(random.randint(100000, 999999))

            try:
                user, created = User.objects.get_or_create(phone=phone, defaults={
                    'is_vendor': False,
                    'username': phone  # required since username is unique in AbstractUser
                })
                user.otp = otp
                user.save()

                print(f"[User OTP] {phone} -> {otp}")
                return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

            except Exception as e:
                print("Database error:", str(e))
                traceback.print_exc()
                return Response({"message": "Database error", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyUserOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']

            try:
                # Just fetch by phone, no extra filters for debugging
                user = User.objects.filter(phone=phone).first()
                if not user:
                    return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

                if user.otp == otp:
                    user.otp = None
                    user.save()
                    tokens = get_tokens_for_user(user)
                    return Response({
                        "message": "OTP verified",
                        "access": tokens['access'],
                        "refresh": tokens['refresh'],
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("DB error:", e)
                traceback.print_exc()
                return Response({"error": "Server error during verification"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateUserLocation(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserLocationSerializer(data=request.data)
        if serializer.is_valid():
            request.user.latitude = serializer.validated_data['latitude']
            request.user.longitude = serializer.validated_data['longitude']
            request.user.save()
            return Response({"message": "Location updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserProfile(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated", "user": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                                                 








# Keep all existing user-related views

# Updated Restaurant Views
class SendRestaurantOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = Restaurant.objects.get(phone=phone)
        except Restaurant.DoesNotExist:
            restaurant = Restaurant.objects.create(
                phone=phone,
                name=f"Restaurant {phone[-4:]}",
                category='Other',
                food_categories='Other',
                address='To be updated',
                city='To be updated',
                state='To be updated',
                pincode='000000',
                latitude=Decimal('0.000000'),
                longitude=Decimal('0.000000'),
            )

        # Generate and update OTP
        otp = str(random.randint(100000, 999999))
        restaurant.otp = otp
        restaurant.otp_created_at = timezone.now()
        restaurant.is_verified = False
        restaurant.save(update_fields=["otp", "otp_created_at", "is_verified"])

        print(f"[Restaurant OTP] {phone}: {otp}")
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)




class VerifyRestaurantOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        otp = request.data.get("otp")
        
        if not phone or not otp:
            return Response({"error": "Phone number and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = Restaurant.objects.get(phone=phone)
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check OTP
        if restaurant.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is expired
        if restaurant.otp_is_expired():
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify restaurant
        restaurant.is_verified = True
        restaurant.otp = None
        restaurant.otp_created_at = None
        
        # Create or get user
        if not restaurant.user:
            try:
                existing_user = User.objects.filter(phone=restaurant.phone).first()
                if existing_user:
                    restaurant.user = existing_user
                    
                else:
                    # Create user with required fields
                    username = f"vendor_{restaurant.phone}"  # or any other pattern
                    user_data = {
                    'phone': restaurant.phone,
                    'username': username,  # Add this line
                    'is_vendor': True,
                    'first_name': restaurant.name,
                    'password': None,  # Or generate a random password
                    }
                    user = User.objects.create_user(**user_data)
                    restaurant.user = user
            except Exception as e:
                logger.error(f"User creation failed for restaurant {restaurant._id}: {str(e)}", exc_info=True)
                return Response(
                    {"error": "User account could not be created. Please contact support."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            restaurant.save(update_fields=["is_verified", "otp", "otp_created_at", "user"])
        except Exception as e:
            logger.error(f"Failed to save restaurant {restaurant._id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to complete verification. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Generate JWT tokens
        try:
            refresh = RefreshToken.for_user(restaurant.user)
            return Response({
                "message": "OTP verified successfully",
                "restaurant_id": str(restaurant._id),
                "user_id": str(restaurant.user.id),
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Token generation failed for user {restaurant.user.id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "Login completed but token generation failed. Please try logging in."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import Restaurant, RestaurantImage
from .serializers import RestaurantSerializer, RestaurantCreateSerializer, RestaurantImageSerializer
from bson import ObjectId
import traceback

class RestaurantView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        """Create a new restaurant"""
        try:
            # Check if user already has a restaurant
            existing_restaurant = Restaurant.objects.filter(user=request.user).first()
            if existing_restaurant:
                return Response(
                    {"error": "User already has a restaurant. Use PUT to update."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create new restaurant
            serializer = RestaurantCreateSerializer(data=request.data)
            if serializer.is_valid():
                restaurant = serializer.save(user=request.user)
                
                # Handle gallery images if provided
                gallery_images = request.FILES.getlist('gallery_images')
                if gallery_images:
                    image_paths = []
                    for image in gallery_images:
                        restaurant_image = RestaurantImage.objects.create(restaurant=restaurant, image=image)
                        image_paths.append(restaurant_image.image.url)
                    restaurant.gallery_images = image_paths
                    restaurant.save()
                
                # Return the created restaurant with all details
                result_serializer = RestaurantSerializer(restaurant)
                return Response({
                    "message": "Restaurant created successfully",
                    "restaurant": result_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"[ERROR] Restaurant creation failed: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"Server error during restaurant creation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        """Update existing restaurant"""
        try:
            restaurant = Restaurant.objects.filter(user=request.user).first()
            if not restaurant:
                return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = RestaurantSerializer(restaurant, data=request.data, partial=True)
            if serializer.is_valid():
                updated_restaurant = serializer.save()
                
                # Handle gallery images if provided
                if hasattr(request, 'FILES') and request.FILES.getlist('gallery_images'):
                    gallery_images = request.FILES.getlist('gallery_images')
                    image_paths = updated_restaurant.gallery_images or []
                    for image in gallery_images:
                        if image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                            restaurant_image = RestaurantImage.objects.create(restaurant=updated_restaurant, image=image)
                            image_paths.append(restaurant_image.image.url)
                    updated_restaurant.gallery_images = image_paths
                    updated_restaurant.save()
                
                result_serializer = RestaurantSerializer(updated_restaurant)
                return Response({
                    "message": "Restaurant updated successfully",
                    "restaurant": result_serializer.data
                }, status=status.HTTP_200_OK)
                
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"[ERROR] Restaurant update failed: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"Server error during restaurant update: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Get user's restaurant details"""
        try:
            restaurant = Restaurant.objects.filter(user=request.user).first()
            if not restaurant:
                return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = RestaurantSerializer(restaurant)
            return Response({
                "restaurant": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"[ERROR] Restaurant fetch failed: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"Server error during restaurant fetch: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RestaurantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, restaurant_id=None):
        """Get restaurant details by ID or list all restaurants"""
        try:
            if restaurant_id:
                try:
                    restaurant = Restaurant.objects.filter(_id=ObjectId(restaurant_id)).first()
                except Exception as e:
                    return Response({"error": "Invalid restaurant ID"}, status=status.HTTP_400_BAD_REQUEST)
                if not restaurant:
                    return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = RestaurantSerializer(restaurant)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                restaurants = Restaurant.objects.all()
                
                # Apply filters if provided
                category = request.query_params.get('category')
                if category:
                    restaurants = restaurants.filter(category=category)
                
                city = request.query_params.get('city')
                if city:
                    restaurants = restaurants.filter(city=city)
                
                is_verified = request.query_params.get('is_verified')
                if is_verified is not None:
                    is_verified_bool = is_verified.lower() == 'true'
                    restaurants = restaurants.filter(is_verified=is_verified_bool)
                
                # Apply pagination
                page = int(request.query_params.get('page', 1))
                page_size = int(request.query_params.get('page_size', 10))
                start = (page - 1) * page_size
                end = start + page_size
                
                paginated_restaurants = restaurants[start:end]
                
                serializer = RestaurantSerializer(paginated_restaurants, many=True)
                
                return Response({
                    "count": restaurants.count(),
                    "next": page + 1 if end < restaurants.count() else None,
                    "previous": page - 1 if page > 1 else None,
                    "results": serializer.data
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"[ERROR] Error fetching restaurant(s): {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"Server error while fetching restaurant data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, restaurant_id):
        """Delete a restaurant by ID"""
        try:
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                restaurant = Restaurant.objects.filter(_id=ObjectId(restaurant_id)).first()
            except Exception as e:
                return Response({"error": "Invalid restaurant ID"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not restaurant:
                return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
            
            if restaurant.user != request.user and not request.user.is_staff:
                return Response({"error": "You don't have permission to delete this restaurant"}, 
                                status=status.HTTP_403_FORBIDDEN)
            
            restaurant.delete()
            return Response({"message": "Restaurant deleted successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"[ERROR] Error deleting restaurant: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": f"Server error while deleting restaurant: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UploadRestaurantImagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            restaurant_id = request.data.get('restaurant')
            if not restaurant_id:
                return Response(
                    {"error": "Restaurant ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Rest of your POST method implementation...
            try:
                restaurant = Restaurant.objects.get(_id=ObjectId(restaurant_id))
            except Restaurant.DoesNotExist:
                return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
            
            images = request.FILES.getlist('images')
            if not images:
                return Response({"error": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process images
            for image in images:
                RestaurantImage.objects.create(restaurant=restaurant, image=image)
            
            return Response({"message": "Images uploaded successfully"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},  # More detailed error for debugging
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
   