from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/', include('product.urls')),  # अगर आपने product app बनाई है
    path('reviews/', include('reviews.urls')),
    path('users/', include('users.urls')),
    path('orders/', include('order.urls')),
    path('servers/', include('server.urls')),

    # Add other app urls here
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
