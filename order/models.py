from djongo import models
from bson import ObjectId
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()



class DeliveryBoy(models.Model):
    _id = models.ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_boy', null=True, blank=True)
    # Basic Info
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField( null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Authentication
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # Location Info
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Profile / Documents
    profile_pic = models.ImageField(upload_to='delivery_boys/profile_pics/', null=True, blank=True)
    aadhar_number = models.CharField(max_length=20, null=True, blank=True)
    aadhar_image = models.ImageField(upload_to='delivery_boys/aadhar/', null=True, blank=True)
    license_number = models.CharField(max_length=20, null=True, blank=True)
    license_image = models.ImageField(upload_to='delivery_boys/license/', null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, null=True, blank=True)
    vehicle_model = models.CharField(max_length=50, null=True, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=[("bike", "Bike"), ("scooter", "Scooter"), ("car", "Car")], null=True, blank=True)

    # Status and Timing
    is_available = models.BooleanField(default=True)
    current_status = models.CharField(max_length=20, choices=[
        ('idle', 'Idle'), 
        ('on_delivery', 'On Delivery'), 
        ('offline', 'Offline')
    ], default='idle')
    last_active = models.DateTimeField(null=True, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or self.phone}"



ORDER_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Preparing', 'Preparing'),
    ('Picked Up', 'Picked Up'),
    ('On the Way', 'On the Way'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
    ('Refunded', 'Refunded'),
]

PAYMENT_METHOD_CHOICES = [
    ('Cash on Delivery', 'Cash on Delivery'),
    ('UPI', 'UPI'),
    ('Card', 'Card'),
    ('Net Banking', 'Net Banking'),
    ('Wallet', 'Wallet'),
]

PAYMENT_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Paid', 'Paid'),
    ('Failed', 'Failed'),
    ('Refunded', 'Refunded'),
]

DELIVERY_TYPE_CHOICES = [
    ('Delivery', 'Delivery'),
    ('Pickup', 'Pickup'),
]

class Order(models.Model):
    _id = models.ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    restaurant = models.ForeignKey('users.Restaurant', on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')
    
    delivery_boy = models.ForeignKey('order.DeliveryBoy', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    order_number = models.CharField(max_length=20, unique=True)
    items = models.JSONField(help_text="List of product IDs, names, quantities, and prices")
    instructions = models.TextField(blank=True, null=True, help_text="Special instructions from user")

    subtotal = models.FloatField()
    tax = models.FloatField(default=0.0)
    delivery_fee = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    total_price = models.FloatField()

    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='Cash on Delivery')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES, default='Delivery')
    delivery_address = models.TextField()
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)

    estimated_time_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    
    is_rated = models.BooleanField(default=False)
    cancelled_by = models.CharField(max_length=20, blank=True, null=True)  # User/Restaurant/Admin
    cancellation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"