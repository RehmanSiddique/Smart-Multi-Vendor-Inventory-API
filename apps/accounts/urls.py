"""
URL configuration for Account API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Import the views module

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'vendors', views.VendorViewSet, basename='vendor')

urlpatterns = [
    path('', include(router.urls)),
]