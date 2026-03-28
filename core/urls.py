from django.urls import path
from . import views

urlpatterns = [
    # Product Management
    path('add-product', views.add_product, name='add-product'), 
    path('my-products', views.get_my_products, name='my-products'),
    path('delete-product/<str:pk>', views.delete_product, name='delete-product'),
    path('all-market-products', views.get_all_market_products, name='all-market-products'),
    
    # Order & Request Management
    path('create-order', views.create_order, name='create-order'),
    path('farmer-orders', views.get_farmer_orders, name='farmer-orders'),
    path('vendor-orders', views.get_vendor_orders, name='vendor-orders'),
    path('update-order-status', views.update_order_status, name='update-order-status'),
    path('manage-requests', views.manage_requests, name='manage-requests'),
    path('delete-order/<str:pk>', views.delete_order, name='delete-order'),
    path('delete-request/<str:pk>', views.delete_request, name='delete-request'),
]