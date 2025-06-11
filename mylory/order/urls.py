from django.urls import path
from .views import   SendDeliveryBoyOTPView, VerifyDeliveryBoyOTPView, DeliveryBoyProfileView ,DeliveryBoyDetailView ,CreateOrderView,OrderTrackingView,UpdateOrderStatusView

urlpatterns = [
    path('deliveryboy/send-otp/', SendDeliveryBoyOTPView.as_view(), name='send_deliveryboy_otp'),
    path('deliveryboy/verify-otp/', VerifyDeliveryBoyOTPView.as_view(), name='verify_deliveryboy_otp'),
    path('deliveryboy/profile/', DeliveryBoyProfileView.as_view(), name='deliveryboy_profile'),
    path('deliveryboy/<str:delivery_boy_id>/', DeliveryBoyDetailView.as_view()), 

    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('track/<str:order_id>/', OrderTrackingView.as_view(), name='track-order'),
    path('update-status/<str:order_id>/', UpdateOrderStatusView.as_view(), name='update-order-status'),
]
