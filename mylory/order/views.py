from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DeliveryBoy , Order
from .serializers import DeliveryBoySerializer, DeliveryBoyProfileUpdateSerializer , OrderStatusUpdateSerializer
from django.utils import timezone
from datetime import timedelta
from django.db import DatabaseError
from users.models import Restaurant
import traceback
import random
from django.shortcuts import get_object_or_404
  # Assuming you have this function
import uuid
from .serializers import OrderSerializer
from bson import ObjectId
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_otp():
    return str(random.randint(1000, 9999))

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SendDeliveryBoyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number is required'}, status=400)

        otp = generate_otp()
        delivery_boy, created = DeliveryBoy.objects.get_or_create(phone=phone)
        delivery_boy.otp = otp
        delivery_boy.otp_created_at = timezone.now()
        delivery_boy.save()

        # Here you'd integrate with an actual SMS service
        print(f"OTP for {phone}: {otp}")
        return Response({'message': 'OTP sent successfully'})

class VerifyDeliveryBoyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response({'error': 'Phone and OTP are required'}, status=400)

        try:
            delivery_boy = DeliveryBoy.objects.get(phone=phone, otp=otp)

            if timezone.now() - delivery_boy.otp_created_at > timedelta(minutes=10):
                return Response({'error': 'OTP expired'}, status=400)

            # ✅ User create karo agar assign nahi hai
            if not delivery_boy.user:
                try:
                    # Check if a user with the same phone/username exists
                    user = User.objects.filter(phone=phone).first()
                    if not user:
                        user = User.objects.create_user(
                            phone=phone,
                            username=f"{phone}_{uuid.uuid4().hex[:6]}",  # Ensuring uniqueness
                            password='temp@123',
                            is_delivery_boy=True
                        )
                    delivery_boy.user = user
                    delivery_boy.save()
                except DatabaseError as db_err:
                    print("DB Error Trace:")
                    print(traceback.format_exc())
                    return Response({
                        'error': 'Database error while creating user',
                        'details': str(db_err),
                        'trace': traceback.format_exc()
                    }, status=500)
            else:
                user = delivery_boy.user

            delivery_boy.is_verified = True
            delivery_boy.save()

            tokens = get_tokens_for_user(user)
            return Response({'message': 'OTP verified successfully', 'tokens': tokens}, status=200)

        except DeliveryBoy.DoesNotExist:
            return Response({'error': 'Invalid OTP or phone number'}, status=400)
        except Exception as e:
            print(traceback.format_exc())
            return Response({'error': 'Unexpected error', 'details': str(e)}, status=500)  
            
class DeliveryBoyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        delivery_boy = DeliveryBoy.objects.get(phone=request.user.phone)
        serializer = DeliveryBoySerializer(delivery_boy)
        return Response(serializer.data)

    def put(self, request):
        delivery_boy = DeliveryBoy.objects.get(phone=request.user.phone)
        serializer = DeliveryBoyProfileUpdateSerializer(delivery_boy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully', 'data': serializer.data})
        return Response(serializer.errors, status=400)



class DeliveryBoyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, delivery_boy_id):
        try:
            return DeliveryBoy.objects.get(_id=ObjectId(delivery_boy_id))
        except DeliveryBoy.DoesNotExist:
            raise NotFound("Delivery boy not found")

    def get(self, request, delivery_boy_id):
        delivery_boy = self.get_object(delivery_boy_id)
        serializer = DeliveryBoySerializer(delivery_boy)
        return Response(serializer.data)

    def put(self, request, delivery_boy_id):
        delivery_boy = self.get_object(delivery_boy_id)
        serializer = DeliveryBoyProfileUpdateSerializer(delivery_boy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully', 'data': serializer.data})
        return Response(serializer.errors, status=400)

    def delete(self, request, delivery_boy_id):
        delivery_boy = self.get_object(delivery_boy_id)
        delivery_boy.delete()
        return Response({'message': 'Delivery boy deleted successfully'}, status=200)


def generate_order_number():
    return f"FT{uuid.uuid4().hex[:8].upper()}"

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        restaurant_id_str = data.get('restaurant')

        try:
            restaurant_id = ObjectId(restaurant_id_str)
        except Exception:
            return Response({"error": "Invalid restaurant ID format"}, status=400)

        try:
            restaurant = Restaurant.objects.get(_id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=404)

        # ✅ Don't send 'restaurant' as ObjectId or string — assign instance directly
        data['order_number'] = generate_order_number()
        data['user'] = request.user.id

        serializer = OrderSerializer(data=data, context={'restaurant': restaurant, 'user': request.user})
        if serializer.is_valid():
            order = serializer.save(restaurant=restaurant, user=request.user)  # 👈 Important fix here
            serialized_order = OrderSerializer(order).data

            # Convert ObjectIds to string
            serialized_order['_id'] = str(order._id)
            return Response({'message': 'Order placed successfully', 'order': serialized_order}, status=201)

        return Response(serializer.errors, status=400)


class OrderTrackingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(_id=ObjectId(order_id), user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, _id=ObjectId(order_id))
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            order.status = serializer.validated_data['status']
            order.save()
            return Response({'message': 'Order status updated successfully'})
        return Response(serializer.errors, status=400) 

    def delete(self, request, order_id):
        order = get_object_or_404(Order, _id=ObjectId(order_id))

        # अगर आप cancellation reason भी देना चाहते हैं
        reason = request.data.get('cancellation_reason', 'No reason provided')
        cancelled_by = request.user.id if request.user.is_authenticated else None

        # Update only status-related fields instead of deleting from DB
        order.status = "Cancelled"
        order.cancellation_reason = reason
        order.cancelled_by = cancelled_by
        order.save()

        return Response({'message': 'Order cancelled successfully'})               