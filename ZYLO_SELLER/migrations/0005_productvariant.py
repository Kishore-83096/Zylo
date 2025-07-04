# Generated by Django 5.2 on 2025-06-10 05:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ZYLO_SELLER', '0004_product_on_sale'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(blank=True, help_text="The color of this specific product variant (e.g., 'Red', 'Blue').", max_length=50, null=True)),
                ('size', models.CharField(blank=True, help_text="The size of this specific product variant (e.g., 'S', 'M', 'L').", max_length=50, null=True)),
                ('sku', models.CharField(blank=True, help_text='Stock Keeping Unit - unique identifier for this product variant.', max_length=100, null=True, unique=True)),
                ('price', models.DecimalField(decimal_places=2, help_text='The specific price for this product variant.', max_digits=10)),
                ('stock', models.PositiveIntegerField(default=0, help_text='Current inventory stock quantity for this variant.')),
                ('variant_image', models.ImageField(blank=True, help_text='Image specific to this variant (e.g., a photo of the red shirt).', null=True, upload_to='product_variants/')),
                ('on_sale', models.BooleanField(default=False, help_text='Indicates if this product variant is currently on sale.')),
                ('product', models.ForeignKey(help_text='The parent product this variant belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='ZYLO_SELLER.product')),
            ],
            options={
                'ordering': ['product__name', 'color', 'size'],
                'unique_together': {('product', 'color', 'size')},
            },
        ),
    ]
