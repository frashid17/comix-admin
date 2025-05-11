from django.contrib import admin
from .models import (
    Service, 
    Order, 
    Profile, 
    Product, 
    Feedback, 
    Transaction, 
    ProductCategory,
    ProductReview,
    SupportMessage)
from django.utils.html import format_html

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'service__name')
    ordering = ('-created_at',)
    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone_number',
        'gender',
        'date_of_birth',
        'address',
        'city',
        'country',
        'created_at'
    )
    search_fields = (
        'user__username',
        'phone_number',
        'address',
        'city',
        'country',
    )
    list_filter = ('gender', 'city', 'country', 'created_at')
    list_display = ('user', 'phone_number', 'is_service_provider', 'is_approved_provider', 'created_at')
    list_editable = ('is_service_provider', 'is_approved_provider')
    search_fields = ('user__username', 'phone_number')
    list_filter = ('is_service_provider', 'is_approved_provider')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at', 'product_image_preview')  
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')

    readonly_fields = ('product_image_preview',)  

    def product_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "-"
    
    product_image_preview.short_description = "Image Preview"

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating', 'comment', 'created_at')
    search_fields = ('order__user__username', 'order__service__name', 'comment')
    list_filter = ('rating', 'created_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'reference', 'created_at')
    search_fields = ('user__username', 'reference')
    list_filter = ('payment_method', 'status', 'created_at')



class ProductInline(admin.TabularInline):
    model = Product
    extra = 0  # No blank rows
    can_delete = False  # Prevent deleting from inline
    show_change_link = True  # Allows link to edit page

    # Make fields read-only in inline
    readonly_fields = ['name', 'price', 'description', 'created_at', 'image']
    fields = ['name', 'price', 'description', 'image', 'created_at']

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [ProductInline]

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment'] 

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_from_admin', 'created_at']
    list_filter = ['is_from_admin', 'created_at']
    search_fields = ['user__username', 'message']
