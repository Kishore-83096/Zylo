# sellers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('sellerreg/', views.seller_registration_view, name='sellerreg'),
    path('reg_done/', views.registration_completed, name='registration_done'),
    path('store/',views.store,name='store'),
    path('Storeprofile/', views.storeprofile, name='storeprofile'),
    path('upload_store_logo/', views.upload_store_logo, name='upload_store_logo'),
    path('update_store_contact/', views.update_store_contact, name='update_store_contact'),
    path('update_store_profile/', views.update_store_profile, name='update_store_profile'),
    path('productsmanagement/', views.product_management, name='product_management'),
    path('add/', views.add_product, name='add_product'),
    path('load-subcategories/', views.load_subcategories, name='load_subcategories'),
    path('update-product/<int:product_id>/', views.update_product, name='update_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('toggle-product-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('addvariant/',views.variantform,name='addvariant'),
    path('variantdet/<int:variant_id>',views.variantdet,name='variantdet'),
    path('update_on_sale/<int:variant_id>/', views.update_on_sale, name='update_on_sale'),
    path('update_variant/<int:variant_id>/', views.update_variant, name='updatevariant'),
    path('delete-variant/<int:variant_id>/', views.delete_variant, name='delete_variant'),
]
