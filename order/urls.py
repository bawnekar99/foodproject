from django.urls import path
from .views import   SendDeliveryBoyOTPView, VerifyDeliveryBoyOTPView, DeliveryBoyProfileView ,DeliveryBoyDetailView ,CreateOrderView,OrderTrackingView,UpdateOrderStatusView ,DeliveryBoyListView ,DeliveryBoyOrdersView

urlpatterns = [
    path('deliveryboy/send-otp/', SendDeliveryBoyOTPView.as_view(), name='send_deliveryboy_otp'),
    path('deliveryboy/verify-otp/', VerifyDeliveryBoyOTPView.as_view(), name='verify_deliveryboy_otp'),
    path('deliveryboy/profile/', DeliveryBoyProfileView.as_view(), name='deliveryboy_profile'),
    path('deliveryboy/', DeliveryBoyListView.as_view()),  # GET all delivery boys
    path('deliveryboy/<str:delivery_boy_id>/', DeliveryBoyDetailView.as_view()),  


    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('track/', OrderTrackingView.as_view(), name='track-orders-list'),             # ✅ All orders
    path('track/<str:order_id>/', OrderTrackingView.as_view(), name='track-order'),
    path('update-status/<str:order_id>/', UpdateOrderStatusView.as_view(), name='update-order-status'),
    path('delivery/orders/', DeliveryBoyOrdersView.as_view(), name='delivery-boy-orders'),

]
