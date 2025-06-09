from django.urls import path
from .views import (
    CategoryListCreate, CategoryDetail,
    ProductListCreate, ProductDetail,UploadProductImagesView,UploadCategoryImagesView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,  # ✅ Refresh view
)

urlpatterns = [
    # Category URLs
    path('categories/', CategoryListCreate.as_view(), name='category_list_create'),
    path('categories/<str:pk>/', CategoryDetail.as_view(), name='category_detail'),

    # Product URLs
    path('products/', ProductListCreate.as_view(), name='product_list_create'),
    path('products/<str:pk>/', ProductDetail.as_view(), name='product_detail'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('upload-product-images/', UploadProductImagesView.as_view(), name='upload-product-images'),
    path('upload-category-images/', UploadCategoryImagesView.as_view(), name='upload-category-images'),

    # Your other URLs
]
