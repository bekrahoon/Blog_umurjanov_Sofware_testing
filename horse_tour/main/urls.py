from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Документация через django.contrib.admindocs (должна быть до admin/)
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
]
