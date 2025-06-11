from django.urls import path
from . import views

urlpatterns = [
    path('server/', views.server_status, name='server_status'),
    path('db/', views.db_status, name='db_status'),
]
