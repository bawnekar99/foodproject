from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RestaurantView, RestaurantDetailView, UploadRestaurantImagesView,SendUserOTPView,VerifyUserOTPView ,UpdateUserLocation ,UpdateUserProfile ,SendRestaurantOTPView ,VerifyRestaurantOTPView
urlpatterns = [
    # User-related URLs
    path('send-otp/', SendUserOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyUserOTPView.as_view(), name='verify_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('update-location/', UpdateUserLocation.as_view(), name='update_location'),
    path('update-profile/', UpdateUserProfile.as_view(), name='update_profile'),

    # Restaurant-related URLs
    path('restaurant/send-otp/', SendRestaurantOTPView.as_view(), name='send_restaurant_otp'),
    path('restaurant/verify-otp/', VerifyRestaurantOTPView.as_view(), name='verify_restaurant_otp'),
    
    # Restaurant CRUD operations
    path('restaurant/', RestaurantView.as_view(), name='restaurant_create_update'),
    path('restaurants/', RestaurantDetailView.as_view(), name='restaurant_list'),
    path('restaurant/<str:restaurant_id>/', RestaurantDetailView.as_view(), name='restaurant_detail'),
    
    # Restaurant images
    path('restaurant_images_upload/', UploadRestaurantImagesView.as_view(), name='restaurant_images_upload'),
    # path('restaurant/image/<str:image_id>/', UploadRestaurantImagesView.as_view(), name='restaurant_image_delete'),
]

