import json
import os
from django.db import models
from django.conf import settings # Always use settings.AUTH_USER_MODEL for user ForeignKey/OneToOneField
from PIL import Image,ImageDraw
from django.contrib.auth.models import User



# Create your models here.

class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, help_text="Upload an image for the category.")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = ProductCategory.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    if old_instance.image.path and os.path.exists(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except ProductCategory.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Resize the image to 500px x 500px
        if self.image:
            try:
                img = Image.open(self.image.path)
                img = img.resize((500, 500), Image.LANCZOS)
                img.save(self.image.path)
            except Exception as e:
                print(f"Error resizing image for ProductCategory: {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the category is deleted
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


class ProductSubcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True, help_text="Upload an image for the subcategory.")

    class Meta:
        unique_together = ('name', 'category')  # Ensure subcategory names are unique within a category

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        # Delete the old image if a new one is uploaded
        if self.pk:
            try:
                old_instance = ProductSubcategory.objects.get(pk=self.pk)
                if old_instance.image and old_instance.image != self.image:
                    if old_instance.image.path and os.path.exists(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except ProductSubcategory.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Resize the image to 500px x 500px
        if self.image:
            try:
                img = Image.open(self.image.path)
                img = img.resize((500, 500), Image.LANCZOS)
                img.save(self.image.path)
            except Exception as e:
                print(f"Error resizing image for ProductSubcategory: {e}")

    def delete(self, *args, **kwargs):
        # Delete the image file when the subcategory is deleted
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)
    

class UserProfilepictures(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default.jpg'
    )

    def __str__(self):
        return f'{self.user.username} Profile'

    # Override save method to resize images AND delete old ones
    def save(self, *args, **kwargs):
        # Check if the instance already exists (i.e., it's an update, not a creation)
        if self.pk: # self.pk will be True if the object already has an ID in the database
            try:
                # Get the old instance from the database
                old_instance = UserProfilepictures.objects.get(pk=self.pk)
                # Check if the image path has changed and if the old image is not the default
                if old_instance.image and old_instance.image.path != self.image.path:
                    # Make sure the old image is not the default.jpg
                    if 'default.jpg' not in old_instance.image.path:
                        # Delete the old image file if it exists
                        if os.path.exists(old_instance.image.path):
                            os.remove(old_instance.image.path)
                            print(f"Old image deleted: {old_instance.image.path}")
            except UserProfilepictures.DoesNotExist:
                # This can happen if the object is new, or there's a race condition
                pass # No old image to delete if it's a new instance

        super().save(*args, **kwargs) # Save the new image (or the same image, or default)

        # Image stretching and circularization logic
        if self.image:
            try:
                # Ensure the image file actually exists after super().save()
                if os.path.exists(self.image.path):
                    img = Image.open(self.image.path)
                    target_size = (350, 350) # Define the desired square output size

                    # Stretch the image to the exact target_size, which might distort aspect ratio
                    img = img.resize(target_size, Image.LANCZOS)

                    # Ensure the image is in RGBA mode for transparency if needed,
                    # otherwise convert to RGB before saving.
                    # For circular crop, we primarily work with RGBA to handle the transparent corners.
                    img_rgba = img.convert("RGBA")

                    # Create a circular mask
                    mask = Image.new('L', target_size, 0) # L mode for grayscale, 0 for black (transparent)
                    draw = ImageDraw.Draw(mask)
                    # Draw a white filled circle (255) on the black mask
                    draw.ellipse((0, 0, target_size[0], target_size[1]), fill=255)

                    # Apply the circular mask to the image
                    # The mask determines the alpha channel for the img_rgba
                    # We composite it onto a solid white background (or transparent if saving as PNG)
                    final_img = Image.composite(img_rgba, Image.new("RGBA", target_size, (255, 255, 255, 255)), mask)

                    # If saving as JPEG (which doesn't support transparency), convert to RGB.
                    # This will fill the transparent parts created by the circular mask with white.
                    if final_img.mode == 'RGBA':
                         final_img = final_img.convert('RGB')

                    # Save the final image, overwriting the original
                    final_img.save(self.image.path)
                    print(f"Image stretched to {target_size}, circularized, and saved: {self.image.path}")
                else:
                    print(f"Warning: Image file not found at {self.image.path} immediately after save. Skipping processing.")
            except FileNotFoundError:
                print(f"Warning: Image file not found at {self.image.path} during processing attempt. Skipping processing.")
            except Exception as e:
                print(f"An error occurred during image processing (stretch and circularize): {e}")


    # Optional: Override the delete method to remove the image file when the model instance is deleted
    def delete(self, *args, **kwargs):
        # Only delete the file if it's not the default image
        if self.image and 'default.jpg' not in self.image.path:
            if os.path.exists(self.image.path):
                os.remove(self.image.path)
                print(f"Associated image file deleted on model instance deletion: {self.image.path}")
        super().delete(*args, **kwargs)


class ContactInformation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_info', # This allows request.user.contact_info
        verbose_name="User Profile" # A more descriptive name for the admin
    )
    email = models.EmailField(
        unique=True,
        blank=False, # Email is required in the form
        null=False,  # Email must have a value in the database
        verbose_name="Email Address"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,  # Allows the field to be empty in forms
        null=True,   # Allows NULL in the database
        verbose_name="Phone Number"
    )
    location = models.CharField(
        max_length=255,
        blank=True,  # Allows the field to be empty in forms
        null=True,   # Allows NULL in the database
        verbose_name="Location Details"
    )

    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"

    def __str__(self):
        # Handle cases where user might not be available for some reason (though unlikely with OneToOne)
        return f"Contact Info for {self.user.username}" if self.user else f"Contact Info ID: {self.pk}"

class SavedAddress(models.Model):
    ADDRESS_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('friend', 'Friend'),
        ('others', 'Others'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_CHOICES, default='home', unique=False) # Not unique per user for type
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True) # State might be optional depending on country
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India') # Default country for convenience
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        # Ensures a user can only have one address of a specific type (e.g., only one 'Home' address)
        # If you want multiple 'Home' addresses, remove or modify this constraint.
        unique_together = ('user', 'address_type')
        verbose_name = "Saved Address"
        verbose_name_plural = "Saved Addresses"

    def __str__(self):
        return f"{self.user.username}'s {self.get_address_type_display()} Address"

class SavedCard(models.Model):
    CARD_BRAND_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('jcb', 'JCB'),
        ('unionpay', 'UnionPay'),
        ('diners', 'Diners Club'),
        ('unknown', 'Unknown'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_cards')
    card_nickname = models.CharField(max_length=50, help_text="e.g., 'My Visa', 'Work Card'")
    last_four_digits = models.CharField(max_length=4) # Only store last four digits
    expiration_month = models.PositiveIntegerField(
        choices=[(i, str(i).zfill(2)) for i in range(1, 13)] # 1 to 12 for months
    )
    expiration_year = models.PositiveIntegerField() # e.g., 2025
    card_brand = models.CharField(max_length=20, choices=CARD_BRAND_CHOICES, default='unknown')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Saved Card"
        verbose_name_plural = "Saved Cards"
        # Optional: Ensure a user doesn't save two cards with the exact same nickname
        # unique_together = ('user', 'card_nickname')

    def __str__(self):
        return f"{self.user.username}'s {self.card_nickname} (**** {self.last_four_digits})"

    def get_display_expiration(self):
        return f"{str(self.expiration_month).zfill(2)}/{str(self.expiration_year)[-2:]}"







class cart_Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_wishlist')
    quantity = models.IntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)
    cart = models.TextField(default=json.dumps([]))  # Store as JSON list
    wishlist = models.TextField(default=json.dumps([]))  # Store as JSON list
    
    def __str__(self):
        return f"{self.user.username}'s Cart/Wishlist"
    
    def get_cart_items(self):
        """Returns the cart items as a Python list"""
        return json.loads(self.cart)
    
    def get_wishlist_items(self):
        """Returns the wishlist items as a Python list"""
        return json.loads(self.wishlist)
    
    def add_to_cart(self, variant_id):
        """Add a variant ID to the cart"""
        cart_items = self.get_cart_items()
        if variant_id not in cart_items:
            cart_items.append(variant_id)
            self.cart = json.dumps(cart_items)
            self.save()
            return True
        return False
    
    def remove_from_cart(self, variant_id):
        """Remove a variant ID from the cart"""
        cart_items = self.get_cart_items()
        if variant_id in cart_items:
            cart_items.remove(variant_id)
            self.cart = json.dumps(cart_items)
            self.save()
            return True
        return False
    


    def add_to_wishlist(self, variant_id):
        """Add variant to wishlist"""
        wishlist_items = self.get_wishlist_items()
        if variant_id not in wishlist_items:
            wishlist_items.append(variant_id)
            self.wishlist = json.dumps(wishlist_items)
            self.save()
            return True
        return False
    
    def remove_from_wishlist(self, variant_id):
        """Remove variant from wishlist"""
        wishlist_items = self.get_wishlist_items()
        if variant_id in wishlist_items:
            wishlist_items.remove(variant_id)
            self.wishlist = json.dumps(wishlist_items)
            self.save()
            return True
        return False