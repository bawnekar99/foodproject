from djongo import models
from django.conf import settings

class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    rating = models.FloatField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RestaurantReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurant = models.ForeignKey('users.Restaurant', on_delete=models.CASCADE)

    food_rating = models.FloatField()
    food_comment = models.TextField(blank=True)

    service_rating = models.FloatField()
    service_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
