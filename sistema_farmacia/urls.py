# sistema_farmacia/urls.py
from django.contrib import admin
from django.urls import path, include
from decouple import config

# Ruta del admin oculta — configurable por variable de entorno ADMIN_URL
ADMIN_URL = config('ADMIN_URL', default='gestion-interna-nahum/')

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path('', include('farmacia.urls')),
    path('farmacia/', include('farmacia.urls')),
]
