from rest_framework import serializers
from .models import User, Restaurant, RestaurantImage
from decimal import Decimal
from bson import Decimal128
import logging


import json
from bson import ObjectId
from rest_framework import serializers




logger = logging.getLogger(__name__)

class FlexibleDecimalField(serializers.DecimalField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data:
            try:
                data = Decimal(data)
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"{self.field_name} must be a valid decimal number.")
        return super().to_internal_value(data)

    def to_representation(self, value):
        if isinstance(value, Decimal128):
            value = Decimal(str(value))
        return super().to_representation(value)

class FlexibleFloatField(serializers.FloatField):
    def to_representation(self, value):
        if isinstance(value, Decimal128):
            value = float(str(value))
        return super().to_representation(value)

class UserOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        # Add any phone number validation here
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return value

class UserOTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

class UserLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

 # import your User model accordingly

logger = logging.getLogger(__name__)

class ObjectIdField(serializers.Field):
    """Custom field to handle ObjectId serialization"""
    
    def to_representation(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return str(value)
    
    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except:
            raise serializers.ValidationError("Invalid ObjectId format")

class UserProfileUpdateSerializerSimple(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'latitude', 'longitude', 'address', 'profile_pic', 'birth_date',
            'gender', 'bio', 'country', 'city', 'website', 'otp',
            'is_vendor', 'is_active', 'is_staff'
        ]
        read_only_fields = ['id','is_active', 'is_staff', 'otp', 'is_vendor']
    
    def get__id(self, obj):
        """Convert integer ID to ObjectId-like string"""
        # Create a pseudo ObjectId from integer
        # This will create a 24-character hex string that looks like ObjectId
        import hashlib
        
        # Create a consistent ObjectId-like string from integer ID
        hash_object = hashlib.md5(str(obj.id).encode())
        hex_dig = hash_object.hexdigest()
        
        # Take first 24 characters to make it look like ObjectId
        pseudo_object_id = hex_dig[:24]
        
        return pseudo_object_id
    
    # Alternative: Generate actual ObjectId
    def get__id_alternative(self, obj):
        """Generate a new ObjectId for each user"""
        # This will generate a new ObjectId every time
        # Not recommended if you want consistent IDs
        new_object_id = ObjectId()
        return str(new_object_id)


class FlexibleDecimalField(serializers.DecimalField):
    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        try:
            return super().to_internal_value(data)
        except Exception:
            return float(data) if data else None

class FlexibleFloatField(serializers.FloatField):
    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        try:
            return float(data)
        except (ValueError, TypeError):
            return None

# User Serializer (assuming you have this)
class UserOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Replace with your User model
        fields = ['phone']  # Add other fields as needed

# Restaurant Image Serializer (assuming you have this)
class RestaurantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantImage  # Replace with your RestaurantImage model
        fields = '__all__'  # Adjust fields as needed

# Main Restaurant Serializer
class RestaurantSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    user = UserOTPSerializer(read_only=True)
    images = RestaurantImageSerializer(many=True, read_only=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    cover_image = serializers.ImageField(required=False, allow_null=True)
    latitude = FlexibleDecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = FlexibleDecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    delivery_fee = FlexibleFloatField(required=False, allow_null=True)
    packaging_fee = FlexibleFloatField(required=False, allow_null=True)
    min_order_amount = FlexibleFloatField(required=False, allow_null=True)
    average_rating = FlexibleFloatField(read_only=True)
    total_revenue = FlexibleFloatField(read_only=True)

    class Meta:
        model = Restaurant  # Replace with your Restaurant model
        fields = [
            '_id', 'user_id', 'user', 'name', 'description', 'restaurant_type', 'category', 
            'food_categories', 'cuisine_types', 'logo', 'cover_image', 'gallery_images', 
            'address', 'city', 'state', 'pincode', 'latitude', 'longitude', 'phone', 
            'email', 'delivery_available', 'delivery_type', 'pickup_available', 
            'delivery_radius', 'min_delivery_time', 'max_delivery_time', 'min_order_amount', 
            'delivery_fee', 'packaging_fee', 'opening_time', 'closing_time', 'is_24_hours', 
            'weekly_off', 'average_rating', 'total_reviews', 'gst_number', 'fssai_license', 
            'business_license', 'status', 'is_verified', 'is_featured', 'is_promoted', 
            'accepts_cash', 'accepts_card', 'accepts_upi', 'has_parking', 'has_wifi', 
            'has_ac', 'total_orders', 'total_revenue', 'created_at', 'updated_at', 'images'
        ]
        read_only_fields = [
            '_id', 'user_id', 'user', 'is_verified', 'created_at', 'updated_at',
            'average_rating', 'total_reviews', 'total_orders', 'total_revenue'
        ]

    def get__id(self, obj):
        """Return restaurant ObjectId as string"""
        try:
            return str(obj.id) if hasattr(obj, 'id') and obj.id else None
        except Exception as e:
            logger.error(f"Error getting restaurant _id: {str(e)}")
            return None

    def get_user_id(self, obj):
        """Return user ID"""
        try:
            if hasattr(obj, 'user') and obj.user:
                # If using ObjectId for user as well
                if hasattr(obj.user, 'id'):
                    return str(obj.user.id) if isinstance(obj.user.id, ObjectId) else obj.user.id
                # If using regular integer ID
                return obj.user.pk
            return None
        except Exception as e:
            logger.error(f"Error getting user_id: {str(e)}")
            return None

    def to_representation(self, instance):
        """Custom representation to ensure IDs are properly formatted"""
        logger.debug(f"Serializing restaurant instance ID: {instance.id}")
        logger.debug(f"Restaurant instance ID type: {type(instance.id)}")
        
        data = super().to_representation(instance)
        
        # Debug logging
        logger.debug(f"Serialized data before processing: {data}")
        
        # Ensure _id is properly set
        if hasattr(instance, 'id') and instance.id:
            data['_id'] = str(instance.id)
        
        # Ensure user_id is properly set
        if hasattr(instance, 'user') and instance.user:
            if hasattr(instance.user, 'id'):
                data['user_id'] = str(instance.user.id) if isinstance(instance.user.id, ObjectId) else instance.user.id
            else:
                data['user_id'] = instance.user.pk
        
        logger.debug(f"Final serialized data: {data}")
        return data

    def validate_logo(self, value):
        """Validate logo file format"""
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Logo must be a PNG, JPG, or JPEG file.")
        return value

    def validate_cover_image(self, value):
        """Validate cover image file format"""
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Cover image must be a PNG, JPG, or JPEG file.")
        return value

class RestaurantCreateSerializer(serializers.ModelSerializer):
    _id = serializers.CharField(source='id', read_only=True)
    latitude = FlexibleDecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = FlexibleDecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    delivery_fee = FlexibleFloatField(required=False, allow_null=True)
    packaging_fee = FlexibleFloatField(required=False, allow_null=True)
    min_order_amount = FlexibleFloatField(required=False, allow_null=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    cover_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Restaurant
        fields = [
            '_id', 'name', 'description', 'restaurant_type', 'category', 'food_categories',
            'cuisine_types', 'logo', 'cover_image', 'address', 'city', 'state',
            'pincode', 'latitude', 'longitude', 'phone', 'email', 'delivery_available',
            'delivery_type', 'pickup_available', 'delivery_radius', 'min_delivery_time',
            'max_delivery_time', 'min_order_amount', 'delivery_fee', 'packaging_fee',
            'opening_time', 'closing_time', 'is_24_hours', 'weekly_off',
            'gst_number', 'fssai_license', 'business_license',
            'accepts_cash', 'accepts_card', 'accepts_upi', 'has_parking', 'has_wifi', 'has_ac'
        ]
        read_only_fields = ['_id', 'is_verified']

    def to_representation(self, instance):
      data = super().to_representation(instance)
      if '_id' in data:
        data['_id'] = str(data['_id'])
      return data


    def validate_logo(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Logo must be a PNG, JPG, or JPEG file.")
        return value

    def validate_cover_image(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Cover image must be a PNG, JPG, or JPEG file.")
        return value
