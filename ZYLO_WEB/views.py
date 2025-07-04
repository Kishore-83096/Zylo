from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.db import models
from .forms import adminLoginForm,registrationform,ContactInformationForm,UserProfileEditForm,ContactInformation,SavedAddressForm, SavedCardForm, UserProfilepicturesForm
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from .models import ContactInformation,SavedAddress,SavedCard,UserProfilepictures,Wishlist,Cart
from ZYLO_SELLER.models import Category, Product, SellerProfile,storelogo,ProductVariant,SubCategory
from .context_processors import global_context
from django.db import transaction
import json
from django.db.models import Count, Q
from django.contrib.auth import update_session_auth_hash, logout
from .forms import CustomPasswordChangeForm
from .forms import CustomPasswordChangeForm, AccountDeletionForm
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)










# Create your views here.
def zylolandingpageview(request):
    return render(request, 'base/Landingpage.html')










def register(request):
    form = registrationform(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            return redirect('home')  # Redirect to the home page after successful registration
        else:
            messages.error(request, 'Please correct the errors below.')
    
    return render(request, 'ZYLO_WEB/register.html', {'form': form})










def account_login(request):
    if request.method == 'POST':
        form = adminLoginForm(request.POST)  # Bind the form with submitted data
        if form.is_valid():
            email = form.cleaned_data['Email']  # Get the email from the form
            password = form.cleaned_data['password']

            # Retrieve the user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            # Authenticate user using Django's built-in authentication
            if user is not None:
                # Check if the password is correct
                user = authenticate(request, username=user.username, password=password)

                if user is not None:
                    # If the user is authenticated, log them in
                    login(request, user)
                    return redirect('home')  # Redirect to a dashboard page
                else:
                    messages.error(request, "Invalid password.")
            else:
                messages.error(request, "Invalid email address.")
    else:  # GET request, display an empty form
        form = adminLoginForm()

    return render(request, 'ZYLO_WEB/login.html', {'form': form})










def account_logout(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        logout(request)  # Log the user out
        messages.success(request, "You have been logged out successfully.")
    else:
        messages.warning(request, "You are not logged in.")  # Optional: message for not logged in users
    return redirect('account_login')  # Redirect to the login page















def home(request):
    """
    Renders the home page, providing user and seller-related information.
    """
    context = {}

    # Fetch products and their variants
    try:
        products = Product.objects.prefetch_related('variants').all()
        print(f"Products fetched: {products.count()}")
        for product in products:
            product.total_stock = product.variants.aggregate(total_stock=models.Sum('stock'))['total_stock'] or 0

        context['products'] = products
    except Exception as e:
        print(f"Error fetching products and variants: {e}")
        context['products'] = []

    # Fetch available stores with their logos
    try:
        available_stores = SellerProfile.objects.filter(
            status=SellerProfile.SellerStatus.APPROVED
        ).select_related('storelogo').order_by('store_name')  # Fetch approved stores with their logos
        print(f"Available stores fetched: {available_stores.count()}")
        context['available_stores'] = available_stores
    except Exception as e:
        print(f"Error fetching available stores: {e}")
        context['available_stores'] = []

    # Fetch categories associated with sellers
    try:
        categories = Category.objects.all()
        print(f"Categories fetched: {categories.count()}")
        context['categories'] = categories
    except Exception as e:
        print(f"Error fetching categories: {e}")
        context['categories'] = []
    
    
    return render(request, 'ZYLO_WEB/home.html', context)










@login_required
def profile(request):
    """
    Renders the user's profile page, displaying personal information,
    profile picture, contact details, saved addresses, saved cards,
    and seller profile status.
    """
    user = request.user

    # Initialize context with default values
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_name': user.username,
        'is_superuser': user.is_superuser,
        'profile_picture': None,
        'profile_pic_form': None,
        'contact_information': None,
        'contact_info_form': None,
        'saved_addresses': [],
        'saved_address_form': SavedAddressForm(),
        'saved_cards': [],
        'saved_card_form': SavedCardForm(),
        'user_is_seller': False,
        'seller_profile': None,
        'store_status': 'not_registered',  # Default if user is not a seller
        'is_store_approved': False,         # Derived from 'store_status'
        'is_store_rejected': False,         # Derived from 'store_status'
        'store_name': None,
        'logo': None,  # Placeholder for logo if needed
    }

    # --- Fetch or Create User Profile Related Objects ---
    try:
        with transaction.atomic():
            profile_picture, _ = UserProfilepictures.objects.get_or_create(user=user)
            context['profile_picture'] = profile_picture
            context['profile_pic_form'] = UserProfilepicturesForm(instance=profile_picture)
    except Exception as e:
        logger.error(f"Error fetching/creating UserProfilepictures for user {user.id}: {e}")
        # Forms for profile picture will remain None or default, handled in template

    try:
        with transaction.atomic():
            contact_information, _ = ContactInformation.objects.get_or_create(user=user)
            context['contact_information'] = contact_information
            context['contact_info_form'] = ContactInformationForm(instance=contact_information)
    except Exception as e:
        logger.error(f"Error fetching/creating ContactInformation for user {user.id}: {e}")
        # Forms for contact information will remain None or default, handled in template

    # --- Fetch Other Related Objects ---
    try:
        context['saved_addresses'] = SavedAddress.objects.filter(user=user)
    except Exception as e:
        logger.error(f"Error fetching SavedAddress for user {user.id}: {e}")

    try:
        context['saved_cards'] = SavedCard.objects.filter(user=user).order_by('-is_default', 'card_nickname')
    except Exception as e:
        logger.error(f"Error fetching SavedCard for user {user.id}: {e}")

    # Initialize user profile edit form
    context['user_form'] = UserProfileEditForm(instance=user)

    # --- Check SellerProfile status (Refactored) ---
    try:
        seller_profile = SellerProfile.objects.get(user=user)
        context['user_is_seller'] = True
        context['seller_profile'] = seller_profile
        context['store_name'] = seller_profile.store_name

        # Directly use the 'status' field from SellerProfile
        context['store_status'] = seller_profile.status

        # Derive boolean flags for template convenience (if your template uses them)
        context['is_store_approved'] = (seller_profile.status == SellerProfile.SellerStatus.APPROVED)
        context['is_store_rejected'] = (seller_profile.status == SellerProfile.SellerStatus.REJECTED)
        logo_instance = storelogo.objects.filter(store=seller_profile).first()
        context['logo'] = logo_instance
        # You could also add 'is_store_pending' or 'is_store_suspended' if needed
        # context['is_store_pending'] = (seller_profile.status == SellerProfile.SellerStatus.PENDING)
        # context['is_store_suspended'] = (seller_profile.status == SellerProfile.SellerStatus.SUSPENDED)

    except SellerProfile.DoesNotExist:
        # User is authenticated but does not have a SellerProfile
        context['user_is_seller'] = False # Ensure this is accurately set
        context['store_status'] = 'not_registered' # Remains as default
        pass # No seller profile, so no need to change default context values
    except Exception as e:
        logger.error(f"Error retrieving SellerProfile for user {user.id}: {e}")
        # Seller-related context will remain as default ('not_registered') on error

    return render(request, 'ZYLO_WEB/profile.html', context)












@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserProfileEditForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Profile information updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile information. Please check your input.')
            print("User form errors:", user_form.errors)
            return redirect('profile')
    else:
        return redirect('profile')












@login_required
def profile_picture_edit(request):
    profile_picture, created = UserProfilepictures.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile_pic_form = UserProfilepicturesForm(request.POST, request.FILES, instance=profile_picture)
        if profile_pic_form.is_valid():
            profile_pic_form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile picture. Please check your file.')
            print("Profile picture form errors:", profile_pic_form.errors)
            return redirect('profile')
    else:
        return redirect('profile')













@login_required
def contact_info_edit(request):
    try:
        contact_information = ContactInformation.objects.get(user=request.user)
    except ContactInformation.DoesNotExist:
        contact_information = None

    if request.method == 'POST':
        contact_info_form = ContactInformationForm(request.POST, instance=contact_information)
        if contact_info_form.is_valid():
            # If contact_information was None, a new one will be created now
            contact_info_form.instance.user = request.user  # Set user before saving
            contact_info_form.save()
            messages.success(request, 'Contact information updated successfully!')
        else:
            messages.error(request, 'Error updating contact information. Please check your input.')
            print("Contact info form errors:", contact_info_form.errors)
        return redirect('profile')
    else:
        return redirect('profile')











@login_required
def add_saved_address(request):
    if request.method == 'POST':
        form = SavedAddressForm(request.POST)
        if form.is_valid():
            saved_address = form.save(commit=False)
            saved_address.user = request.user
            try:
                saved_address.save()
                messages.success(request, f'Address ({saved_address.get_address_type_display()}) added successfully!')
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    messages.error(request, f"You already have a '{saved_address.get_address_type_display()}' address. Please edit the existing one or choose a different type.")
                else:
                    messages.error(request, f"An error occurred while saving address: {e}")
                print(f"Error saving address: {e}")
            return redirect('profile')
        else:
            messages.error(request, 'Error adding address. Please correct the form.')
            print("Saved address form errors:", form.errors)
            return redirect('profile')
    else:
        return redirect('profile')















@login_required
def edit_saved_address(request, address_id):
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)

    if request.method == 'POST':
        form = SavedAddressForm(request.POST, instance=address)
        if form.is_valid():
            # Check for unique address type only if address_type is changed
            if 'address_type' in form.changed_data and form.cleaned_data['address_type'] != address.address_type:
                if SavedAddress.objects.filter(user=request.user, address_type=form.cleaned_data['address_type']).exclude(id=address_id).exists():
                    messages.error(request, f"You already have a '{form.cleaned_data['address_type'].capitalize()}' address. Cannot change to this type.")
                    # Optionally, you might want to re-render the form with errors here
                    return render(request, 'your_template_name.html', {'form': form, 'address': address}) # <--- Important: render with form for error display
            
            form.save()
            messages.success(request, f'Address ({address.get_address_type_display()}) updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating address. Please correct the form.')
            print("Edit address form errors:", form.errors)
            # Re-render the form with errors so the user can correct them
            return render(request, 'your_template_name.html', {'form': form, 'address': address}) # <--- Important: render with form for error display
    else:  # This block handles GET requests
        form = SavedAddressForm(instance=address) # <--- Instantiate form with existing data
        return render(request, 'your_template_name.html', {'form': form, 'address': address}) # <--- Render the template with the form













@login_required
def delete_saved_address(request, address_id):
    try:
        address = SavedAddress.objects.get(id=address_id, user=request.user)
        address_type_display = address.get_address_type_display()
        address.delete()
        messages.success(request, f'"{address_type_display}" address deleted successfully.')
    except SavedAddress.DoesNotExist:
        messages.error(request, 'Address not found or you do not have permission to delete it.')
    except Exception as e:
        messages.error(request, f'An error occurred while deleting the address: {e}')
    return redirect('profile')












@login_required
def add_saved_card(request):
    if request.method == 'POST':
        form = SavedCardForm(request.POST)
        if form.is_valid():
            saved_card = form.save(commit=False)
            saved_card.user = request.user

            # If this card is set as default, unset previous defaults
            if saved_card.is_default:
                SavedCard.objects.filter(user=request.user, is_default=True).update(is_default=False)

            saved_card.save()
            messages.success(request, f'Card "{saved_card.card_nickname}" added successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error adding card. Please correct the form.')
            print("Saved card form errors:", form.errors)
            return redirect('profile')
    else:
        return redirect('profile')















@login_required
def edit_saved_card(request, card_id):
    card = get_object_or_404(SavedCard, id=card_id, user=request.user)

    if request.method == 'POST':
        form = SavedCardForm(request.POST, instance=card)
        if form.is_valid():
            # If this card is set as default, unset previous defaults
            if form.cleaned_data['is_default']:
                SavedCard.objects.filter(user=request.user, is_default=True).exclude(id=card_id).update(is_default=False)
            form.save()
            messages.success(request, f'Card "{card.card_nickname}" updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating card. Please correct the form.')
            print("Edit card form errors:", form.errors)
            return redirect('profile')
    else:
        return redirect('profile')














@login_required
def delete_saved_card(request, card_id):
    try:
        card = SavedCard.objects.get(id=card_id, user=request.user)
        card_nickname = card.card_nickname
        card.delete()
        messages.success(request, f'Card "{card_nickname}" deleted successfully.')
    except SavedCard.DoesNotExist:
        messages.error(request, 'Card not found or you do not have permission to delete it.')
    except Exception as e:
        messages.error(request, f'An error occurred while deleting the card: {e}')
    return redirect('profile')











def product_var(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Fetch the product
    variants = ProductVariant.objects.filter(product_id=product_id)  # Fetch all variants for the product
    related_products_by_category = Product.objects.filter(category=product.category).exclude(id=product_id)    # Fetch all products in the same category, excluding the current product
    related_products_by_subcategory = Product.objects.filter(subcategory=product.subcategory).exclude(id=product_id)     # Fetch all products in the same subcategory, excluding the current product
    return render(request, 'ZYLO_WEB/product_var.html', {
        'product': product,
        'variants': variants,
        'related_products_by_category': related_products_by_category,
        'related_products_by_subcategory': related_products_by_subcategory,
    })
















from decimal import Decimal
from django.db.models import F

@login_required
def cart_page(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    variant_ids = cart_obj.get_cart_items()
    quantities = cart_obj.get_quantities()

    variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product__seller')


    available_items = []
    unavailable_items = []
    cart_subtotal = Decimal('0.00')

    for variant in variants:
        qty = int(quantities.get(str(variant.id), 1))
        item = {
            'variant': variant,
            'quantity': qty,
        }

        # Check availability
        is_in_stock = variant.stock > 0
        is_on_sale = variant.on_sale  # FIX: use product's `on_sale`

        if is_in_stock and is_on_sale:
            total_price = variant.price * qty
            item['total_price'] = round(total_price, 2)
            cart_subtotal += total_price
            available_items.append(item)
        else:
            reasons = []
            if not is_in_stock:
                reasons.append("Out of Stock")
            if not is_on_sale:
                reasons.append("Not on Sale")
            item['reasons'] = reasons
            unavailable_items.append(item)

    return render(request, 'ZYLO_WEB/cart.html', {
        'available_items': available_items,
        'unavailable_items': unavailable_items,
        'cart_subtotal': round(cart_subtotal, 2),
        'cart_items_count': len(available_items),
    })











@login_required
def add_to_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)

    if cart_obj.add_to_cart(variant.id):
        messages.success(request, f"{variant.product.name} added to cart.")
    else:
        messages.info(request, f"{variant.product.name} is already in your cart.")

    return redirect('cart')














@login_required
def remove_from_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart_obj = get_object_or_404(Cart, user=request.user)

    if cart_obj.remove_from_cart(variant.id):
        # Also remove quantity from session
        quantities = request.session.get('cart_quantities', {})
        if str(variant.id) in quantities:
            del quantities[str(variant.id)]
            request.session['cart_quantities'] = quantities
        messages.success(request, f"{variant.product.name} removed from your cart.")
    else:
        messages.info(request, f"{variant.product.name} was not in your cart.")

    return redirect(request.META.get('HTTP_REFERER', '/'))














@login_required
def ajax_update_cart_quantity(request):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        action = request.POST.get('action')
        
        try:
            variant = ProductVariant.objects.select_related('product').get(id=variant_id)
            max_stock = variant.stock

            cart_obj, _ = Cart.objects.get_or_create(user=request.user)
            quantities = cart_obj.get_quantities()
            current_qty = int(quantities.get(str(variant_id), 1))

            if action == 'increase' and current_qty < max_stock:
                current_qty += 1
            elif action == 'decrease' and current_qty > 1:
                current_qty -= 1

            # Save updated quantity
            cart_obj.set_quantity(variant_id, current_qty)

            # Calculate item total only if available
            is_available = variant.stock > 0 and variant.product.on_sale
            item_total = round(variant.price * current_qty, 2) if is_available else 0

            # Recalculate subtotal only for available items
            cart_items = cart_obj.get_cart_items()
            cart_quantities = cart_obj.get_quantities()
            subtotal = 0

            variants = ProductVariant.objects.filter(id__in=cart_items).select_related('product')
            for v in variants:
                if v.stock > 0 and v.on_sale:
                    qty = int(cart_quantities.get(str(v.id), 1))
                    subtotal += v.price * qty

            return JsonResponse({
                'success': True,
                'quantity': current_qty,
                'stock': variant.stock,
                'item_total': f"{item_total:.2f}",
                'cart_subtotal': f"{subtotal:.2f}",
                'cart_count': len([v for v in variants if v.stock > 0 and v.product.on_sale])
            })

        except ProductVariant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Variant not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})







@login_required
def wishlist_view(request):
    user = request.user
    wishlist_obj, created = Wishlist.objects.get_or_create(user=user)
    variant_ids = wishlist_obj.get_wishlist_items()
    variants = ProductVariant.objects.filter(id__in=variant_ids)
    return render(request, 'ZYLO_WEB/wishlist.html', {'variants': variants})












@login_required
def add_to_wishlist(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    user = request.user

    wishlist_obj, created = Wishlist.objects.get_or_create(user=user)
    added = wishlist_obj.add_to_wishlist(variant.id)

    if added:
        messages.success(request, "Item added to wishlist.")
    else:
        messages.info(request, "Item is already in your wishlist.")

    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', '/'))











@login_required
def remove_from_wishlist(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    wishlist_obj, created = Wishlist.objects.get_or_create(user=request.user)

    removed = wishlist_obj.remove_from_wishlist(variant.id)

    if removed:
        # Optionally add a success message
        from django.contrib import messages
        messages.success(request, "Item removed from wishlist.")
    else:
        messages.info(request, "Item was not in your wishlist.")

    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', '/wishlist/'))









def category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    subcat = SubCategory.objects.filter(category=category_id)
    products = Product.objects.filter(category=category_id)\
        .select_related('seller').prefetch_related('variants')# Single optimized query to get all required data

    return render(request, 'ZYLO_WEB/category.html', {
        'category': category,
        'subcat': subcat,
        'products': products,
    })











def subcategory(request, subcategory_id,name):
    products = Product.objects.filter(subcategory=subcategory_id)\
        .select_related('seller').prefetch_related('variants')# Single optimized query to get all required data
    return render(request, 'ZYLO_WEB/subcategory.html',{'products':products,'name':name})










def store_preview(request, store_id):
    store = get_object_or_404(SellerProfile, id=store_id)
    products = Product.objects.filter(seller=store_id).select_related('category')
    
    # Get categories and annotate with product count
    categories = Category.objects.filter(
        products__seller=store_id
    ).distinct().annotate(
        product_count=Count('products', filter=Q(products__seller=store_id))
    )
    
    return render(request, 'ZYLO_WEB/storepreview.html', {
        'store': store,
        'products': products,
        'categories': categories
    })










@login_required
def account_settings(request):
    user = request.user
    last_login = user.last_login

    password_form = CustomPasswordChangeForm(user)
    deletion_form = AccountDeletionForm()

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('account_settings')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif 'delete_account' in request.POST:
            deletion_form = AccountDeletionForm(request.POST)
            if deletion_form.is_valid():
                email = deletion_form.cleaned_data['email']
                password = deletion_form.cleaned_data['password']

                if email != user.email:
                    messages.error(request, "The email you entered doesn't match your account.")
                else:
                    authenticated_user = authenticate(username=user.username, password=password)
                    if authenticated_user:
                        if SellerProfile.objects.filter(user=user).exists():
                            messages.error(request, "Account deletion is restricted for registered sellers.")
                        else:
                            user.delete()
                            logout(request)
                            messages.success(request, 'Your account has been deleted.')
                            return redirect('home')
                    else:
                        messages.error(request, "Invalid password. Please try again.")

    return render(request, 'ZYLO_WEB/settings.html', {
        'form': password_form,
        'last_login': last_login,
        'deletion_form': deletion_form
    })
