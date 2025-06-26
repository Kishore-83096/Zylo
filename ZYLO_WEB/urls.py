from django.urls import path
from ZYLO_WEB import views

urlpatterns = [
    path('login/', views.account_login, name='account_login'),
    path('logout/', views.account_logout, name='account_logout'),
    path('register/', views.register, name='register'),
    path('home/',views.home,name='home'),
    path('profile/',views.profile,name='profile'),
    path('profile_edit/', views.profile_edit, name='profile_edit'),
    path('profile/picture/edit/', views.profile_picture_edit, name='profile_picture_edit'), # New URL for image editing
    path('profile/contact/edit/', views.contact_info_edit, name='contact_info_edit'), # New URL
    path('profile/address/add/', views.add_saved_address, name='add_saved_address'), # New URL for adding
    path('profile/address/edit/<int:address_id>/', views.edit_saved_address, name='edit_saved_address'), # New URL for editing
    path('profile/address/delete/<int:address_id>/', views.delete_saved_address, name='delete_saved_address'), # New URL for deleting
    path('profile/card/add/', views.add_saved_card, name='add_saved_card'), # New URL for adding card
    path('profile/card/edit/<int:card_id>/', views.edit_saved_card, name='edit_saved_card'), # New URL for editing card
    path('profile/card/delete/<int:card_id>/', views.delete_saved_card, name='delete_saved_card'), # New URL for deleting card
    path('product_var/<int:product_id>/',views.product_var,name='product_var'),
    path('cart/', views.cart, name='cart'), # New URL for cart
    path('cart/<int:variant_id>/',views.add_to_cart,name='add_to_cart'),
    path('remove_from_cart/<int:variant_id>',views.remove_from_cart,name='remove_from_cart'),
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]