from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # User Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # Admin
    path('admin-login/', views.admin_login, name='admin_login'),
    # path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('myadmin/', views.myadmin, name='myadmin'),
    # --- Product CRUD ---
    # --- Product CRUD (Custom Admin) ---
    path('myadmin/products/add/', views.add_product, name='add_product'),
    path('myadmin/products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('myadmin/products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('myadmin/orders/', views.orders_page, name='orders_page'),

 # --- ✅ Category Management (NEW) ---
    path('myadmin/categories/add/', views.add_category, name='add_category'),
    path('myadmin/categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('myadmin/categories/<int:pk>/delete/', views.delete_category, name='delete_category'),


    
    path('orders/', views.orders_page, name='orders_page'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('delete_all_orders/', views.delete_all_orders, name='delete_all_orders'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
