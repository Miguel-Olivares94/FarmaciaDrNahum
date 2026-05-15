# collico_sw/urls.py
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('farmacia.urls')),
    path('farmacia/', include('farmacia.urls')),
    
]
