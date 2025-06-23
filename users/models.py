from django.contrib.auth.models import AbstractUser
from django.db import models
from djongo.models import ObjectIdField

from django.utils import timezone
from datetime import timedelta
from .managers import CustomUserManager
from djongo.models.fields import ObjectIdField

from djongo import models as djongo_models
from django.contrib.auth.models import BaseUserManager
from decimal import Decimal
import logging
from djongo import models
from django.contrib.auth.models import AbstractUser
from bson import ObjectId

# Set up logging for debugging
logger = logging.getLogger(__name__)
from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        
        user = self.model(
            phone=phone,
            username=phone,  # Set username same as phone
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)



class User(AbstractUser):
    id = models.ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True)
    is_delivery_boy = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_vendor = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_pic = models.ImageField(upload_to='user_profiles/', null=True, blank=True)

    # Added fields only:
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(null=True, blank=True)

   

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    
    objects = CustomUserManager()

    class Meta:
        db_table = 'users_user' 

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

     

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp

    def __str__(self):
        return self.phone

 






class Restaurant(models.Model):
    # Restaurant Types
    RESTAURANT_TYPES = [
        ('movable', 'Movable (Food Truck/Cart)'),
        ('non_movable', 'Non-Movable (Fixed Location)'),
        ('restaurant', 'Traditional Restaurant'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Temporarily Closed'),
        ('suspended', 'Suspended'),
    ]
    
    # Delivery Type Choices
    DELIVERY_TYPES = [
        ('self', 'Self Delivery'),
        ('platform', 'Platform Delivery'),
        ('both', 'Both'),
        ('pickup_only', 'Pickup Only'),
    ]
    
    _id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Basic Information
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    restaurant_type = models.CharField(max_length=20, choices=RESTAURANT_TYPES, default='restaurant')
    category = models.CharField(max_length=100)  # e.g., Fast Food, Fine Dining, Cafe
    food_categories = models.CharField(max_length=500)  # e.g., Indian, Chinese, Italian
    cuisine_types = models.JSONField(default=list, blank=True)  # List of cuisines
    
    # Media
    logo = models.ImageField(upload_to='restaurant_logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='restaurant_covers/', null=True, blank=True)
    gallery_images = models.JSONField(default=list, blank=True)  # List of additional images
    
    # Location & Contact
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal('0.000000'))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal('0.000000'))
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    
    # Delivery & Timing
    delivery_available = models.BooleanField(default=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPES, default='platform')
    pickup_available = models.BooleanField(default=True)
    delivery_radius = models.PositiveIntegerField(default=5, help_text="Delivery radius in KM")
    min_delivery_time = models.PositiveIntegerField(default=30, help_text="Minimum delivery time in minutes")
    max_delivery_time = models.PositiveIntegerField(default=60, help_text="Maximum delivery time in minutes")
    
    # Pricing
    min_order_amount = models.FloatField(default=0.00)
    delivery_fee = models.FloatField(default=0.00)
    packaging_fee = models.FloatField(default=0.00)
    
    # Business Hours
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_24_hours = models.BooleanField(default=False)
    weekly_off = models.JSONField(default=list, blank=True)  # List of days like ['sunday']
    
    # Rating & Reviews
    average_rating = models.FloatField(default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Business Details (Optional)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    fssai_license = models.CharField(max_length=14, blank=True, null=True)
    business_license = models.CharField(max_length=50, blank=True, null=True)
    
    # Status & Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_promoted = models.BooleanField(default=False)
    
    # OTP & Verification
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Features
    accepts_cash = models.BooleanField(default=True)
    accepts_card = models.BooleanField(default=True)
    accepts_upi = models.BooleanField(default=True)
    has_parking = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    
    # Analytics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.FloatField(default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'status']),
            models.Index(fields=['restaurant_type']),
            models.Index(fields=['delivery_available']),
            models.Index(fields=['is_verified']),
        ]
    
    def otp_is_expired(self):
        if not self.otp_created_at:
            return True
        return timezone.now() > self.otp_created_at + timedelta(minutes=30)
    
    def is_open(self):
        if self.is_24_hours:
            return True
        
        if not self.opening_time or not self.closing_time:
            return False
            
        current_time = timezone.now().time()
        current_day = timezone.now().strftime('%A').lower()
        
        if current_day in self.weekly_off:
            return False
            
        return self.opening_time <= current_time <= self.closing_time
    
    def can_deliver_to(self, distance_km):
        return self.delivery_available and distance_km <= self.delivery_radius
    
    def get_estimated_delivery_time(self):
        return f"{self.min_delivery_time}-{self.max_delivery_time} mins"
    
    def __str__(self):
        return f"{self.name} ({self.get_restaurant_type_display()})"


class RestaurantImage(models.Model):
    id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    restaurant = models.ForeignKey('users.Restaurant', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='restaurant_images/')

    def __str__(self):
        return f"{self.restaurant.name} Image"
