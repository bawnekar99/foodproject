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
        logger.info(f"OTP sent to delivery boy {phone}: {otp}")
        return Response({'message': 'OTP sent successfully'})

class VerifyDeliveryBoyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response({'error': 'Phone and OTP are required'}, status=400)

        try:
            logger.info(f"Verifying OTP for phone: {phone}, OTP: {otp}")
            
            # ✅ DeliveryBoy find karo
            delivery_boy = DeliveryBoy.objects.get(phone=phone, otp=otp)
            logger.info(f"Found delivery boy: {delivery_boy.id}")

            # ✅ OTP expiry check
            if timezone.now() - delivery_boy.otp_created_at > timedelta(minutes=10):
                logger.warning(f"OTP expired for phone: {phone}")
                return Response({'error': 'OTP expired'}, status=400)

            # ✅ User create/assign karo
            user = None
            
            if not delivery_boy.user:
                logger.info(f"No user assigned to delivery boy {phone}, creating/finding user")
                try:
                    # Pehle check karo ki phone se koi user exist karta hai
                    existing_user = User.objects.filter(phone=phone).first()
                    
                    if existing_user:
                        logger.info(f"Found existing user with phone {phone}: {existing_user.id}")
                        user = existing_user
                    else:
                        logger.info(f"Creating new user for phone {phone}")
                        # नया user create karo
                        unique_username = f"delivery_{phone}_{uuid.uuid4().hex[:6]}"
                        user = User.objects.create_user(
                            phone=phone,
                            username=unique_username,
                            password='temp@123',
                            is_delivery_boy=True
                        )
                        logger.info(f"Created new user: {user.id} with username: {unique_username}")
                    
                    # DeliveryBoy को user assign karo
                    delivery_boy.user = user
                    delivery_boy.is_verified = True
                    delivery_boy.save()
                    logger.info(f"Assigned user {user.id} to delivery boy {delivery_boy.id}")
                    
                except DatabaseError as db_err:
                    logger.error(f"Database error: {str(db_err)}")
                    logger.error(traceback.format_exc())
                    return Response({
                        'error': 'Database error while creating/assigning user',
                        'details': str(db_err)
                    }, status=500)
                except Exception as user_create_err:
                    logger.error(f"Error creating/assigning user: {str(user_create_err)}")
                    logger.error(traceback.format_exc())
                    return Response({
                        'error': 'Error while creating/assigning user',
                        'details': str(user_create_err)
                    }, status=500)
            else:
                # User already assigned hai
                user = delivery_boy.user
                delivery_boy.is_verified = True
                delivery_boy.save()
                logger.info(f"User already assigned: {user.id}")

            # ✅ Final check - make sure user exists
            if not user:
                logger.error("User is None after creation/assignment process")
                return Response({
                    'error': 'Failed to create or assign user'
                }, status=500)

            # ✅ Tokens generate karo
            try:
                logger.info(f"Generating tokens for user: {user.id}")
                tokens = get_tokens_for_user(user)
                logger.info(f"Tokens generated successfully for user: {user.id}")
                
                return Response({
                    'message': 'OTP verified successfully',
                    'tokens': tokens,
                    'user_id': user.id,
                    'delivery_boy_id': delivery_boy.id
                }, status=200)
                
            except Exception as token_err:
                logger.error(f"Error generating tokens: {str(token_err)}")
                logger.error(traceback.format_exc())
                return Response({
                    'error': 'Error generating authentication tokens',
                    'details': str(token_err)
                }, status=500)

        except DeliveryBoy.DoesNotExist:
            logger.warning(f"Invalid OTP or phone number: {phone}, {otp}")
            return Response({'error': 'Invalid OTP or phone number'}, status=400)
            
        except Exception as e:
            logger.error(f"Unexpected error in OTP verification: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'error': 'Unexpected error occurred',
                'details': str(e),
                'trace': traceback.format_exc()
            }, status=500)

class DeliveryBoyProfileView(APIView):
    permission_classes = [IsAuthenticated]

   
    def put(self, request):
        delivery_boy = DeliveryBoy.objects.get(phone=request.user.phone)
        serializer = DeliveryBoyProfileUpdateSerializer(delivery_boy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully', 'data': serializer.data})
        return Response(serializer.errors, status=400)

class DeliveryBoyListView(APIView):
    permission_classes = [IsAuthenticated]  # You can change this to IsAuthenticated if needed

    def get(self, request):
        delivery_boys = DeliveryBoy.objects.all()
        serializer = DeliveryBoySerializer(delivery_boys, many=True)
        return Response(serializer.data)


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

    def get(self, request, order_id=None, *args, **kwargs):
        order_id = order_id or kwargs.get('order_id')

        if order_id:
            try:
                order = Order.objects.get(_id=ObjectId(order_id), user=request.user)
                serializer = OrderSerializer(order)
                return Response(serializer.data)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=404)
            except Exception:
                return Response({'error': 'Invalid Order ID format'}, status=400)
        else:
            # 👇 NO filtering on status, only filter by user
            orders = Order.objects.filter(user=request.user).order_by('-created_at')
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)





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


class DeliveryBoyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            delivery_boy = DeliveryBoy.objects.get(user=request.user)  # request.user.id = 35 होना चाहिए

        except DeliveryBoy.DoesNotExist:
            return Response({'error': 'Delivery boy not found'}, status=404)

        status_filter = request.query_params.get('status')  # Optional: ?status=Delivered
        if status_filter:
            orders = Order.objects.filter(delivery_boy=delivery_boy, status=status_filter)
        else:
            orders = Order.objects.filter(delivery_boy=delivery_boy)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)                     