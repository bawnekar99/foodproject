from bson import ObjectId
from bson.errors import InvalidId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Category,Product, ProductImage, CategoryImage
from django.shortcuts import get_object_or_404
from .serializers import CategorySerializer, ProductSerializer
from users.models import Restaurant
from rest_framework.permissions import IsAuthenticated


# Category CRUD
class CategoryListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
       categories = Category.objects.all()
       serializer = CategorySerializer(categories, many=True, context={"request": request})
       print("==== DEBUG RESPONSE ====")
       print(serializer.data)  # ← यहाँ से देखो क्या print हो रहा
       return Response(serializer.data)


    def post(self, request):
        serializer = CategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CategoryDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Category.objects.get(id=ObjectId(pk))
        except (Category.DoesNotExist, Exception):
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadCategoryImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        category_id = request.data.get('category')
        if not category_id:
            return Response({"error": "Category ID is required."}, status=400)

        try:
            category_obj_id = ObjectId(category_id)
            category = get_object_or_404(Category, id=category_obj_id)
        except (InvalidId, Category.DoesNotExist):
            return Response({"error": "Invalid Category ID format."}, status=400)

        images = request.FILES.getlist('images')
        if not images:
            return Response({"error": "No images provided."}, status=400)

        for image in images:
            CategoryImage.objects.create(category=category, image=image)

        return Response({"message": "Images uploaded successfully"}, status=201)


class ProductListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Filter products by user's restaurants
        try:
            user_restaurants = Restaurant.objects.filter(user=request.user)
            if not user_restaurants.exists():
                logger.warning(f"No restaurants found for user {request.user.id}")
                return Response({"error": "No restaurants found for this user"}, status=status.HTTP_404_NOT_FOUND)

            products = Product.objects.filter(restaurant__in=user_restaurants)
            serializer = ProductSerializer(products, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        data = request.data.copy()

        # Validate restaurant ID
        restaurant_id = data.get('restaurant')
        if not restaurant_id:
            return Response({"error": "Restaurant ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate ObjectId format
            restaurant_object_id = ObjectId(restaurant_id)
        except Exception as e:
            logger.error(f"Invalid restaurant ID format: {restaurant_id}, Error: {str(e)}")
            return Response({"error": "Invalid restaurant ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if restaurant exists and belongs to the current user
            restaurant = Restaurant.objects.get(
                id=restaurant_object_id,
                user=request.user
            )
        except Restaurant.DoesNotExist:
            logger.warning(f"Restaurant {restaurant_id} not found for user {request.user.id}")
            return Response({"error": "Restaurant not found for this user"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error querying restaurant: {str(e)}")
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Validate category ID
        category_id = data.get('category')
        if not category_id:
            return Response({"error": "Category ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate ObjectId format for category
            category_object_id = ObjectId(category_id)
        except Exception as e:
            logger.error(f"Invalid category ID format: {category_id}, Error: {str(e)}")
            return Response({"error": "Invalid category ID format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = Category.objects.get(id=category_object_id)
        except Category.DoesNotExist:
            logger.warning(f"Category {category_id} not found")
            return Response({"error": "Category not found with this ID"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error querying category: {str(e)}")
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Set actual model instances in the data
        data['restaurant'] = str(restaurant.id)  # Convert ObjectId to string
        data['category'] = str(category.id)      # Convert ObjectId to string

        serializer = ProductSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            try:
                product = serializer.save()
                return Response(
                    ProductSerializer(product, context={"request": request}).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error saving product: {str(e)}")
                return Response({"error": f"Failed to save product: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Product.objects.get(id=ObjectId(pk))
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UploadProductImagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from bson import ObjectId

        product_id = request.data.get('product')
        if not product_id:
            return Response({"error": "Product ID is required."}, status=400)

        try:
            product = get_object_or_404(Product, id=ObjectId(product_id))
        except Exception:
            return Response({"error": "Invalid Product ID format."}, status=400)

        images = request.FILES.getlist('images')
        if not images:
            return Response({"error": "No images provided."}, status=400)

        for image in images:
            ProductImage.objects.create(product=product, image=image)

        return Response({"message": "Images uploaded successfully"}, status=201)
