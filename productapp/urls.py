from django.urls import path
from .views import create_product, create_order ,get_orders
from django.urls import path
from .views import (
    customer_segmentation, 
    product_recommendations, 
    predict_previous_orders, 
    suggest_remaining_products
   
)

urlpatterns = [
    path('add_product/', create_product, name='add_product'),
    path('place_order/', create_order, name='place_order'),
    path('get_orders/<str:customer_id>/', get_orders, name='get_orders'),
    
    path('customer_segmentation/', customer_segmentation, name='customer_segmentation'),
    path('product_recommendations/', product_recommendations, name='product_recommendations'),
    path('predict_previous_orders/', predict_previous_orders, name='predict_previous_orders'),
    path('suggest_remaining_products/', suggest_remaining_products, name='suggest_remaining_products'),
    
]




