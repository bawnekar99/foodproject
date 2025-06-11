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
    images = CategoryImageSerializer(many=True, read_only=True)
    image_files = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'images',      # multiple images URLs
            'image_files', # for upload
        ]
        read_only_fields = ['id']

    def get_images(self, obj):
        request = self.context.get('request')
        images = obj.images.all()
        return [
            request.build_absolute_uri(img.image.url) if request else img.image.url
            for img in images
        ]

    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        category = Category.objects.create(**validated_data)
        for image in image_files:
            CategoryImage.objects.create(category=category, image=image)
        return category


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
        fields = '__all__'

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






# serializers.py

# class RelatedProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = ['id', 'name']


# class CategoryWithProductsSerializer(serializers.ModelSerializer):
#     related_products = serializers.SerializerMethodField()

#     class Meta:
#         model = Category
#         fields = ['id', 'name', 'description', 'image', 'related_products']

#     def get_related_products(self, obj):
#         products = obj.products.exclude(id=self.context.get('exclude_product_id'))
#         return RelatedProductSerializer(products, many=True).data


# class ProductDetailSerializer(serializers.ModelSerializer):
#     category = serializers.SerializerMethodField()

#     class Meta:
#         model = Product
#         fields = ['id', 'name', 'description', 'price', 'image', 'category']

#     def get_category(self, obj):
#         return CategoryWithProductsSerializer(
#             obj.category,
#             context={'exclude_product_id': obj.id}
#         ).data

