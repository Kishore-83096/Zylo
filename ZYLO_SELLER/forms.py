# sellers/forms.py
from django import forms
from .models import SellerProfile,storelogo,Product, Category, SubCategory,ProductVariant

class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        # List the fields you want the seller to fill out during registration
        fields = [
            'store_name',
            'store_description',
            'phone_number',
            'business_email',
            'address_line1',
            'address_line2',
            'city',
            'state_province',
            'zip_code',
            'country',
            'store_category',
        ]
        widgets = {
            'store_description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'store_name': 'Your Store Name',
            # Customize other labels as needed
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap/Tailwind CSS classes or other styling if needed
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})



class storelogoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the 'form-control' class to the image field's widget
        self.fields['image'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = storelogo
        fields = ['image'] # We only want the user to modify the image here


from django import forms
from .models import SellerProfile # Assuming your SellerProfile model is in a 'models.py' file in the same app

class SellerContactForm(forms.ModelForm):
    """
    A form for updating only the contact details of a SellerProfile.
    """
    class Meta:
        model = SellerProfile
        fields = [
            'phone_number',
            'business_email',
            'address_line1',
            'address_line2',
            'city',
            'state_province',
            'zip_code',
            'country',
        ]
        labels = {
            'phone_number': 'Phone Number',
            'business_email': 'Business Email',
            'address_line1': 'Address Line 1',
            'address_line2': 'Address Line 2 (Optional)',
            'city': 'City',
            'state_province': 'State/Province',
            'zip_code': 'Zip Code',
            'country': 'Country',
        }
        widgets = {
            'address_line1': forms.TextInput(attrs={'placeholder': 'Street address, P.O. Box'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, unit, building, floor, etc.'}),
        }

# Define the SellerProfileForm using Django's ModelForm
class SellerProfileForm(forms.ModelForm):
    """
    A Django ModelForm for the SellerProfile model,
    including only 'store_name', 'store_description', and 'store_category'.
    """
    class Meta:
        # Link the form to the SellerProfile model
        model = SellerProfile
        # Specify the fields that should be included in this form
        fields = ['store_name', 'store_description', 'store_category']

    # You can add custom validation or widgets here if needed
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example of adding a custom placeholder for store_name
        self.fields['store_name'].widget.attrs.update({'placeholder': 'e.g., My Awesome Store'})
        self.fields['store_description'].widget.attrs.update({'placeholder': 'Tell us about your products...'})
        self.fields['store_category'].widget.attrs.update({'placeholder': 'e.g., Electronics, Fashion, Books'})





class ProductForm(forms.ModelForm):
    """
    Enhanced form for creating and updating Product instances.
    """
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'subcategory',
            'image',
            'description',
            'brand',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-md',
                'placeholder': 'Enter product name',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control rounded-md',
                'placeholder': 'Enter price (e.g., 19.99)',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control rounded-md',
            }),
            'subcategory': forms.Select(attrs={
                'class': 'form-control rounded-md',
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            }),
        }
        labels = {
            'name': 'Product Name',
            'price': 'Price',
            'image': 'Product Image',
        }
        help_texts = {
            'category': 'Select the main category for this product.',
            'subcategory': 'Optional: Select a subcategory.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically filter categories and subcategories
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Add dynamic filtering for subcategories based on the selected category
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # Invalid input; fallback to empty queryset
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(category=self.instance.category).order_by('name')







class ProductVariantForm(forms.ModelForm):
    """
    Form for creating and updating ProductVariant instances.
    It allows selection of an existing Product and provides fields
    for variant-specific details like color, size, price, etc.
    """
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),  # Default to an empty queryset
        empty_label="--- Select a Product ---",
        help_text="Select the parent product for this variant."
    )

    class Meta:
        model = ProductVariant
        fields = [
            'product',
            'variant_name',
            'model_name',
            'color',
            'color_hex',
            'size',
            'sku',
            'price',
            'stock',
            'variant_image',
            'on_sale',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'product': 'Associated Product',
            'variant_image': 'Variant Image',
        }
        help_texts = {
            'product': 'Choose the main product to which this variant belongs.',
            'variant_name': "Required:The display name of this variant (e.g., 'Productname(product name) or series name + color and size (Black 256GB)').",
            'model_name': 'Optional: A specific model name for this variant.',
            'color': 'E.g., Red, Blue, Black.',
            'color_hex':'#333',
            'size': 'E.g., S, M, L, XL, or shoe sizes.',
            'sku': 'Unique identifier for inventory tracking.',
            'price': 'The selling price for this specific variant.',
            'stock': 'Current quantity in stock.',
            'on_sale': 'Check if this variant is currently on sale.',

        }

    def __init__(self, *args, **kwargs):
        seller = kwargs.pop('seller', None)  # Extract the seller from kwargs
        super().__init__(*args, **kwargs)
        if seller:
            # Filter the product dropdown to only show products belonging to the seller
            self.fields['product'].queryset = Product.objects.filter(seller=seller).order_by('name')

         # Prepopulate the product field with the current product if an instance is provided
        if self.instance and self.instance.pk:
            self.fields['product'].initial = self.instance.product