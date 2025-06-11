from django.urls import path
from .views import *

urlpatterns = [
    # Product Review APIs
    path('product/review/', ProductReviewCreateOrUpdateView.as_view(), name='product-review-create'),
    path('product/review/<str:review_id>/', ProductReviewDetailView.as_view(), name='product-review-detail'),

    # Delete by product ID
    path('product/review/delete/<str:product_id>/', ProductReviewDetailView.as_view(), name='product-review-delete-by-product'),
    path('product/reviews/', ProductReviewListView.as_view(), name='product-review-list'),

    # Restaurant Review APIs
    path('restaurant/review/', CreateOrUpdateRestaurantReviewView.as_view(), name='restaurant-review-create-update'),
    path('restaurant/review/<str:review_id>/', RestaurantReviewDetailView.as_view()),
    path('restaurant/review/delete/<str:restaurant_id>/', RestaurantReviewDetailView.as_view()),

    path('restaurant/reviewslist/', RestaurantReviewListView.as_view(), name='restaurant-review-list'),
]

