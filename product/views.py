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
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
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
# Product CRUD
class ProductListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        print("🔍 Authenticated user:", request.user)
        print("🔍 User ID:", request.user.id)
        print("📱 User phone from request.user.phone:", getattr(request.user, 'phone', None))

        try:
         restaurant = Restaurant.objects.get(user_id=request.user.id)
        except Restaurant.DoesNotExist:
         return Response({"error": "Restaurant not found for this user"}, status=400)


        data = request.data.copy()
        data['restaurant'] = str(restaurant._id)
        print("📌 Restaurant ID being set in data:", data['restaurant'])

        serializer = ProductSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            product = serializer.save()
            response_serializer = ProductSerializer(product, context={"request": request})
            return Response(response_serializer.data, status=201)

        print("❌ Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=400)

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
