"""
Main API URL configuration.
Handles versioning and includes app-specific URLs.
"""

from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Smart Multi-Vendor Inventory API",
        default_version='v1',
        description="Complete inventory management system with multi-tenancy",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@smvia.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # API Version 1
    path('v1/', include([
        # Authentication endpoints
        path('auth/', include([
            path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
            path('verify/', TokenVerifyView.as_view(), name='token_verify'),
        ])),
        
        # App endpoints - make sure these aren't duplicated elsewhere
        path('accounts/', include('apps.accounts.urls')),
        path('inventory/', include('apps.inventory.urls')),
    ])),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]