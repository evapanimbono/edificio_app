"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

schema_view = get_schema_view(
    openapi.Info(
        title="API de Administración de Edificios",
        default_version='v1',
        description="Documentación de la API para arrendadores y arrendatarios",
        terms_of_service="https://www.tuweb.com/terminos/",  # Opcional
        contact=openapi.Contact(email="soporte@tuweb.com"),  # Opcional
        license=openapi.License(name="BSD License"),         # Opcional
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[JWTAuthentication],
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/edificios/', include('edificios.urls')),
    path('api/contratos/', include('contratos.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/gastos/', include('gastos.urls')),
    path('api/tasas/', include('tasas.urls')),
    path('api/encuestas/', include('encuestas.urls')),
    path('api/log/', include('log.urls')),


    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Paso 1: usuario solicita el cambio de contraseña
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # Paso 2: Django envía email con link, este es el link que abre el usuario
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # Paso 3: Formulario para nueva contraseña (token y UID en la URL)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # Paso 4: Confirmación de cambio exitoso
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
