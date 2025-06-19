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




import ast  # Safe way to parse stringified list

class OrderSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    restaurant = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    delivery_boy = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get__id(self, obj):
        return str(obj._id)

    def get_restaurant(self, obj):
        return str(obj.restaurant._id) if obj.restaurant else None

    def get_user(self, obj):
        return str(obj.user.id) if obj.user else None

    def get_delivery_boy(self, obj):
        return str(obj.delivery_boy._id) if obj.delivery_boy else None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Safely parse the stringified 'items' if it's a string
        raw_items = data.get('items')
        if isinstance(raw_items, str):
            try:
                parsed_items = ast.literal_eval(raw_items)
                data['items'] = parsed_items
                # Convert product_id to str inside items
                for item in parsed_items:
                    if isinstance(item.get('product_id'), ObjectId):
                        item['product_id'] = str(item['product_id'])
            except Exception as e:
                data['items'] = []  # fallback

        return data


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        'Accepted', 'Preparing', 'On the Way', 'Delivered', 'Cancelled'
    ])
