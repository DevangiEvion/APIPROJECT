"""
URL configuration for APIPROJECT project.

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
from django.urls import path
from myapp.views import RegisterView, LoginView, ProfileView
from products.views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,CategoryListCreateView, CategoryRetrieveUpdateDestroyView, 
    CartListCreateView, CartUpdateView, CartDeleteView, CartClearView, OrderView, PurchaseView, ProductReturnViewSet,
    OrderReportView, UserOrderReportView, ProductSalesReportView, PurchaseReportView, invoice_view, invoice_pdf, Order_invoice, Order_invoice_pdf
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('profile/', ProfileView.as_view()),

    # Products
    path('products/', ProductListView.as_view()),
    path('products/add/', ProductCreateView.as_view()),
    path('products/<int:pk>/update/', ProductUpdateView.as_view()),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view()),

    # Categories
    path('categories/', CategoryListCreateView.as_view()),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view()),

    # Cart
    path('cart/', CartListCreateView.as_view()),
    path('cart/<int:pk>/update/', CartUpdateView.as_view()),
    path('cart/<int:pk>/delete/', CartDeleteView.as_view()),
    path('cart/clear/', CartClearView.as_view()),
    #path('cart/checkout/', CartCheckoutView.as_view()),

    # Orders
    path('orders/', OrderView.as_view()),          
    path('orders/<int:pk>/', OrderView.as_view()),

    # Purchase
    path('purchases/', PurchaseView.as_view()),       
    path('purchases/<int:pk>/', PurchaseView.as_view()),

    # Product Return
    path('product-returns/', ProductReturnViewSet.as_view({'get': 'list', 'post': 'create'}), name='productreturn-list-create'),
    path('product-returns/<int:pk>/', ProductReturnViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='productreturn-detail'),

    # Order Report
    path('orders/report/', OrderReportView.as_view(), name='order-report'),
    path('orders/report/user/<int:user_id>/', UserOrderReportView.as_view(), name='user-order-report'),
    path('reports/product-sales/', ProductSalesReportView.as_view(), name='product-sales-report'),
    path('reports/purchases/', PurchaseReportView.as_view(), name='purchase-report'),

    # Invoice
    path("invoice/<int:purchase_id>/", invoice_view, name="invoice_view"),
    path("invoice/<int:purchase_id>/pdf/", invoice_pdf, name="invoice_pdf"),
    path("Order_invoice/<int:order_id>/", Order_invoice, name="Order_invoice"),
    path("Order_invoice/<int:order_id>/pdf/", Order_invoice_pdf, name="Order_invoice_pdf"),
]

