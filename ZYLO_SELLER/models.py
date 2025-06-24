from django.db import models
from django.conf import settings # Always use settings.AUTH_USER_MODEL for user ForeignKey/OneToOneField
from PIL import Image,ImageDraw
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import os
from django.utils.translation import gettext_lazy as _

class SellerProfile(models.Model):
    """
    Represents a seller's profile and store information.
    Each user can have at most one seller profile.
    """
    class SellerStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        verbose_name="Associated User Account"
    )

    store_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="The unique name of your store."
    )
    store_description = models.TextField(
        blank=True,
        null=True,
        help_text="A brief description of your store and what you sell."
    )

    store_category = models.CharField(max_length=255, blank=True, null=True)

    # Contact Information for the seller's business
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    business_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Business contact email (different from login email if preferred)."
    )

    # Business Address (simplified for now, can be a separate model if complex)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # --- Replaced approval status with a single CharField with choices ---
    status = models.CharField(
        max_length=20, # Max length based on the longest choice value, e.g., 'suspended'
        choices=SellerStatus.choices,
        default=SellerStatus.PENDING, # Set 'pending' as the default status
        help_text="The approval status of the seller's profile."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
        

    class Meta:
        verbose_name = "Seller Profile"
        verbose_name_plural = "Seller Profiles"

    def __str__(self):
        return f"Seller Profile for {self.user.username} - {self.store_name} ({self.get_status_display()})"

    # You might add methods here, e.g., to check if the profile is complete
    def is_complete(self):
        return all([
            self.store_name,
            self.phone_number, # Or more critical fields
            self.address_line1,
            self.city,
            self.country,
        ])
    
    
class storelogo(models.Model):
    store = models.OneToOneField(SellerProfile, on_delete=models.CASCADE,)
    image = models.ImageField(
        upload_to='storelogo/',
        default='storelogo/default.jpg'
    )

    def __str__(self):
        return f'{self.store.user.username} Profile'

    # Override save method to resize images AND delete old ones
    def save(self, *args, **kwargs):
        # Check if the instance already exists (i.e., it's an update, not a creation)
        if self.pk: # self.pk will be True if the object already has an ID in the database
            try:
                # Get the old instance from the database
                old_instance = storelogo.objects.get(pk=self.pk)
                # Check if the image path has changed and if the old image is not the default
                if old_instance.image and old_instance.image.path != self.image.path:
                    # Make sure the old image is not the default.jpg
                    if 'default.jpg' not in old_instance.image.path:
                        # Delete the old image file if it exists
                        if os.path.exists(old_instance.image.path):
                            os.remove(old_instance.image.path)
                            print(f"Old image deleted: {old_instance.image.path}")
            except storelogo.DoesNotExist:
                # This can happen if the object is new, or there's a race condition
                pass # No old image to delete if it's a new instance

        super().save(*args, **kwargs) # Save the new image (or the same image, or default)

        # Image resizing logic (remains the same)
        if self.image:
            try:
                if os.path.exists(self.image.path):
                    img = Image.open(self.image.path)
                    target_size = (300, 300)

                    # Calculate dimensions for cropping to a square from the center
                    width, height = img.size
                    if width > height:
                        left = (width - height) // 2
                        top = 0
                        right = (width + height) // 2
                        bottom = height
                    else:
                        left = 0
                        top = (height - width) // 2
                        right = width
                        bottom = (height + width) // 2

                    # Crop the image to a perfect square from the center
                    img = img.crop((left, top, right, bottom))

                    # Resize the square image to the target_size
                    img = img.resize(target_size, Image.LANCZOS)

                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    img.save(self.image.path)
                    print(f"Product image cropped to square, resized to {target_size}, and saved: {self.image.path}")
                else:
                    print(f"Warning: Product image file not found at {self.image.path} immediately after save. Skipping processing.")
            except FileNotFoundError:
                print(f"Warning: Product image file not found at {self.image.path} during processing attempt. Skipping processing.")
            except Exception as e:
                print(f"An error occurred during product image processing (square crop): {e}")

                
    # Optional: Override the delete method to remove the image file when the model instance is deleted
    def delete(self, *args, **kwargs):
        # Only delete the file if it's not the default image
        if self.image and 'default.jpg' not in self.image.path:
            if os.path.exists(self.image.path):
                os.remove(self.image.path)
                print(f"Associated image file deleted on model instance deletion: {self.image.path}")
        super().delete(*args, **kwargs)


from django.db import models
import os
from PIL import Image

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, help_text="Upload an image for the category.")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = Category.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    if old_instance.image.path and os.path.exists(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except Category.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Resize the image to 500px x 500px
        if self.image:
            try:
                img = Image.open(self.image.path)
                img = img.resize((500, 500), Image.LANCZOS)
                img.save(self.image.path)
            except Exception as e:
                print(f"Error resizing image for Category: {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the category is deleted
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True, help_text="Upload an image for the subcategory.")

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} > {self.name}"

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = SubCategory.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    if old_instance.image.path and os.path.exists(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except SubCategory.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Resize the image to 500px x 500px
        if self.image:
            try:
                img = Image.open(self.image.path)
                img = img.resize((500, 500), Image.LANCZOS)
                img.save(self.image.path)
            except Exception as e:
                print(f"Error resizing image for SubCategory: {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the subcategory is deleted
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

class Product(models.Model):
    """
    The core Product model, linked to Category, SubCategory, and SellerProfile.
    """
    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="The seller offering this product."
    )
    name = models.CharField(
        max_length=255,
        help_text="Full name of the product.",
        unique=False,
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="The main category for this product."
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True,
        help_text="Optional subcategory for this product."
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Main image for the product."
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Brand or manufacturer of the product."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the product."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    on_sale = models.BooleanField(
        default=True,
        help_text="Indicates if the product is currently on sale."
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = Product.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    if old_instance.image.path and os.path.exists(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except Product.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Image processing to be perfectly squared and then circularized
        if self.image:
            try:
                if os.path.exists(self.image.path):
                    img = Image.open(self.image.path)
                    target_size = (300, 300)

                    # Calculate dimensions for cropping to a square from the center
                    width, height = img.size
                    if width > height:
                        left = (width - height) // 2
                        top = 0
                        right = (width + height) // 2
                        bottom = height
                    else:
                        left = 0
                        top = (height - width) // 2
                        right = width
                        bottom = (height + width) // 2

                    # Crop the image to a perfect square from the center
                    img = img.crop((left, top, right, bottom))

                    # Resize the square image to the target_size
                    img = img.resize(target_size, Image.LANCZOS)

                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    img.save(self.image.path)
                    print(f"Product image cropped to square, resized to {target_size}, and saved: {self.image.path}")
                else:
                    print(f"Warning: Product image file not found at {self.image.path} immediately after save. Skipping processing.")
            except FileNotFoundError:
                print(f"Warning: Product image file not found at {self.image.path} during processing attempt. Skipping processing.")
            except Exception as e:
                print(f"An error occurred during product image processing (square crop): {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the product is deleted
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


from django.db import models
import os
from PIL import Image

class ProductVariant(models.Model):
    """
    Represents a specific variant of a Product, defined by attributes like color and size.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        help_text="The parent product this variant belongs to."
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The model name of the product variant (e.g., 'Nike Air Max')."
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The color of this specific product variant (e.g., 'Red', 'Blue')."
    )
    color_hex = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text="The hexadecimal color code for this variant (e.g., '#FF5733')."
    )
    size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The size of this specific product variant (e.g., 'S', 'M', 'L')."
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Stock Keeping Unit - unique identifier for this product variant."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The specific price for this product variant."
    )
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Current inventory stock quantity for this variant."
    )
    variant_image = models.ImageField(
        upload_to='product_variants/',
        blank=True,
        null=True,
        help_text="Image specific to this variant (e.g., a photo of the red shirt)."
    )
    on_sale = models.BooleanField(
        default=False,
        help_text="Indicates if this product variant is currently on sale."
    )

    class Meta:
        unique_together = ('product', 'color', 'size')
        ordering = ['product__name', 'color', 'size']

    def __str__(self):
        variant_attributes = []
        if self.color:
            variant_attributes.append(self.color)
        if self.size:
            variant_attributes.append(self.size)

        sale_status = " (On Sale!)" if self.on_sale else ""

        if variant_attributes:
            return f"{self.product.name} ({', '.join(variant_attributes)}){sale_status}"
        return f"{self.product.name} (Base Variant - SKU: {self.sku or 'N/A'}){sale_status}"

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = ProductVariant.objects.get(pk=self.pk)
                if old_instance.variant_image and old_instance.variant_image != self.variant_image:
                    if old_instance.variant_image.path and os.path.exists(old_instance.variant_image.path):
                        os.remove(old_instance.variant_image.path)
            except ProductVariant.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Image processing to be perfectly squared and then circularized
        if self.variant_image:
            try:
                if os.path.exists(self.variant_image.path):
                    img = Image.open(self.variant_image.path)
                    target_size = (300, 300)

                    # Calculate dimensions for cropping to a square from the center
                    width, height = img.size
                    if width > height:
                        left = (width - height) // 2
                        top = 0
                        right = (width + height) // 2
                        bottom = height
                    else:
                        left = 0
                        top = (height - width) // 2
                        right = width
                        bottom = (height + width) // 2

                    # Crop the image to a perfect square from the center
                    img = img.crop((left, top, right, bottom))

                    # Resize the square image to the target_size
                    img = img.resize(target_size, Image.LANCZOS)

                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    img.save(self.variant_image.path)
                    print(f"Product image cropped to square, resized to {target_size}, and saved: {self.variant_image.path}")
                else:
                    print(f"Warning: Product image file not found at {self.variant_image.path} immediately after save. Skipping processing.")
            except FileNotFoundError:
                print(f"Warning: Product image file not found at {self.variant_image.path} during processing attempt. Skipping processing.")
            except Exception as e:
                print(f"An error occurred during product image processing (square crop): {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the variant is deleted
        if self.variant_image and os.path.exists(self.variant_image.path):
            os.remove(self.variant_image.path)
        super().delete(*args, **kwargs)