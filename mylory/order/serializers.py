from rest_framework import serializers
from .models import DeliveryBoy , Order


class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        fields = '__all__'
        read_only_fields = ['_id', 'is_verified', 'otp', 'otp_created_at', 'created_at', 'updated_at']

class DeliveryBoyProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        exclude = ['_id', 'otp', 'otp_created_at', 'is_verified', 'created_at', 'updated_at']




class OrderSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    restaurant = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get__id(self, obj):
        return str(obj._id)

    def get_restaurant(self, obj):
        return str(obj.restaurant._id) if obj.restaurant else None

    def get_user(self, obj):
        return str(obj.user.id) if obj.user else None

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        'Accepted', 'Preparing', 'On the Way', 'Delivered', 'Cancelled'
    ])
