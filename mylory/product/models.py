from unicodedata import category
from django.db import models
from djongo.models import ObjectIdField
from bson import ObjectId
from decimal import Decimal

from django.utils import timezone

class Category(models.Model):
    id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class CategoryImage(models.Model):
    id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return f"{self.category.name} Image"


class Product(models.Model):
    id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    category_name = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    # No need to import Restaurant anymore

    restaurant = models.ForeignKey("users.Restaurant", on_delete=models.CASCADE, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.FloatField(default=0.0)
    
    
    main_image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)

    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)

    is_veg = models.BooleanField(default=True)
    tags = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Handle category_name
        if self.category:
            self.category_name = self.category.name

        # Handle final_price calculation
        if self.price is not None and self.discount_percent is not None:
            try:
                discount_percent = Decimal(str(self.discount_percent))
                discount_amount = (self.price * discount_percent) / 100
                self.final_price = self.price - discount_amount
                # Ensure final_price has exactly 2 decimal places
                self.final_price = self.final_price.quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError):
                self.final_price = self.price  # Fallback to price if calculation fails
        else:
            self.final_price = self.price  # Use price if no discount

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'


class ProductImage(models.Model):
    id = ObjectIdField(primary_key=True, default=ObjectId, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"{self.product.name} Image"
