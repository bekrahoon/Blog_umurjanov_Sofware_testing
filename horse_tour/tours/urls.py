from django.urls import path

from . import views

urlpatterns = [
    path('', views.tour_list_view, name='tour_list'),
    path('tours/<int:id>/', views.tour_detail_view, name='tour_detail'),
    path('categories/create/', views.create_category_view, name='create_category'),
    path('tours/create/', views.create_tour_view, name='create_tour'),
    path('routes/create/', views.create_route_view, name='create_route'),
    path('customers/create/', views.create_customer_view, name='create_customer'),
    path('bookings/create/', views.create_booking_view, name='create_booking'),
    path('comments/create/', views.create_comment_view, name='create_comment'),
]
