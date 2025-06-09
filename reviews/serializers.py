from rest_framework import serializers
from .models import ProductReview, RestaurantReview
from .models import ProductReview 
from users.models import Restaurant , User


class ProductReviewSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at', 'product', 'user']

    def get_product(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_user(self, obj):
        try:
            return str(obj.user.id)
        except Exception:
            return None







class RestaurantReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    restaurant = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantReview
        fields = [
            'id', 'restaurant', 'user',
            'food_rating', 'food_comment',
            'service_rating', 'service_comment',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'restaurant', 'created_at']

    def get_user(self, obj):
     try:
        if hasattr(obj, 'user') and obj.user:
            return str(obj.user.id)
     except User.DoesNotExist:
        return None


    def get_restaurant(self, obj):
     try:
        if hasattr(obj, 'restaurant') and obj.restaurant:
            return str(obj.restaurant._id)
     except Restaurant.DoesNotExist:
        return None


    def create(self, validated_data):
        # Expect 'user' and 'restaurant' in context
        user = self.context.get('user')
        restaurant = self.context.get('restaurant')

        if not user or not restaurant:
            raise serializers.ValidationError("User and Restaurant must be provided")

        # Remove them from data if passed accidentally
        validated_data.pop('user', None)
        validated_data.pop('restaurant', None)

        return RestaurantReview.objects.create(
            user=user,
            restaurant=restaurant,
            **validated_data
        )

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
