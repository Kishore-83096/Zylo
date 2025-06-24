from django.contrib import admin
from django.forms import RadioSelect
from .models import SellerProfile # Assuming SellerProfile is in models.py

class SellerProfileAdmin(admin.ModelAdmin):
    # --- CORRECTED LINES HERE ---
    list_display = ('user', 'store_name', 'status', 'created_at', 'updated_at')
    list_filter = ('status',) # Filter by the new 'status' field

    search_fields = ('user__username', 'store_name', 'business_email')

    fieldsets = (
        (None, {
            'fields': ('user', 'store_name', 'store_description', 'status'),
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'business_email'),
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'zip_code', 'country'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_at', 'updated_at',)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "status":
            kwargs['widget'] = RadioSelect
        return super().formfield_for_choice_field(db_field, request, **kwargs)

admin.site.register(SellerProfile, SellerProfileAdmin)

# admin.py

from django.contrib import admin
from .models import Category, SubCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['category']
