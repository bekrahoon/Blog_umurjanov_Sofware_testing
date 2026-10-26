from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('create/', views.product_create_view, name='product_create'),
    path('<int:id>/', views.product_detail_view, name='product_detail'),
    path('<int:id>/update/', views.product_update_view, name='product_update'),
    path('<int:id>/delete/', views.product_delete_view, name='product_delete'),
]
