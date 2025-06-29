# users/views.py
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from bson import ObjectId
import random
import hashlib
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone 
from .models import Restaurant, User, RestaurantImage
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    UserOTPSerializer, UserOTPVerifySerializer, UserLocationSerializer, 
    UserProfileUpdateSerializerSimple, RestaurantSerializer,
    RestaurantImageSerializer, RestaurantCreateSerializer 
)
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone 
from rest_framework.parsers import MultiPartParser, FormParser
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404
from helpers.sms import send_sms
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
import logging
from django.db import transaction
from rest_framework.throttling import AnonRateThrottle
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, DatabaseError

logger = logging.getLogger(__name__)
User = get_user_model()


logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
import random
import logging
import traceback
from django.db import IntegrityError
from bson import ObjectId  # Import for MongoDB ObjectId handling

logger = logging.getLogger(__name__)

# Custom JSON serializer for ObjectId
def serialize_objectid(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

class SendUserOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'otp'

    def post(self, request):
        phone = str(request.data.get('phone', '')).strip()
        logger.info(f"Processing OTP for: {phone}")

        # Phone validation
        if not phone.isdigit() or len(phone) != 10:
            return Response(
                {"error": "Invalid phone number. Must be 10 digits."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        logger.info(f"Generated OTP: {otp}")

        try:
            # Try to get existing user
            try:
                user = User.objects.get(phone=phone)
                user.otp = otp
                user.save(update_fields=['otp'])
                logger.info(f"Updated OTP for existing user: {phone}")
            except User.DoesNotExist:
                # Create new user if doesn't exist
                try:
                    user = User.objects.create_user(
                        phone=phone,
                        username=phone,
                        otp=otp,
                        password=None
                    )
                    logger.info(f"Created new user with OTP: {phone}")
                except IntegrityError as e:
                    logger.error(f"Integrity error creating user {phone}: {str(e)}")
                    return Response(
                        {"error": "User creation failed due to database constraints"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Send SMS
            sms_response = send_sms(to=phone, var1=otp, var2="")
            if not sms_response.get("status"):
                logger.error(f"SMS failed for {phone}: {sms_response.get('error')}")
                return Response(
                    {"error": "Failed to send OTP"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                "status": "success",
                "message": "OTP sent successfully",
                "phone": phone,
                "otp": otp  # Remove in production
            })

        except Exception as e:
            logger.exception(f"Critical error for {phone}: {str(e)}")
            return Response(
                {"error": "System error processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyUserOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']

            try:
                user = User.objects.filter(phone=phone).first()
                if not user:
                    return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

                if user.otp == otp:
                    user.otp = None
                    user.save()
                    
                    # Get tokens
                    tokens = get_tokens_for_user(user)
                    
                    # Convert ObjectId to string if present
                    user_id = serialize_objectid(user.id) if hasattr(user, 'id') else user.pk
                    
                    return Response({
                        "message": "OTP verified",
                        "access": tokens['access'],
                        "refresh": tokens['refresh'],
                        "user_id": user_id,  # Now safely serializable
                        "phone": user.phone
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
        try:
            user = request.user
            
            # Verify user exists in database
            if not User.objects.filter(id=user.id).exists():
                return Response(
                    {"detail": "User not found", "code": "user_not_found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            serializer = UserLocationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            user.latitude = serializer.validated_data['latitude']
            user.longitude = serializer.validated_data['longitude']
            user.save()
            
            return Response({
                "message": "Location updated successfully",
                "user_id": str(user.id)  # Convert ObjectId to string
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating location for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to update location"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateUserProfile(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        try:
            user = request.user
            
            # Verify user exists
            if not User.objects.filter(id=user.id).exists():
                return Response(
                    {"detail": "User not found", "code": "user_not_found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            serializer = UserProfileUpdateSerializerSimple(
                user,
                data=request.data,
                partial=True
            )
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            serializer.save()
            
            response_data = {
                "message": "Profile updated successfully",
                "user": serializer.data
            }
            
            # Ensure ObjectId is properly serialized
            if 'id' in response_data['user']:
                response_data['user']['id'] = str(response_data['user']['id'])
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating profile for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to update profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                                                 
class ObjectIdJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder jo ObjectId ko string me convert karta hai"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # ObjectId ko string banao
        return super().default(obj)


logger = logging.getLogger(__name__)

class UserListViewWithCustomEncoder(APIView):
    def get(self, request):
        try:
            users = User.objects.all()
            logger.debug(f"Total users fetched: {users.count()}")

            # Filter only users with valid IDs (avoid unhashable error)
            valid_users = [user for user in users if user.id]

            logger.debug(f"Users with valid IDs: {len(valid_users)}")
            
            serializer = UserProfileUpdateSerializerSimple(valid_users, many=True)
            logger.debug(f"Serialized users data: {serializer.data}")
            
            # Use custom JSON encoder to handle ObjectId, etc.
            json_data = json.dumps(serializer.data, cls=ObjectIdJSONEncoder)
            return HttpResponse(json_data, content_type='application/json', status=200)
                         
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")
            return Response({
                "error": f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailViewWithCustomEncoder(APIView):
    def get(self, request, user_id):
        try:
            logger.info(f"Received user_id: {user_id}, type: {type(user_id)}")

            user_id_str = str(user_id).strip()
            if len(user_id_str) != 24 or not all(c in '0123456789abcdef' for c in user_id_str.lower()):
                logger.error(f"Invalid ObjectId format: {user_id_str}")
                return Response({
                    "error": "Invalid user ID format (ObjectId must be 24 hexadecimal characters)"
                }, status=status.HTTP_400_BAD_REQUEST)

            ObjectId(user_id_str)
            logger.info(f"Validated ObjectId-like string: {user_id_str}")

            # Fetch only IDs first (avoids model instance hashing issues)
            user_ids = User.objects.values_list('id', flat=True)
            
            for user_id_db in user_ids:
                hash_object = hashlib.md5(str(user_id_db).encode())
                pseudo_object_id = hash_object.hexdigest()[:24]
                if pseudo_object_id == user_id_str:
                    # Fetch full user only if match found
                    user = User.objects.get(pk=user_id_db)
                    logger.info(f"✓ User found with _id: {user_id_str}, corresponding id: {user.id}")
                    serializer = UserProfileUpdateSerializerSimple(user)
                    return Response(serializer.data, status=status.HTTP_200_OK)

            # Return "Not Found" only after checking ALL users
            logger.error(f"User not found with _id: {user_id_str}")
            return Response({
                "error": "User not found",
                "searched_id": user_id_str
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Unexpected error fetching user {user_id}: {str(e)}")
            return Response({
                "error": f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id):
        try:
            logger.info(f"Received user_id for deletion: {user_id}, type: {type(user_id)}")

            user_id_str = str(user_id).strip()
            if len(user_id_str) != 24 or not all(c in '0123456789abcdef' for c in user_id_str.lower()):
                logger.error(f"Invalid ObjectId format: {user_id_str}")
                return Response({
                    "error": "Invalid user ID format (ObjectId must be 24 hexadecimal characters)"
                }, status=status.HTTP_400_BAD_REQUEST)

            ObjectId(user_id_str)
            logger.info(f"Validated ObjectId-like string for deletion: {user_id_str}")

            # Fetch only IDs first (avoids model instance hashing issues)
            user_ids = User.objects.values_list('id', flat=True)
            
            for user_id_db in user_ids:
                hash_object = hashlib.md5(str(user_id_db).encode())
                pseudo_object_id = hash_object.hexdigest()[:24]
                if pseudo_object_id == user_id_str:
                    # Found matching user, now delete
                    user = User.objects.get(pk=user_id_db)
                    user.delete()
                    logger.info(f"✓ User deleted with _id: {user_id_str}")
                    return Response({
                        "message": "User deleted successfully"
                    }, status=status.HTTP_200_OK)

            # Return "Not Found" only after checking ALL users
            logger.error(f"User not found for deletion with _id: {user_id_str}")
            return Response({
                "error": "User not found",
                "searched_id": user_id_str
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
            return Response({
                "error": f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        # Print to console (for debugging)
        print(f"[Restaurant OTP] {phone}: {otp}")
        
        # Return response with OTP (remove in production)
        return Response({
            "message": "OTP sent successfully",
            "otp": otp  # Include OTP in response for development
        }, status=status.HTTP_200_OK)




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





from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from bson.objectid import ObjectId, InvalidId
from .models import Restaurant
from .serializers import RestaurantSerializer
import traceback
import logging

logger = logging.getLogger(__name__)
class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id=None, *args, **kwargs):
        """Get restaurant details or list of restaurants"""
        try:
            restaurant_id = restaurant_id or kwargs.get("restaurant_id")

            if restaurant_id:
                # Get single restaurant
                try:
                    object_id = ObjectId(restaurant_id)
                except (InvalidId, ValueError, TypeError) as e:
                    logger.error(f"Invalid restaurant ID format: {restaurant_id}, Error: {str(e)}")
                    return Response(
                        {"error": "Invalid restaurant ID format"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                restaurant = Restaurant.objects.filter(id=object_id).first()
                if not restaurant:
                    return Response(
                        {"error": "Restaurant not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )

                logger.debug(f"Found restaurant: {restaurant.id}")
                serializer = RestaurantSerializer(restaurant, context={"request": request})
                response_data = serializer.data
                logger.debug(f"Serializer response data: {response_data}")
                
                return Response(response_data, status=status.HTTP_200_OK)

            # Get list of restaurants with pagination
            restaurants = Restaurant.objects.all()
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 10))
            start = (page - 1) * page_size
            end = start + page_size
            paginated_restaurants = restaurants[start:end]
            total_count = restaurants.count()

            serializer = RestaurantSerializer(
                paginated_restaurants, 
                many=True, 
                context={"request": request}
            )
            
            response_data = {
                "count": total_count,
                "next": page + 1 if end < total_count else None,
                "previous": page - 1 if page > 1 else None,
                "results": serializer.data
            }
            
            logger.debug(f"Paginated response data: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching restaurant(s): {str(e)}\n{traceback.format_exc()}")
            return Response(
                {"error": f"Server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, restaurant_id):
        """Delete a restaurant"""
        try:
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            try:
                object_id = ObjectId(restaurant_id)
            except Exception:
                return Response(
                    {"error": "Invalid restaurant ID"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            restaurant = Restaurant.objects.filter(id=object_id).first()
            if not restaurant:
                return Response(
                    {"error": "Restaurant not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check permissions
            if restaurant.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to delete this restaurant"},
                    status=status.HTTP_403_FORBIDDEN
                )

            restaurant.delete()
            return Response(
                {"message": "Restaurant deleted successfully"}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error deleting restaurant {restaurant_id}: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {"error": f"Server error: {str(e)}"}, 
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

    
   
