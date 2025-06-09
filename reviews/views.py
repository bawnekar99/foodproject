# views.py
from rest_framework import generics
from .models import ProductReview, RestaurantReview
from .serializers import ProductReviewSerializer, RestaurantReviewSerializer

# Product Review Views
from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework import status, permissions
from .models import ProductReview
from .serializers import ProductReviewSerializer
from product.models import Product
from .models import RestaurantReview
from .serializers import RestaurantReviewSerializer
from users.models import Restaurant  


class ProductReviewCreateOrUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("🔐 Authenticated user:", request.user)
        print("🧾 Request data:", request.data)

        # Validate product ID
        product_id = request.data.get("product")
        if not product_id or not ObjectId.is_valid(product_id):
            return Response({"error": "Invalid or missing product ID"}, status=400)

        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        # Check if review already exists for this user and product
        existing_review = ProductReview.objects.filter(user=request.user, product=product).first()

        data = request.data.copy()

        if existing_review:
            # Update
            serializer = ProductReviewSerializer(existing_review, data=data, partial=True)
        else:
            # Create
            serializer = ProductReviewSerializer(data=data)

        if serializer.is_valid():
            review = serializer.save(user=request.user, product=product)
            return Response({
                "message": "Review updated successfully" if existing_review else "Review created successfully",
                "data": ProductReviewSerializer(review).data
            }, status=status.HTTP_200_OK if existing_review else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=400)


class ProductReviewListView(generics.ListAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Initialize with an empty queryset as fallback
        queryset = ProductReview.objects.none()  

        try:
            # Start with all product reviews
            queryset = ProductReview.objects.all()
            
            # Apply filters
            product_id = self.request.query_params.get('product_id')
            if product_id:
                queryset = queryset.filter(product__id=product_id)
                
            # Apply ordering
            queryset = queryset.order_by('-created_at')
            
        except Exception as e:
            print(f"Error in get_queryset: {e}")  # Debugging
            
        return queryset

# class ProductReviewDeleteView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, product_id):
#         if not ObjectId.is_valid(product_id):
#             return Response({"error": "Invalid product ID"}, status=400)

#         try:
#             review = ProductReview.objects.get(user=request.user, product=ObjectId(product_id))
#             review.delete()
#             return Response({"message": "Review deleted successfully"}, status=204)
#         except ProductReview.DoesNotExist:
#             return Response({"error": "Review not found"}, status=404)


class ProductReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):
        try:
            review = ProductReview.objects.get(id=int(review_id))
            serializer = ProductReviewSerializer(review)
            return Response(serializer.data, status=200)
        except ProductReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def delete(self, request, product_id):
        if not ObjectId.is_valid(product_id):
            return Response({"error": "Invalid product ID"}, status=400)

        try:
            review = ProductReview.objects.get(user=request.user, product=ObjectId(product_id))
            review.delete()
            return Response({"message": "Review deleted successfully"}, status=204)
        except ProductReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def put(self, request, review_id):
        try:
            review = ProductReview.objects.get(id=int(review_id))
            serializer = ProductReviewSerializer(review, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ProductReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def patch(self, request, review_id):
        try:
            review = ProductReview.objects.get(id=review_id, user=request.user)
            serializer = ProductReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ProductReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)


class CreateOrUpdateRestaurantReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("🔐 Authenticated user:", request.user)
        print("🧾 Request data:", request.data)

        # Validate restaurant ID
        restaurant_id = request.data.get("restaurant")
        if not restaurant_id or not ObjectId.is_valid(restaurant_id):
            return Response({"error": "Invalid or missing restaurant ID"}, status=400)

        try:
            restaurant = Restaurant.objects.get(_id=ObjectId(restaurant_id))
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=404)

        # Check if review exists
        existing_review = RestaurantReview.objects.filter(user=request.user, restaurant=restaurant).first()

        data = request.data.copy()
        data['restaurant'] = str(restaurant._id)


        if existing_review:
            # Update existing review
            serializer = RestaurantReviewSerializer(existing_review, data=data, partial=True)
        else:
            # Create new review with proper context
            serializer = RestaurantReviewSerializer(data=data, context={
                'user': request.user,
                'restaurant': restaurant
            })

        if serializer.is_valid():
            if existing_review:
                review = serializer.save()
            else:
                review = serializer.save(user=request.user, restaurant=restaurant)

            return Response({
                "message": "Review updated successfully" if existing_review else "Review created successfully",
                "data": RestaurantReviewSerializer(review).data
            }, status=status.HTTP_200_OK if existing_review else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=400)


class RestaurantReviewListView(generics.ListAPIView):
    serializer_class = RestaurantReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Fallback to empty queryset in case of any failure
        queryset = RestaurantReview.objects.none()

        try:
            # Start with all restaurant reviews
            queryset = RestaurantReview.objects.all()

            # Apply restaurant ID filter from query params
            restaurant_id = self.request.query_params.get('restaurant_id')
            if restaurant_id and ObjectId.is_valid(restaurant_id):
                queryset = queryset.filter(restaurant__id=ObjectId(restaurant_id))

            # Order by creation date
            queryset = queryset.order_by('-created_at')

        except Exception as e:
            print(f"Error in get_queryset: {e}")  # Debugging output

        return queryset


# class DeleteRestaurantReviewView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, restaurant_id):
#         if not ObjectId.is_valid(restaurant_id):
#             return Response({"error": "Invalid restaurant ID"}, status=400)

#         try:
#             review = RestaurantReview.objects.get(user=request.user, restaurant=ObjectId(restaurant_id))
#             review.delete()
#             return Response({"message": "Review deleted successfully"}, status=204)
#         except RestaurantReview.DoesNotExist:
#             return Response({"error": "Review not found"}, status=404)


class RestaurantReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):
        try:
            review = RestaurantReview.objects.get(id=review_id, user=request.user)
            serializer = RestaurantReviewSerializer(review)
            return Response(serializer.data, status=200)
        except RestaurantReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def delete(self, request, restaurant_id):
        try:
            review = RestaurantReview.objects.get(user=request.user, restaurant_id=restaurant_id)
            review.delete()
            return Response({"message": "Review deleted successfully"}, status=204)
        except RestaurantReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def put(self, request, review_id):
        try:
            review = RestaurantReview.objects.get(id=review_id, user=request.user)
            serializer = RestaurantReviewSerializer(review, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except RestaurantReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

    def patch(self, request, review_id):
        try:
            review = RestaurantReview.objects.get(id=review_id, user=request.user)
            serializer = RestaurantReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except RestaurantReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
