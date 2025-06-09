from rest_framework import serializers
from .models import User, Restaurant, RestaurantImage
from decimal import Decimal
from bson import Decimal128

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

class UserOTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

class UserLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'phone', 'otp', 'is_vendor', 'latitude', 'longitude', 'address', 'profile_pic',
            'first_name', 'last_name', 'birth_date', 'gender', 'bio', 'country', 'city', 'website'
        ]

    def validate_phone(self, value):
        user = self.instance
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        return value


class RestaurantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantImage
        fields = ['id', 'image']
        

class RestaurantSerializer(serializers.ModelSerializer):
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
        model = Restaurant
        fields = [
            'user', 'name', 'description', 'restaurant_type', 'category', 'food_categories',
            'cuisine_types', 'logo', 'cover_image', 'gallery_images', 'address', 'city', 'state',
            'pincode', 'latitude', 'longitude', 'phone', 'email', 'delivery_available',
            'delivery_type', 'pickup_available', 'delivery_radius', 'min_delivery_time',
            'max_delivery_time', 'min_order_amount', 'delivery_fee', 'packaging_fee',
            'opening_time', 'closing_time', 'is_24_hours', 'weekly_off', 'average_rating',
            'total_reviews', 'gst_number', 'fssai_license', 'business_license', 'status',
            'is_verified', 'is_featured', 'is_promoted', 'accepts_cash', 'accepts_card',
            'accepts_upi', 'has_parking', 'has_wifi', 'has_ac', 'total_orders',
            'total_revenue', 'created_at', 'updated_at', 'images'
        ]
        read_only_fields = ['user', 'is_verified', 'created_at', 'updated_at',
                           'average_rating', 'total_reviews', 'total_orders', 'total_revenue']

    def validate_logo(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Logo must be a PNG, JPG, or JPEG file.")
        return value

    def validate_cover_image(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Cover image must be a PNG, JPG, or JPEG file.")
        return value

class RestaurantCreateSerializer(serializers.ModelSerializer):
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
            'name', 'description', 'restaurant_type', 'category', 'food_categories',
            'cuisine_types', 'logo', 'cover_image', 'address', 'city', 'state',
            'pincode', 'latitude', 'longitude', 'phone', 'email', 'delivery_available',
            'delivery_type', 'pickup_available', 'delivery_radius', 'min_delivery_time',
            'max_delivery_time', 'min_order_amount', 'delivery_fee', 'packaging_fee',
            'opening_time', 'closing_time', 'is_24_hours', 'weekly_off',
            'gst_number', 'fssai_license', 'business_license',
            'accepts_cash', 'accepts_card', 'accepts_upi', 'has_parking', 'has_wifi', 'has_ac'
        ]
        read_only_fields = ['is_verified']

    def validate_logo(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Logo must be a PNG, JPG, or JPEG file.")
        return value

    def validate_cover_image(self, value):
        if value and not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Cover image must be a PNG, JPG, or JPEG file.")
        return value