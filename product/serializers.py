from rest_framework import serializers
from .models import Category, Product, ProductImage, CategoryImage
from bson import ObjectId
from users.models import Restaurant
from decimal import Decimal


class CategoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryImage
        fields = ['id', 'image']

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    debug_check = serializers.SerializerMethodField()

    def get_debug_check(self, obj):
        return "CategorySerializer used"

    class Meta:
        model = Category
        fields = [
    'id', 'name', 'description', 'restaurant', 'is_active',
    'display_order', 'dietary_type', 'image', 'slug',
    'created_at', 'updated_at'
      ]

        # read_only_fields = ['id', 'created_at', 'updated_at', 'slug']

    def validate_restaurant(self, value):
        # Ensure the restaurant belongs to the authenticated user
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You can only add categories to your own restaurant")
        return value

    def validate_name(self, value):
        # Ensure name is unique for the restaurant
        restaurant_id = self.initial_data.get('restaurant')
        if restaurant_id and Category.objects.filter(
            name=value, restaurant__id=restaurant_id
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Category name already exists for this restaurant")
        return value

    def create(self, validated_data):
        # Auto-set restaurant if not provided, based on authenticated user
        if 'restaurant' not in validated_data:
            try:
                restaurant = Restaurant.objects.get(user=self.context['request'].user)
                validated_data['restaurant'] = restaurant
            except Restaurant.DoesNotExist:
                raise serializers.ValidationError("Restaurant not found for this user")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ensure restaurant cannot be changed to another user's restaurant
        if 'restaurant' in validated_data and validated_data['restaurant'] != instance.restaurant:
            raise serializers.ValidationError("Cannot change the restaurant of an existing category")
        return super().update(instance, validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']





class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    restaurant = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.all())
    
    image_files = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    
    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'description',
            'restaurant',
            'price',
            'final_price',
            'discount_percent',
            'main_image',
            'stock',
            'is_available',
            'average_rating',
            'total_reviews',
            'is_veg',
            'tags',
            'created_at',
            'updated_at',
            'images',
            'image_files'
        ]
        read_only_fields = [
            'id', 'final_price', 'category_name', 'average_rating', 
            'total_reviews', 'created_at', 'updated_at'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter restaurant queryset based on current user
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['restaurant'].queryset = Restaurant.objects.filter(user=request.user)
    
    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        product = Product.objects.create(**validated_data)
        
        for image in image_files:
            ProductImage.objects.create(product=product, image=image)
        
        return product
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = str(instance.id)
        rep['category'] = str(instance.category_id)
        rep['restaurant'] = str(instance.restaurant_id)
        
        request = self.context.get('request')
        if instance.main_image:
            rep['main_image'] = (
                request.build_absolute_uri(instance.main_image.url)
                if request else instance.main_image.url
            )
        return rep
    
    def to_internal_value(self, data):
        for field in ['category', 'restaurant']:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = ObjectId(data[field])
                except Exception:
                    raise serializers.ValidationError({field: "Invalid ObjectId format."})
        return super().to_internal_value(data)
    
    def validate_restaurant(self, value):
        """Validate that the restaurant belongs to the current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                restaurant = Restaurant.objects.get(id=value, user=request.user)
                return value
            except Restaurant.DoesNotExist:
                raise serializers.ValidationError("Restaurant not found for this user")
        return value
    
    def validate_price(self, value):
        if value is None:
            return None
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Price must be a valid decimal number.")
    
    def validate_final_price(self, value):
        if value is None:
            return None
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Final price must be a valid decimal number.")