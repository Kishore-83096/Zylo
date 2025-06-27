import json
from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import render, redirect,HttpResponseRedirect, get_object_or_404
from django.urls import reverse
from .forms import SellerRegistrationForm, storelogoForm,SellerContactForm, ProductForm,SellerProfileForm,ProductVariantForm
from ZYLO_WEB.models import UserProfilepictures
from django.contrib.auth.decorators import login_required
from .models import SellerProfile,storelogo,Category,SubCategory, Product,ProductVariant
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from ZYLO_WEB.context_processors import global_context
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt



@login_required
def seller_registration_view(request):
    form = SellerRegistrationForm()  # Initialize form outside the conditional to ensure it's always available

    first_name = ''  # Initialize variables for user data to avoid potential NameError
    last_name = ''  # Initialize variables for user data to avoid potential NameError
    is_superuser = False  # Initialize variables for user data to avoid potential NameError
    profile_picture = None  # This will hold the UserProfilepictures instance

    if request.user.is_authenticated:
        first_name = request.user.first_name  # Fetch the first name of the authenticated user
        last_name = request.user.last_name  # Fetch the last name of the authenticated user
        is_superuser = request.user.is_superuser  # Check if the authenticated user is a superuser

        profile_picture, created = UserProfilepictures.objects.get_or_create(user=request.user)  # Get or create the UserProfilepictures instance for the current user

    if request.method == 'POST':  # Handle form submission
        form = SellerRegistrationForm(request.POST)  # Bind the form with POST data
        if form.is_valid():  # Check if the form is valid
            seller_profile = form.save(commit=False)  # Save the form without committing to assign the user
            seller_profile.user = request.user  # Assign the current logged-in user to the seller profile
            seller_profile.save()  # Save the seller profile to the database
            return redirect('registration_done')  # Redirect to a success page after successful registration

    context = {
        'form': form,  # Pass the form instance to the template
        'first_name': first_name,  # Pass the first name to the template
        'last_name': last_name,  # Pass the last name to the template
        'is_superuser': is_superuser,  # Pass the superuser status to the template
        'profile_picture': profile_picture,  # Pass the UserProfilepictures instance directly
    }

    return render(request, 'ZYLO_SELLER/sellerreg.html', context)  # Render the template, passing the context




@login_required
def registration_completed(request):
    """
    Renders the store registration success page, displaying the specific
    approval status of the user's SellerProfile.
    """
    user = request.user  # Get the currently logged-in user
    profile_picture_obj = None  # Initialize profile_picture_obj to None

    try:
        profile_picture_obj = UserProfilepictures.objects.get(user=user)  # Get the UserProfilepictures instance for the user
    except UserProfilepictures.DoesNotExist:
        profile_picture_obj = UserProfilepictures.objects.create(user=user)  # Create a default UserProfilepictures instance if none exists

    user_store = None  # Initialize user_store to None
    store_status = 'not_found'  # Default status if no SellerProfile is found for the user
    is_rejected = False  # Flag to indicate if the store status is rejected
    is_suspended = False  # Flag to indicate if the store status is suspended

    try:
        user_store = SellerProfile.objects.get(user=user)  # Attempt to retrieve the SellerProfile associated with the user
        store_status = user_store.status  # Get the status from the SellerProfile instance
        is_rejected = (store_status == SellerProfile.SellerStatus.REJECTED)  # Check if the status is rejected
        is_suspended = (store_status == SellerProfile.SellerStatus.SUSPENDED)  # Check if the status is suspended
    except SellerProfile.DoesNotExist:
        pass  # If no SellerProfile is found, store_status remains 'not_found'

    context = {
        'profile_picture': profile_picture_obj,  # Pass the profile picture object to the template
        'user_store': user_store,  # Pass the user store object to the template
        'store_status': store_status,  # Pass the store status to the template
        'is_rejected': is_rejected,  # Pass the rejection flag to the template
        'is_suspended': is_suspended,  # Pass the suspension flag to the template
        'is_superuser': user.is_superuser  # Pass the superuser status to the template
    }
    return render(request, 'ZYLO_SELLER/reg_success.html', context)  # Render the template with the context





@login_required
def store(request):  # Displays the seller's store page. Redirects to seller registration if no SellerProfile exists. Handles the display of the store logo gracefully if it exists.
    store_name = "Your Store"  # Default value if no profile found (though a redirect will happen)
    seller_profile_exists = False  # Flag to indicate if a SellerProfile was found
    is_superuser = request.user.is_superuser  # Check if the user is a superuser
    logo_instance = None  # Initialize logo_instance to None
    total_products = 0  # Initialize total product count
    total_active_products = 0  # Initialize total active product count
    user_products = []  # Initialize user products list

    try:
        seller_profile = SellerProfile.objects.get(user=request.user)  # Attempt to fetch the SellerProfile for the logged-in user
        store_name = seller_profile.store_name  # Get the store name from the profile
        seller_profile_exists = True  # Set the flag to True if a SellerProfile is found

        logo_instance = storelogo.objects.filter(store=seller_profile).first()  # Safely retrieve the logo

        products = seller_profile.products.all()  # Fetch all products associated with the seller
        total_products = products.count()  # Count total products
        total_active_products = products.filter(on_sale=True).count()  # Count active products
        user_products = products  # Assign the user's products to the variable

    except SellerProfile.DoesNotExist:
        return redirect('sellerreg')  # If no SellerProfile exists for this user, redirect them to register

    context = {
        'store_name': store_name,  # Pass the store name to the template
        'seller_profile_exists': seller_profile_exists,  # Pass the flag to the template
        'logo': logo_instance,  # Pass the logo instance (will be None if not found)
        'is_superuser': is_superuser,  # Include superuser status, often useful for navigation
        'total_products': total_products,  # Total number of products
        'total_active_products': total_active_products,  # Total number of active products
        'user_products': user_products,  # Pass the user's products to the template
    }
    return render(request, 'ZYLO_SELLER/store.html', context)  # Render the template with the context






@login_required
def storeprofile(request):
    """
    Handles displaying the seller's store profile, including store name and logo.
    Initializes forms for store logo upload, contact details update, and core store info update.
    """
    seller_profile = None  # Initialize seller_profile to None
    logo_instance = None  # Initialize logo_instance to None

    # --- Fetch existing data for display ---
    try:
        seller_profile = SellerProfile.objects.get(user=request.user)
        print(seller_profile.id)
        products = seller_profile.products.all()
        total_products = products.count()  # Fetch the SellerProfile for the logged-in user
        try:
            logo_instance = storelogo.objects.get(store=seller_profile)  # Attempt to get store logo if seller_profile exists
        except storelogo.DoesNotExist:
            print(f"No storelogo found for seller: {seller_profile.store_name}")  # Debugging log for missing logo
            pass  # No logo, logo_instance remains None
    except SellerProfile.DoesNotExist:
        messages.info(request, "Please complete your basic store information to get started.")  # Inform the user to complete their profile
        pass  # If no SellerProfile, the user needs to set it up

    # --- Handle POST requests for form submissions ---
    if request.method == 'POST':  # Check if the request method is POST
        if 'update_store_info' in request.POST:  # Handle SellerProfileForm submission
            profile_form = SellerProfileForm(request.POST, instance=seller_profile)  # Bind the form with POST data
            if profile_form.is_valid():  # Check if the form is valid
                new_seller_profile = profile_form.save(commit=False)  # Save the form data without committing
                if not seller_profile:  # If it's a brand new profile
                    new_seller_profile.user = request.user  # Assign the current user
                new_seller_profile.save()  # Save the seller profile
                messages.success(request, "Store information updated successfully!")  # Success message
                return redirect('storeprofile')  # Redirect to refresh the page with updated data
            else:
                messages.error(request, "Error updating store information. Please check the form.")  # Error message
        elif 'upload_logo' in request.POST:  # Handle storelogoForm submission
            if seller_profile:  # Ensure seller_profile exists before trying to upload a logo
                logo_form = storelogoForm(request.POST, request.FILES, instance=logo_instance)  # Bind the form with POST data and files
                if logo_form.is_valid():  # Check if the form is valid
                    new_logo = logo_form.save(commit=False)  # Save the form data without committing
                    new_logo.store = seller_profile  # Link logo to the seller profile
                    new_logo.save()  # Save the logo
                    messages.success(request, "Store logo uploaded successfully!")  # Success message
                    return redirect('storeprofile')  # Redirect to refresh the page
                else:
                    messages.error(request, "Error uploading logo. Please check the file.")  # Error message
            else:
                messages.error(request, "Please create your store profile before uploading a logo.")  # Error message for missing profile
        elif 'update_contact_info' in request.POST:  # Handle SellerContactForm submission
            contact_form = SellerContactForm(request.POST, instance=seller_profile)  # Bind the form with POST data
            if contact_form.is_valid():  # Check if the form is valid
                contact_form.save()  # Save the contact information
                messages.success(request, "Contact information updated successfully!")  # Success message
                return redirect('storeprofile')  # Redirect to refresh the page
            else:
                messages.error(request, "Error updating contact information. Please check the form.")  # Error message
        else:
            messages.warning(request, "An unknown form was submitted.")  # Warning message for unknown form

    # --- Initialize forms for display (GET request or after POST with errors) ---
    profile_form = SellerProfileForm(instance=seller_profile)  # Initialize SellerProfileForm
    logo_form = storelogoForm(instance=logo_instance)  # Initialize storelogoForm
    contact_form = SellerContactForm(instance=seller_profile)  # Initialize SellerContactForm

    context = {
        'seller_profile': seller_profile,  # Pass the seller profile to the template
        "store_name": seller_profile.store_name if seller_profile else "Your Store",  # Default name if no profile
        "logo": logo_instance,  # Pass the logo instance to the context
        "profile_form": profile_form,  # Pass the SellerProfileForm to the context
        "logo_form": logo_form,  # Pass the storelogoForm to the context
        "contact_form": contact_form,  # Pass the SellerContactForm to the context
        "business_email": seller_profile.business_email if seller_profile else None,  # Pass business email
        "store_description": seller_profile.store_description if seller_profile else None,  # Pass store description
        'store_category': seller_profile.store_category if seller_profile else None,  # Pass store category
        "store_address1": seller_profile.address_line1 if seller_profile else None,  # Pass address line 1
        "store_address2": seller_profile.address_line2 if seller_profile else None,  # Pass address line 2
        "store_city": seller_profile.city if seller_profile else None,  # Pass city
        "store_state": seller_profile.state_province if seller_profile else None,  # Pass state/province
        "store_zip": seller_profile.zip_code if seller_profile else None,  # Pass zip code
        "store_country": seller_profile.country if seller_profile else None,  # Pass country
        "store_phone": seller_profile.phone_number if seller_profile else None,  # Pass phone number
        'is_superuser': request.user.is_superuser,  # Include superuser status for template logic
        'total_products': total_products,  # Pass the total number of products
    }
    return render(request, 'ZYLO_SELLER/storeprofile.html', context)  # Render the template with the context






@login_required
def upload_store_logo(request):
    """
    Handles the upload/update of a seller's store logo.
    This view expects a POST request.
    """
    seller_profile = get_object_or_404(SellerProfile, user=request.user)  # Fetch the SellerProfile for the logged-in user
    logo_instance = None  # Initialize logo_instance to None
    try:
        logo_instance = storelogo.objects.get(store=seller_profile)  # Attempt to fetch the existing store logo
    except storelogo.DoesNotExist:
        pass  # No existing logo, form will create a new one

    if request.method == 'POST':  # Check if the request method is POST
        form = storelogoForm(request.POST, request.FILES, instance=logo_instance)  # Bind the form with POST data and files
        if form.is_valid():  # Check if the form is valid
            new_logo = form.save(commit=False)  # Save the form data without committing
            new_logo.store = seller_profile  # Link the logo to the seller profile
            new_logo.save()  # Save the logo
            messages.success(request, 'Store logo updated successfully!')  # Success message
            return redirect('storeprofile')  # Redirect to the store profile page
        else:
            messages.error(request, 'Error uploading logo. Please check the form.')  # Error message
            print("Logo form errors:", form.errors)  # Debugging log for form errors
            return redirect('storeprofile')  # Redirect back to the store profile page
    else:
        messages.error(request, 'Invalid request method for logo upload.')  # Error message for invalid request method
        return redirect('storeprofile')  # Redirect to the store profile page
    



 
@login_required
def update_store_contact(request):
    """
    Handles the update of a seller's contact information.
    This view expects a POST request.
    """
    seller_profile = get_object_or_404(SellerProfile, user=request.user)  # Fetch the SellerProfile for the logged-in user

    if request.method == 'POST':  # Check if the request method is POST
        form = SellerContactForm(request.POST, instance=seller_profile)  # Bind the form with POST data
        if form.is_valid():  # Check if the form is valid
            form.save()  # Save the contact information
            messages.success(request, 'Your contact details have been updated successfully!')  # Success message
            return redirect('storeprofile')  # Redirect to the store profile page
        else:
            messages.error(request, 'Please correct the errors below.')  # Error message
            print("Contact form errors:", form.errors)  # Debugging log for form errors
            return redirect('storeprofile')  # Redirect back to the store profile page
    else:
        messages.error(request, 'Invalid request method for contact update.')  # Error message for invalid request method
        return redirect('storeprofile')  # Redirect to the store profile page
    



@login_required
def update_store_profile(request):
    print("Update store profile view called")  # Debugging log
    sellerProfile = get_object_or_404(SellerProfile, user=request.user)  # Fetch the SellerProfile for the logged-in user
    if request.method == 'POST':  # Check if the request method is POST
        form = SellerProfileForm(request.POST, instance=sellerProfile)  # Bind the form with POST data
        if form.is_valid():  # Check if the form is valid
            form.save()  # Save the updated store profile
            messages.success(request, 'Your store profile has been updated successfully!')  # Success message
            return redirect('storeprofile')  # Redirect to the store profile page
        else:
            messages.error(request, 'Please correct the errors below.')  # Error message
            print("Profile form errors:", form.errors)  # Debugging log for form errors
            return redirect('storeprofile')  # Redirect back to the store profile page
    else:
        messages.error(request, 'Invalid request method for profile update.')  # Error message for invalid request method
        return redirect('storeprofile')  # Redirect to the store profile page




def product_management(request):
    """
    Handles product management for sellers.
    Passes product data to the template, including pre-fetched product variants.
    """
    try:
        seller_profile = SellerProfile.objects.get(user=request.user)
        products = seller_profile.products.prefetch_related('variants').all()

        # Annotate each product with the total stock of its variants
        products_with_stock = []
        for product in products:
            total_stock = product.variants.aggregate(total_stock=Sum('stock'))['total_stock'] or 0
            products_with_stock.append({
                'product': product,
                'stock': total_stock
            })
        
        product_count=products.count()

    except SellerProfile.DoesNotExist:
        messages.error(request, 'You must have a seller profile to manage products.')
        return redirect('sellerreg')

    onsale_product_count = products.filter(on_sale=True).count()
    variant_count = sum(product.variants.count() for product in products)

    context = {
        'seller_profile': seller_profile,
        'products_with_stock': products_with_stock,  # Pass products with stock info
        'onsale_product': onsale_product_count,
        'variant_count': variant_count,
        'product_count': product_count
    }

    return render(request, 'ZYLO_SELLER/manage_products.html', context)




@login_required
@require_POST  # Ensures this view only accepts POST requests
def toggle_product_status(request, product_id):
    print(f"Toggling product status for product ID: {product_id}")  # Debugging log
    """
    Toggles the on_sale status of a product and its variants via an AJAX POST request.
    """
    try:
        # Get the seller profile and ensure the product belongs to this seller
        seller = SellerProfile.objects.get(user=request.user)
        product = get_object_or_404(Product, pk=product_id, seller=seller)
    except SellerProfile.DoesNotExist:
        return JsonResponse({'error': 'Seller profile not found.'}, status=403)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found or you do not have permission.'}, status=404)

    # --- Simplified Toggle Logic ---
    # Flip the current boolean status of the product
    product.on_sale = not product.on_sale
    product.save()

    # Update the on_sale status of all associated variants
    product.variants.update(on_sale=product.on_sale)

    # Return a success response with the new status
    # This allows the frontend to accurately update the toggle switch
    return JsonResponse({
        'success': True,
        'message': f'"{product.name}" status updated.',
        'on_sale': product.on_sale  # Send the new status back
    })







@login_required
def add_product(request):
    """
    View to handle adding a new product.
    """
    print("Add product view called")  # Debugging log
    logo_instance = None  # Initialize logo_instance to avoid undefined variable errors

    try:
        # Check if the user has an associated SellerProfile
        seller_profile = SellerProfile.objects.get(user=request.user)
        logo_instance = storelogo.objects.filter(store=seller_profile).first()  # Get the logo if it exists
    except SellerProfile.DoesNotExist:
        print("No SellerProfile found for the user.")  # Debugging log
        messages.error(request, 'You must have a seller profile to add a product.')
        return redirect('sellerreg')  # Redirect to seller registration if no profile exists

    if request.method == 'POST':
        print("POST request received")  # Debugging log
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller_profile  # Assign the seller profile to the product
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect(reverse('add_product'))
        else:
            print("Form is invalid. Errors:", form.errors)  # Debugging log
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    # Render the template with the form and additional context
    return render(request, 'ZYLO_SELLER/add_product.html', {
        'form': form,
        'is_superuser': request.user.is_superuser,
        'logo': logo_instance,  # Pass the store logo instance to the template
    })






@login_required
def load_subcategories(request):
    """
    AJAX view to load subcategories based on the selected category.
    """
    category_id = request.GET.get('category_id')  # Get the category ID from the request
    if category_id:  # Check if a category ID is provided
        subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')  # Fetch subcategories for the given category
        return JsonResponse(list(subcategories.values('id', 'name')), safe=False)  # Return subcategories as JSON
    return JsonResponse({'error': 'Invalid category ID'}, status=400)  # Return an error response if category ID is invalid








@login_required
def update_product(request, product_id):
    """
    View to handle updating a product.
    Ensures that only the seller who owns the product can update it.
    """
    try:
        seller_profile = SellerProfile.objects.get(user=request.user)  # Fetch the seller profile of the logged-in user
    except SellerProfile.DoesNotExist:
        messages.error(request, 'You must have a seller profile to update a product.')  # Error message if no seller profile exists
        return redirect('sellerreg')  # Redirect to seller registration page

    product = get_object_or_404(Product, id=product_id, seller=seller_profile)  # Fetch the product and ensure it belongs to the logged-in seller

    if request.method == 'POST':  # Check if the request method is POST
        form = ProductForm(request.POST, request.FILES, instance=product)  # Bind the form with POST data and files
        if form.is_valid():  # Check if the form is valid
            form.save()  # Save the updated product
            messages.success(request, f'Product "{product.name}" updated successfully!')  # Success message
            return redirect('product_management')  # Redirect to product management page
        else:
            messages.error(request, 'Please correct the errors below.')  # Error message for invalid form
            print("Form errors:", form.errors)  # Debugging log for form errors
    else:
        form = ProductForm(instance=product)  # Initialize the form with the product instance

    return render(request, 'ZYLO_SELLER/update_product.html', {  # Render the template with the form and additional context
        'form': form,  # Pass the form instance to the template
        'product': product,  # Pass the product instance to the template
        'is_superuser': request.user.is_superuser,  # Pass the superuser status to the template
    })





@login_required
def delete_product(request, product_id):
    print("Delete product view called")  # Debugging log
    try:
        print(f"Attempting to delete product with ID: {product_id}")  # Debugging log
        seller_profile = SellerProfile.objects.get(user=request.user)  # Fetch the seller profile of the logged-in user
        print(f"Seller profile found: {seller_profile.store_name}")  # Debugging log
    except SellerProfile.DoesNotExist:
        messages.error(request, 'You must have a seller profile to delete a product.')  # Error message if no seller profile exists
        return redirect('sellerreg')  # Redirect to seller registration page

    product = get_object_or_404(Product, id=product_id, seller=seller_profile)  # Fetch the product and ensure it belongs to the logged-in seller
    print(f"Product found: {product.name}, Seller: {product.seller}")  # Debugging log

    if request.method == 'POST':  # Check if the request method is POST
        try:
            product.delete()  # Delete the product
            messages.success(request, 'Product deleted successfully!')  # Success message
            return HttpResponseRedirect(reverse('product_management'))  # Redirect to product management page
        except Exception as e:
            print(f"Error deleting product: {e}")  # Debugging log for errors
            messages.error(request, 'An error occurred while deleting the product.')  # Error message
            return redirect('product_management')

    print("Request method is not POST")  # Debugging log
    return redirect('product_management')  # Redirect to product management page if not a POST request





@login_required
def variantform(request):
    context = global_context(request)
    print("Variant form view called")  # Debugging log

    try:
        seller_profile = SellerProfile.objects.get(user=request.user)  # Get the seller profile for the logged-in user
    except SellerProfile.DoesNotExist:
        messages.error(request, 'You must have a seller profile to add a variant.')
        return redirect('sellerreg')  # Redirect to seller registration if no profile exists

    if request.method == 'POST':
        form = ProductVariantForm(request.POST, request.FILES, seller=seller_profile)  # Pass the seller to the form
        if form.is_valid():
            variant = form.save(commit=False)  # Save the form without committing to the database
            variant.save()  # Save the variant to the database
            messages.success(request, 'Variant added successfully!')
            return redirect('product_management')  # Redirect to product management page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductVariantForm(seller=seller_profile)  # Pass the seller to the form for GET requests

    return render(request, 'ZYLO_SELLER/variantsform.html', {
        'form': form,
        'context': context,
    })






@login_required
def variantdet(request, variant_id):
    context = global_context(request)
    print(variant_id)
    print("Variant details view called")  # Debugging log

    # Fetch the current variant
    variant = get_object_or_404(ProductVariant, id=variant_id)

    # Fetch other variants with the same product_id, excluding the current variant
    other_variants = ProductVariant.objects.filter(product=variant.product).exclude(id=variant_id)

    return render(request, 'ZYLO_SELLER/Variant_details.html', {
        "context": context,
        "variant": variant,
        "other_variants": other_variants
    })






@require_POST
@login_required
@csrf_exempt  # Only use this if you're having CSRF issues - better to properly handle CSRF
def update_on_sale(request, variant_id):
    print('update _on_sale view called')  # Debugging log
    try:
        variant = ProductVariant.objects.get(id=variant_id)
        data = json.loads(request.body)
        variant.on_sale = data.get('on_sale', False)
        variant.save()
        return JsonResponse({'status': 'success', 'on_sale': variant.on_sale})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Variant not found'}, status=404)
    





@login_required
def update_variant(request, variant_id):
    context = global_context(request)
    print('update_variant view called')  # Debugging log

    try:
        # Fetch the variant or return a 404 if not found
        variant = ProductVariant.objects.get(id=variant_id)
        print(variant)
    except ProductVariant.DoesNotExist:
        print(f"Variant with ID {variant_id} does not exist.")  # Debugging log
        messages.error(request, "The requested variant does not exist.")
        return redirect('home')

    # Correctly fetch the seller profile
    try:
        seller = request.user.seller_profile  # Use the correct related name
        print(seller)
    except SellerProfile.DoesNotExist:
        messages.error(request, "You do not have a seller profile.")
        return redirect('home')

    if request.method == 'POST':
        print("post")
        # Initialize the form with POST data and the existing variant instance
        form = ProductVariantForm(request.POST, request.FILES, instance=variant, seller=seller)
        if form.is_valid():
            print('valid')
            form.save()
            messages.success(request, "Variant updated successfully!")
            return redirect('variantdet', variant_id=variant_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize the form with the existing variant instance for GET requests
        form = ProductVariantForm(instance=variant, seller=seller)

    # Render the template with the form and context
    return render(request, 'ZYLO_SELLER/updatevariant.html', {
        'form': form,
        'variant': variant,
        'context': context,
    })






@login_required
def delete_variant(request, variant_id):
    print("Delete variant view called")  # Debugging log
    try:
        print(f"Attempting to delete variant with ID: {variant_id}")  # Debugging log
        seller_profile = SellerProfile.objects.get(user=request.user)  # Fetch the seller profile of the logged-in user
        print(f"Seller profile found: {seller_profile.store_name}")  # Debugging log
    except SellerProfile.DoesNotExist:
        messages.error(request, 'You must have a seller profile to delete a variant.')  # Error message if no seller profile exists
        return redirect('sellerreg')  # Redirect to seller registration page

    # Fetch the variant and ensure it belongs to a product owned by the logged-in seller
    variant = get_object_or_404(ProductVariant, id=variant_id, product__seller=seller_profile)
    print(f"Variant found: {variant.model_name}, Product: {variant.product.name}")  # Debugging log

    if request.method == 'POST':  # Check if the request method is POST
        try:
            variant.delete()  # Delete the variant
            messages.success(request, f'Variant "{variant.model_name}" deleted successfully!')  # Success message
            return HttpResponseRedirect(reverse('product_management'))  # Redirect to product management page
        except Exception as e:
            print(f"Error deleting variant: {e}")  # Debugging log for errors
            messages.error(request, 'An error occurred while deleting the variant.')  # Error message
            return redirect('product_management')

    print("Request method is not POST")  # Debugging log
    return redirect('product_management')  # Redirect to product management page if not a POST request






