from django.urls import path
from . import views

urlpatterns = [
    path('vendors/', views.vendor_list),
    path('vendors/<str:vendor_code>/', views.vendor_detail),
    path('vendors/<int:vendor_id>/performance', views.vendor_performance_detail),
    path('purchase_orders/', views.purchase_order_list),
    path('purchase_orders/<str:po_number>/', views.purchase_order_detail),
    path('purchase_orders/<int:po_id>/acknowledge', views.acknowledge_purchase_order),
]