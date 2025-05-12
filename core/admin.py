from django.contrib import admin
from django.db.models import Avg
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
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
User = get_user_model()
from django.contrib import admin
from django.urls import re_path

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
        'latitude',
        'longitude',
        'is_service_provider',
        'is_approved_provider',
        'created_at',
        'average_rating',
    )
    list_editable = ('is_service_provider', 'is_approved_provider')
    readonly_fields = ('location_map','created_at')
    search_fields = (
        'user__username',
        'phone_number',
        'address',
        'city',
        'country',
    )
    list_filter = (
        'gender',
        'city',
        'country',
        'is_service_provider',
        'is_approved_provider',
        'created_at'
    )


    actions = ['delete_low_rated_profiles']

    def average_rating(self, obj):
        feedbacks = Feedback.objects.filter(order__user=obj.user)
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else "-"
    
    average_rating.short_description = "Avg Rating"

    def delete_low_rated_profiles(self, request, queryset):
        deleted = 0
        for profile in queryset:
            avg = Feedback.objects.filter(order__user=profile.user).aggregate(Avg('rating'))['rating__avg']
            if avg and avg < 3:
                profile.user.delete()
                deleted += 1
        self.message_user(request, f"Deleted {deleted} users with low ratings.")
    
    delete_low_rated_profiles.short_description = "Delete users with average rating below 3"

    fieldsets = (
        
        (None, {
            'fields': ('user', 'phone_number', 'gender', 'date_of_birth', 'address', 'city', 'country', 'profile_picture')
        }),
        
        ("Provider Info", {
            'fields': ('is_service_provider', 'is_approved_provider', 'certification')
        }),
        ("Location Info", {
            'fields': ('latitude', 'longitude', 'location_map')
        }),
        ("System", {
            'fields': ( 'expo_push_token',)
        }),
    )
    def location_map(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                f'<iframe width="100%" height="300" frameborder="0" style="border:0" '
                f'src="https://www.google.com/maps/embed/v1/view?zoom=15&center={obj.latitude},{obj.longitude}&key=AIzaSyAQRgxwJ7mgwhqkvbHyvmUmOyZIJX7nNYI" '
                f'allowfullscreen></iframe>'
            )
        return "No location set."

    location_map.short_description = "Map Location"


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
    list_display = ['linked_user', 'preview', 'is_from_admin', 'created_at']
    list_filter = ['is_from_admin', 'created_at']
    search_fields = ['user__username', 'message']

    def linked_user(self, obj):
        url = f"/admin/support/thread/{obj.user.id}/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.user.username)

    linked_user.short_description = "User"

    def preview(self, obj):
        return (obj.message[:50] + '...') if len(obj.message) > 50 else obj.message
 

@staff_member_required
def support_thread_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        if "resolve_thread" in request.POST:
            user.profile.support_resolved = True
            user.profile.save()
            return redirect(request.path)
        elif "message" in request.POST:
            msg = request.POST.get("message")
            if msg:
                SupportMessage.objects.create(
                    user=user,
                    message=msg,
                    is_from_admin=True
                )
                return redirect(request.path)

    messages = SupportMessage.objects.filter(user=user).order_by('created_at')

    context = {
        'user': user,
        'messages': messages,
        'title': f'Support Thread with {user.username}',
        'resolved': user.profile.support_resolved
    }

    return TemplateResponse(request, 'admin/support_thread.html', context)



original_get_urls = admin.site.get_urls

def get_urls():
    custom_urls = [
        re_path(r'^support/thread/(?P<user_id>\d+)/$', support_thread_view, name='support-thread'),
    ]
    return custom_urls + original_get_urls()

admin.site.get_urls = get_urls